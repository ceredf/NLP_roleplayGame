"""
Utilities for scenario-pack-driven role-play games.

This module provides a lightweight bridge between plain JSON scenario packs and
SDialog agents. It is intentionally engine-agnostic: the functions here load
scenario data, synthesize role cards / persona prompts, and construct the
corresponding agents for AI-filled roles.
"""
# SPDX-FileCopyrightText: Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-License-Identifier: MIT
import json

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field, ConfigDict

from .agents import Agent
from .personas import Persona


class RoleplayPublicProfile(BaseModel):
    """Public role-card data shown to the role owner."""
    model_config = ConfigDict(extra="allow")

    name: str = ""
    title: str = ""
    background: str = ""
    primary_goal: str = ""
    hidden_goal: str = ""
    opening_position: str = ""
    negotiating_leverage: List[str] = Field(default_factory=list)
    special_move: str = ""


class RoleplayNegotiationProfile(BaseModel):
    """Structured bargaining constraints used to build persona rules."""
    model_config = ConfigDict(extra="allow")

    key_constraints: List[str] = Field(default_factory=list)
    minimum_requirements: List[str] = Field(default_factory=list)
    minimum_thresholds: Dict[str, str] = Field(default_factory=dict)
    preferred_gains: List[str] = Field(default_factory=list)
    red_lines: List[str] = Field(default_factory=list)
    batna: str = ""


class RoleplayPersonaHints(BaseModel):
    """Persona-specific style hints."""
    model_config = ConfigDict(extra="allow")

    archetype: str = ""
    communication_style: str = ""
    politeness: str = ""
    personality: str = ""
    gender: str = ""
    age: Optional[Any] = None


class RoleplayBehavior(BaseModel):
    """Behavioral hints that can later be compiled into orchestrators."""
    model_config = ConfigDict(extra="allow")

    persona: RoleplayPersonaHints = Field(default_factory=RoleplayPersonaHints)
    moderator_role: bool = False
    orchestrator_hints: List[Dict[str, str]] = Field(default_factory=list)


class RoleplayStakeholder(BaseModel):
    """Stakeholder definition in a role-play scenario pack."""
    model_config = ConfigDict(extra="allow")

    id: str
    display_name: str
    iswm_category: str = ""
    playable: bool = True
    ai_default: bool = True
    public_profile: RoleplayPublicProfile = Field(default_factory=RoleplayPublicProfile)
    private_info: List[str] = Field(default_factory=list)
    negotiation: RoleplayNegotiationProfile = Field(default_factory=RoleplayNegotiationProfile)
    key_relationships: List[str] = Field(default_factory=list)
    behavior: RoleplayBehavior = Field(default_factory=RoleplayBehavior)


class RoleplayRound(BaseModel):
    """Round metadata stored in the engine section."""
    model_config = ConfigDict(extra="allow")

    id: str
    title: str = ""
    purpose: str = ""
    turn_order: List[str] = Field(default_factory=list)
    turn_time_seconds: Optional[int] = None


class RoleplayEngine(BaseModel):
    """Engine settings packaged alongside the scenario content."""
    model_config = ConfigDict(extra="allow")

    rounds: List[RoleplayRound] = Field(default_factory=list)
    moderator_prompts: Dict[str, Any] = Field(default_factory=dict)


class RoleplayScenarioPack(BaseModel):
    """Top-level scenario pack."""
    model_config = ConfigDict(extra="allow")

    schema_version: str
    scenario_id: str
    title: str
    summary: str = ""
    setting: Dict[str, Any] = Field(default_factory=dict)
    narrative: Dict[str, Any] = Field(default_factory=dict)
    engine: RoleplayEngine = Field(default_factory=RoleplayEngine)
    proposal_dimensions: List[Dict[str, Any]] = Field(default_factory=list)
    stakeholders: List[RoleplayStakeholder] = Field(default_factory=list)
    events: List[Dict[str, Any]] = Field(default_factory=list)
    critical_failure: Dict[str, Any] = Field(default_factory=dict)
    debrief: Dict[str, Any] = Field(default_factory=dict)
    sources: List[Dict[str, Any]] = Field(default_factory=list)

    def stakeholder_map(self) -> Dict[str, RoleplayStakeholder]:
        """Return stakeholders keyed by stable role id."""
        return {stakeholder.id: stakeholder for stakeholder in self.stakeholders}

    def moderator_stakeholder(self) -> Optional[RoleplayStakeholder]:
        """Return the stakeholder designated as moderator, if any."""
        for stakeholder in self.stakeholders:
            if stakeholder.behavior.moderator_role:
                return stakeholder
        return None

    def opening_turn_order(self) -> List[str]:
        """Return the opening round turn order if present."""
        for round_info in self.engine.rounds:
            if round_info.id == "round_1_opening_positions":
                return round_info.turn_order
        return []


class RoleplayGameRules(BaseModel):
    """Hidden game rules that should not be exposed to player-facing scenario content."""
    model_config = ConfigDict(extra="allow")

    voting: Dict[str, Any] = Field(default_factory=dict)
    outcome_thresholds: Dict[str, Any] = Field(default_factory=dict)


class RoleplaySessionSetup(BaseModel):
    """Return object for prepared scenario state and AI agents."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    scenario: RoleplayScenarioPack
    game_rules: RoleplayGameRules = Field(default_factory=RoleplayGameRules)
    agents: Dict[str, Agent]
    human_roles: List[str] = Field(default_factory=list)
    ai_roles: List[str] = Field(default_factory=list)
    moderator_role: Optional[str] = None

    def get_role_card(self, stakeholder_id: str, reveal_private: bool = True) -> str:
        """Render a role card for a stakeholder in plain text."""
        stakeholder = self.scenario.stakeholder_map()[stakeholder_id]
        return render_role_card(stakeholder, reveal_private=reveal_private)


def load_roleplay_scenario(path: str) -> RoleplayScenarioPack:
    """
    Load and validate a role-play scenario pack from JSON.

    :param path: JSON file path.
    :type path: str
    :return: Parsed scenario pack.
    :rtype: RoleplayScenarioPack
    """
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return RoleplayScenarioPack.model_validate(data)


def load_roleplay_game_rules(path: str) -> RoleplayGameRules:
    """
    Load hidden game rules from JSON.

    :param path: JSON file path.
    :type path: str
    :return: Parsed rules object.
    :rtype: RoleplayGameRules
    """
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return RoleplayGameRules.model_validate(data)


def render_role_card(stakeholder: RoleplayStakeholder, reveal_private: bool = True) -> str:
    """
    Render a stakeholder role card as plain text.

    :param stakeholder: Stakeholder definition.
    :type stakeholder: RoleplayStakeholder
    :param reveal_private: Whether to include private information and hidden goal.
    :type reveal_private: bool
    :return: Role card text suitable for UI or prompt use.
    :rtype: str
    """
    profile = stakeholder.public_profile
    negotiation = stakeholder.negotiation
    lines = [
        f"Role: {stakeholder.display_name}",
        f"Name: {profile.name}",
        f"Title: {profile.title}",
    ]
    if profile.background:
        lines.append(f"Background: {profile.background}")
    if profile.primary_goal:
        lines.append(f"Primary goal: {profile.primary_goal}")
    if reveal_private and profile.hidden_goal:
        lines.append(f"Hidden goal: {profile.hidden_goal}")
    if profile.opening_position:
        lines.append(f"Opening position: {profile.opening_position}")
    if profile.special_move:
        lines.append(f"Special move: {profile.special_move}")
    if profile.negotiating_leverage:
        lines.append("Negotiating leverage:")
        lines.extend(f"- {item}" for item in profile.negotiating_leverage)
    if negotiation.key_constraints:
        lines.append("Key constraints:")
        lines.extend(f"- {item}" for item in negotiation.key_constraints)
    if negotiation.minimum_requirements:
        lines.append("Minimum requirements:")
        lines.extend(f"- {item}" for item in negotiation.minimum_requirements)
    if negotiation.preferred_gains:
        lines.append("Preferred gains:")
        lines.extend(f"- {item}" for item in negotiation.preferred_gains)
    if negotiation.red_lines:
        lines.append("Red lines:")
        lines.extend(f"- {item}" for item in negotiation.red_lines)
    if negotiation.batna:
        lines.append(f"BATNA: {negotiation.batna}")
    if stakeholder.key_relationships:
        lines.append("Key relationships:")
        lines.extend(f"- {item}" for item in stakeholder.key_relationships)
    if reveal_private and stakeholder.private_info:
        lines.append("Private information:")
        lines.extend(f"- {item}" for item in stakeholder.private_info)
    return "\n".join(lines)


def _compose_persona_rules(stakeholder: RoleplayStakeholder, reveal_private: bool) -> str:
    """Build the persona rules string from structured negotiation data."""
    negotiation = stakeholder.negotiation
    behavior = stakeholder.behavior
    instructions: List[str] = [
        f"You are participating in a multi-stakeholder negotiation as the {stakeholder.display_name}.",
        "Stay in character and argue from this stakeholder's incentives, constraints, and lived perspective.",
    ]

    if negotiation.minimum_requirements:
        instructions.append(
            "Your minimum requirements are: " + "; ".join(negotiation.minimum_requirements) + "."
        )
    if reveal_private and negotiation.minimum_thresholds:
        threshold_text = "; ".join(
            f"{dimension}: {threshold}"
            for dimension, threshold in negotiation.minimum_thresholds.items()
        )
        instructions.append(
            "Your hidden minimum thresholds for judging the final agreement are: " + threshold_text + "."
        )
    if negotiation.key_constraints:
        instructions.append(
            "Your key constraints are: " + "; ".join(negotiation.key_constraints) + "."
        )
    if negotiation.preferred_gains:
        instructions.append(
            "Your preferred gains are: " + "; ".join(negotiation.preferred_gains) + "."
        )
    if negotiation.red_lines:
        instructions.append(
            "Your red lines are: " + "; ".join(negotiation.red_lines) + ". Do not endorse plans that violate them."
        )
    if reveal_private and stakeholder.private_info:
        instructions.append(
            "Private information you know: " + "; ".join(stakeholder.private_info) + "."
        )
    if negotiation.batna:
        instructions.append(f"If negotiations fail, your BATNA is: {negotiation.batna}.")
    if stakeholder.public_profile.special_move:
        instructions.append(
            "You have one dramatic special move available in the meeting: "
            + stakeholder.public_profile.special_move
            + ". Use it only when it would materially shift the room."
        )
    if stakeholder.key_relationships:
        instructions.append(
            "Your key relationships in the room are: " + "; ".join(stakeholder.key_relationships) + "."
        )
    if behavior.orchestrator_hints:
        instructions.append("Behavioral reminders:")
        instructions.extend(
            f"- {hint.get('trigger', 'Trigger')}: {hint.get('effect', '')}".rstrip(": ")
            for hint in behavior.orchestrator_hints
        )
    if behavior.moderator_role:
        instructions.append(
            "You are also responsible for facilitating the meeting, enforcing turn order, and keeping focus on producing a complete proposal."
        )
    return "\n".join(instructions)


def build_roleplay_persona(
    stakeholder: RoleplayStakeholder,
    reveal_private: bool = True,
) -> Persona:
    """
    Convert a stakeholder definition into a generic SDialog persona.

    :param stakeholder: Stakeholder to convert.
    :type stakeholder: RoleplayStakeholder
    :param reveal_private: Whether the persona includes hidden information.
    :type reveal_private: bool
    :return: Persona object ready for agent construction.
    :rtype: Persona
    """
    profile = stakeholder.public_profile
    hints = stakeholder.behavior.persona
    personality_parts = [part for part in [hints.personality, hints.communication_style] if part]

    circumstances_parts = [profile.primary_goal]
    if reveal_private and profile.hidden_goal:
        circumstances_parts.append(f"Hidden goal: {profile.hidden_goal}")

    return Persona(
        name=profile.name or stakeholder.display_name,
        age=hints.age or "",
        gender=hints.gender or "",
        role=profile.title or stakeholder.display_name,
        background=profile.background,
        personality=", ".join(personality_parts),
        circumstances=" ".join(part for part in circumstances_parts if part),
        rules=_compose_persona_rules(stakeholder, reveal_private=reveal_private),
    )


def build_roleplay_agent(
    stakeholder: RoleplayStakeholder,
    *,
    reveal_private: bool = True,
    think: bool = True,
    model: Optional[str] = None,
    **llm_kwargs,
) -> Agent:
    """
    Build a single SDialog agent from a stakeholder definition.

    :param stakeholder: Stakeholder to convert.
    :type stakeholder: RoleplayStakeholder
    :param reveal_private: Whether to include hidden information in the persona prompt.
    :type reveal_private: bool
    :param think: Whether to enable thinking mode on the agent.
    :type think: bool
    :param model: Optional explicit model override.
    :type model: Optional[str]
    :return: Configured agent.
    :rtype: Agent
    """
    persona = build_roleplay_persona(stakeholder, reveal_private=reveal_private)
    return Agent(
        persona=persona,
        think=think,
        name=stakeholder.display_name,
        model=model,
        **llm_kwargs,
    )


def prepare_roleplay_session(
    scenario: RoleplayScenarioPack,
    *,
    game_rules: Optional[RoleplayGameRules] = None,
    human_roles: Optional[List[str]] = None,
    include_moderator: bool = True,
    reveal_private_to_ai: bool = True,
    think: bool = True,
    model: Optional[str] = None,
    **llm_kwargs,
) -> RoleplaySessionSetup:
    """
    Prepare AI agents for a scenario pack while leaving chosen roles for humans.

    :param scenario: Parsed scenario pack.
    :type scenario: RoleplayScenarioPack
    :param human_roles: Stakeholder ids reserved for human players.
    :type human_roles: Optional[List[str]]
    :param include_moderator: Whether to auto-build the moderator role if one exists.
    :type include_moderator: bool
    :param reveal_private_to_ai: Whether AI agents receive their role's private information.
    :type reveal_private_to_ai: bool
    :param think: Whether to enable thinking mode for AI agents.
    :type think: bool
    :param model: Optional explicit model override for all AI agents.
    :type model: Optional[str]
    :return: Prepared session bundle.
    :rtype: RoleplaySessionSetup
    """
    human_role_set: Set[str] = set(human_roles or [])
    agents: Dict[str, Agent] = {}
    ai_roles: List[str] = []
    moderator = scenario.moderator_stakeholder()

    for stakeholder in scenario.stakeholders:
        if stakeholder.id in human_role_set:
            continue
        if stakeholder.behavior.moderator_role and not include_moderator:
            continue
        if not stakeholder.ai_default and stakeholder.id != getattr(moderator, "id", None):
            continue

        agents[stakeholder.id] = build_roleplay_agent(
            stakeholder,
            reveal_private=reveal_private_to_ai,
            think=think,
            model=model,
            **llm_kwargs,
        )
        ai_roles.append(stakeholder.id)

    return RoleplaySessionSetup(
        scenario=scenario,
        game_rules=game_rules or RoleplayGameRules(),
        agents=agents,
        human_roles=sorted(human_role_set),
        ai_roles=ai_roles,
        moderator_role=getattr(moderator, "id", None),
    )


def load_and_prepare_roleplay_session(
    path: str,
    *,
    rules_path: Optional[str] = None,
    human_roles: Optional[List[str]] = None,
    include_moderator: bool = True,
    reveal_private_to_ai: bool = True,
    think: bool = True,
    model: Optional[str] = None,
    **llm_kwargs,
) -> RoleplaySessionSetup:
    """
    Convenience wrapper: load a scenario pack from disk and prepare its session.

    :param path: Scenario-pack JSON path.
    :type path: str
    :return: Prepared session bundle.
    :rtype: RoleplaySessionSetup
    """
    scenario = load_roleplay_scenario(path)
    game_rules = load_roleplay_game_rules(rules_path) if rules_path else RoleplayGameRules()
    return prepare_roleplay_session(
        scenario,
        game_rules=game_rules,
        human_roles=human_roles,
        include_moderator=include_moderator,
        reveal_private_to_ai=reveal_private_to_ai,
        think=think,
        model=model,
        **llm_kwargs,
    )


def default_city_x_scenario_path() -> str:
    """
    Return the bundled example City X scenario-pack path.

    :return: Absolute path to the example scenario pack.
    :rtype: str
    """
    return str(Path(__file__).resolve().parents[2] / "examples" / "swm_roleplay" / "city_x_scenario.json")


def default_city_x_game_rules_path() -> str:
    """
    Return the bundled example City X hidden game-rules path.

    :return: Absolute path to the example game-rules file.
    :rtype: str
    """
    return str(Path(__file__).resolve().parents[2] / "examples" / "swm_roleplay" / "city_x_game_rules.json")
