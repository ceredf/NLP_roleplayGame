"""
Minimal engine for scenario-pack-driven role-play sessions.

This module implements the first playable backbone for the SWM role-play game:

- round and turn progression
- transcript capture
- midpoint event injection
- proposal creation and amendment
- check-vote and final-vote collection
- outcome determination

The engine is deliberately conservative and deterministic so it can serve as a
stable backend contract before richer moderator automation is added.
"""
# SPDX-FileCopyrightText: Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-License-Identifier: MIT
import random

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict

from . import Dialog, Turn
from .roleplay import RoleplayGameRules, RoleplayScenarioPack, RoleplaySessionSetup
from .agents import Agent


CHECK_VOTE_LABELS = {"support", "oppose", "undecided"}
FINAL_VOTE_LABELS = {"yes", "no"}
NEGOTIATION_ARCHETYPE_DEFAULTS = {
    "pragmatist": {
        "satisfaction_score": 42,
        "consensus_confidence": 45,
        "flexibility_score": 72,
        "patience_score": 62,
        "threshold_satisfaction": 64,
        "threshold_confidence": 58,
        "minimum_patience": 22,
    },
    "idealist": {
        "satisfaction_score": 36,
        "consensus_confidence": 34,
        "flexibility_score": 45,
        "patience_score": 74,
        "threshold_satisfaction": 76,
        "threshold_confidence": 64,
        "minimum_patience": 24,
    },
    "opportunist": {
        "satisfaction_score": 34,
        "consensus_confidence": 40,
        "flexibility_score": 66,
        "patience_score": 52,
        "threshold_satisfaction": 62,
        "threshold_confidence": 55,
        "minimum_patience": 18,
    },
    "skeptic": {
        "satisfaction_score": 24,
        "consensus_confidence": 26,
        "flexibility_score": 34,
        "patience_score": 58,
        "threshold_satisfaction": 74,
        "threshold_confidence": 70,
        "minimum_patience": 20,
    },
    "mediator": {
        "satisfaction_score": 40,
        "consensus_confidence": 56,
        "flexibility_score": 84,
        "patience_score": 82,
        "threshold_satisfaction": 60,
        "threshold_confidence": 60,
        "minimum_patience": 26,
    },
}


class RoleplayVote(BaseModel):
    """A recorded vote in either the check-vote or final-vote stage."""
    role_id: str
    label: str


class RoleplayProposal(BaseModel):
    """Structured working proposal for Round 3."""
    proposer_role_id: str
    dimensions: Dict[str, str]
    version: int = 1
    amendment_history: List[Dict[str, Any]] = Field(default_factory=list)

    def missing_dimensions(self, required_dimension_ids: List[str]) -> List[str]:
        """Return proposal dimensions that are not yet filled."""
        missing = []
        for dimension_id in required_dimension_ids:
            value = self.dimensions.get(dimension_id, "")
            if not value or not value.strip():
                missing.append(dimension_id)
        return missing


class RoleplayRoundState(BaseModel):
    """Mutable state for the currently active round."""
    round_id: str
    round_title: str = ""
    turn_order: List[str] = Field(default_factory=list)
    current_turn_index: int = 0
    turns_taken: int = 0
    midpoint_event_triggered: bool = False

    def current_speaker(self) -> Optional[str]:
        """Return the current speaker id."""
        if not self.turn_order:
            return None
        return self.turn_order[self.current_turn_index]


class RoleplayNegotiationState(BaseModel):
    """Internal Round 2 negotiation state for one stakeholder."""
    role_id: str
    archetype: str = "pragmatist"
    satisfaction_score: int = 40
    consensus_confidence: int = 40
    flexibility_score: int = 50
    patience_score: int = 60
    ready_to_vote: bool = False
    threshold_satisfaction: int = 65
    threshold_confidence: int = 60
    minimum_patience: int = 20
    demands_addressed: int = 0
    unresolved_conflicts: int = 0
    support_ratio: float = 0.0
    last_action: str = "continue_discussion"
    conditional_readiness: bool = False


class RoleplayNegotiationMetrics(BaseModel):
    """Aggregated Round 2 convergence metrics."""
    proposal_quality_score: int = 0
    conflict_volatility_score: int = 0
    revision_stability_score: int = 0
    support_ratio: float = 0.0
    unresolved_conflicts: int = 0
    stakeholder_demands_addressed: int = 0
    ai_ready_ratio: float = 0.0
    human_ready_ratio: float = 0.0
    stagnation_score: int = 0
    fatigue_score: int = 0
    suggested_transition: bool = False
    suggested_reason: str = ""


class RoleplayOutcome(BaseModel):
    """Resolved game outcome after final vote or critical failure."""
    outcome: str
    endorsements: int = 0
    detail: str = ""
    goals: Dict[str, bool] = Field(default_factory=dict)


class RoleplayGameState(BaseModel):
    """Single session state for a role-play game."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    scenario: RoleplayScenarioPack
    game_rules: RoleplayGameRules = Field(default_factory=RoleplayGameRules)
    human_roles: List[str] = Field(default_factory=list)
    ai_roles: List[str] = Field(default_factory=list)
    moderator_role: Optional[str] = None
    dialog: Dialog
    round_index: int = 0
    round_state: RoleplayRoundState
    active_proposal: Optional[RoleplayProposal] = None
    check_votes: Dict[str, RoleplayVote] = Field(default_factory=dict)
    final_votes: Dict[str, RoleplayVote] = Field(default_factory=dict)
    triggered_events: List[str] = Field(default_factory=list)
    withdrawn_roles: List[str] = Field(default_factory=list)
    negotiation_states: Dict[str, RoleplayNegotiationState] = Field(default_factory=dict)
    negotiation_metrics: RoleplayNegotiationMetrics = Field(default_factory=RoleplayNegotiationMetrics)
    human_ready_to_vote: Dict[str, bool] = Field(default_factory=dict)
    outcome: Optional[RoleplayOutcome] = None

    def current_round(self) -> Dict[str, Any]:
        """Return the raw round metadata for the active round."""
        return self.scenario.engine.rounds[self.round_index].model_dump()

    def current_speaker(self) -> Optional[str]:
        """Return the stakeholder id expected to speak next."""
        return self.round_state.current_speaker()

    def required_dimension_ids(self) -> List[str]:
        """Return required proposal dimension ids in order."""
        return [dimension["id"] for dimension in self.scenario.proposal_dimensions]

    def proposal_is_complete(self) -> bool:
        """Return whether the working proposal covers all required dimensions."""
        if self.active_proposal is None:
            return False
        return not self.active_proposal.missing_dimensions(self.required_dimension_ids())


class RoleplayRuntime(BaseModel):
    """Runtime bundle combining game state with the prepared AI agents."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    game: RoleplayGameState
    agents: Dict[str, Agent]


def _stakeholder_name_map(scenario: RoleplayScenarioPack) -> Dict[str, str]:
    """Return a stable role id -> display name mapping."""
    return {stakeholder.id: stakeholder.display_name for stakeholder in scenario.stakeholders}


def _build_turn_order(scenario: RoleplayScenarioPack, round_index: int) -> List[str]:
    """Resolve turn order for a round, falling back to opening order."""
    round_info = scenario.engine.rounds[round_index]
    if round_info.turn_order:
        return round_info.turn_order
    if scenario.opening_turn_order():
        return scenario.opening_turn_order()
    return [stakeholder.id for stakeholder in scenario.stakeholders]


def _build_round_state(scenario: RoleplayScenarioPack, round_index: int) -> RoleplayRoundState:
    """Create round state from static scenario metadata."""
    round_info = scenario.engine.rounds[round_index]
    return RoleplayRoundState(
        round_id=round_info.id,
        round_title=round_info.title,
        turn_order=_build_turn_order(scenario, round_index),
    )


def _clamp_score(value: float) -> int:
    """Clamp a score to the 0-100 range."""
    return max(0, min(100, int(round(value))))


def _build_negotiation_state(stakeholder) -> RoleplayNegotiationState:
    """Create a stakeholder's internal negotiation state from its archetype."""
    archetype = (stakeholder.behavior.persona.archetype or "pragmatist").lower()
    defaults = NEGOTIATION_ARCHETYPE_DEFAULTS.get(archetype, NEGOTIATION_ARCHETYPE_DEFAULTS["pragmatist"])
    return RoleplayNegotiationState(role_id=stakeholder.id, archetype=archetype, **defaults)


def _render_full_negotiation_text(game: RoleplayGameState) -> str:
    """Render proposal and transcript into one negotiation text block."""
    parts = [_render_recent_transcript(game, max_turns=20), _render_proposal_summary(game)]
    return "\n".join(part for part in parts if part).lower()


def create_roleplay_game(session: RoleplaySessionSetup) -> RoleplayGameState:
    """
    Create a fresh game state from a prepared role-play session.

    :param session: Prepared session setup.
    :type session: RoleplaySessionSetup
    :return: Initialized game state.
    :rtype: RoleplayGameState
    """
    personas = {}
    stakeholder_map = session.scenario.stakeholder_map()
    for stakeholder_id, stakeholder in stakeholder_map.items():
        personas[stakeholder.display_name] = {
            "role_id": stakeholder_id,
            "display_name": stakeholder.display_name,
            "name": stakeholder.public_profile.name,
            "title": stakeholder.public_profile.title,
        }

    dialog = Dialog(
        scenario=session.scenario.model_dump(),
        personas=personas,
        turns=[],
        events=[],
        notes={
            "human_roles": session.human_roles,
            "ai_roles": session.ai_roles,
            "moderator_role": session.moderator_role,
        },
    )

    negotiation_states = {
        stakeholder.id: _build_negotiation_state(stakeholder)
        for stakeholder in session.scenario.stakeholders
        if stakeholder.id != session.moderator_role
    }

    game = RoleplayGameState(
        scenario=session.scenario,
        game_rules=session.game_rules,
        human_roles=session.human_roles,
        ai_roles=session.ai_roles,
        moderator_role=session.moderator_role,
        dialog=dialog,
        round_state=_build_round_state(session.scenario, 0),
        negotiation_states=negotiation_states,
        human_ready_to_vote={role_id: False for role_id in session.human_roles},
    )
    evaluate_negotiation_progress(game)
    return game


def create_roleplay_runtime(session: RoleplaySessionSetup) -> RoleplayRuntime:
    """
    Create a runtime bundle with game state and prepared agents.

    :param session: Prepared session setup.
    :type session: RoleplaySessionSetup
    :return: Runtime bundle.
    :rtype: RoleplayRuntime
    """
    return RoleplayRuntime(game=create_roleplay_game(session), agents=session.agents)


def record_turn(game: RoleplayGameState, role_id: str, text: str) -> None:
    """
    Record a stakeholder turn and advance the speaker cursor.

    :param game: Active game state.
    :type game: RoleplayGameState
    :param role_id: Stakeholder id taking the turn.
    :type role_id: str
    :param text: Submitted utterance text.
    :type text: str
    :raises ValueError: If speaker is unexpected or the game is already over.
    """
    if game.outcome is not None:
        raise ValueError("The game has already been resolved.")

    expected = game.current_speaker()
    if expected and role_id != expected:
        raise ValueError(f"It is not {role_id}'s turn. Expected speaker: {expected}.")

    stakeholder = game.scenario.stakeholder_map()[role_id]
    game.dialog.turns.append(Turn(speaker=stakeholder.display_name, text=text))

    game.round_state.turns_taken += 1
    order_len = len(game.round_state.turn_order)
    if order_len:
        game.round_state.current_turn_index = (game.round_state.current_turn_index + 1) % order_len
    evaluate_negotiation_progress(game)


def maybe_inject_midpoint_event(game: RoleplayGameState, seed: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Inject a midpoint event in Round 2 if the trigger condition has been reached.

    :param game: Active game state.
    :type game: RoleplayGameState
    :param seed: Optional random seed for deterministic event selection.
    :type seed: Optional[int]
    :return: The injected event object, or None if nothing was injected.
    :rtype: Optional[dict]
    """
    if game.round_state.round_id != "round_2_negotiation":
        return None
    if game.round_state.midpoint_event_triggered:
        return None

    order_len = len(game.round_state.turn_order)
    midpoint_turn = max(1, order_len // 2)
    if game.round_state.turns_taken < midpoint_turn:
        return None

    if not game.scenario.events:
        return None

    rng = random.Random(seed)
    available_events = [event for event in game.scenario.events if event["id"] not in game.triggered_events]
    if not available_events:
        available_events = game.scenario.events

    event = rng.choice(available_events)
    game.triggered_events.append(event["id"])
    game.round_state.midpoint_event_triggered = True
    game.dialog.notes["last_event"] = event
    return event


def advance_round(game: RoleplayGameState) -> None:
    """
    Advance to the next round.

    :param game: Active game state.
    :type game: RoleplayGameState
    :raises ValueError: If already at the final round.
    """
    if game.round_index >= len(game.scenario.engine.rounds) - 1:
        raise ValueError("Already at the final round.")
    game.round_index += 1
    game.round_state = _build_round_state(game.scenario, game.round_index)
    if game.round_state.round_id == "round_2_negotiation":
        game.human_ready_to_vote = {role_id: False for role_id in game.human_roles}
    evaluate_negotiation_progress(game)


def create_working_proposal(game: RoleplayGameState, proposer_role_id: str, dimensions: Dict[str, str]) -> RoleplayProposal:
    """
    Create the first working proposal for Round 3.

    :param game: Active game state.
    :type game: RoleplayGameState
    :param proposer_role_id: Stakeholder creating the proposal.
    :type proposer_role_id: str
    :param dimensions: Proposal dimension values keyed by dimension id.
    :type dimensions: dict
    :return: The created proposal.
    :rtype: RoleplayProposal
    """
    proposal = RoleplayProposal(proposer_role_id=proposer_role_id, dimensions=dimensions)
    game.active_proposal = proposal
    evaluate_negotiation_progress(game)
    return proposal


def amend_working_proposal(
    game: RoleplayGameState,
    proposer_role_id: str,
    amendments: Dict[str, str],
    note: str = "",
) -> RoleplayProposal:
    """
    Amend the current working proposal.

    :param game: Active game state.
    :type game: RoleplayGameState
    :param proposer_role_id: Stakeholder proposing the amendment.
    :type proposer_role_id: str
    :param amendments: Changed proposal fields.
    :type amendments: dict
    :param note: Optional explanation of the amendment.
    :type note: str
    :return: Updated proposal.
    :rtype: RoleplayProposal
    :raises ValueError: If there is no working proposal yet.
    """
    if game.active_proposal is None:
        raise ValueError("There is no working proposal to amend.")

    for key, value in amendments.items():
        game.active_proposal.dimensions[key] = value

    game.active_proposal.version += 1
    game.active_proposal.amendment_history.append(
        {
            "role_id": proposer_role_id,
            "amendments": amendments,
            "note": note,
            "version": game.active_proposal.version,
        }
    )
    evaluate_negotiation_progress(game)
    return game.active_proposal


def missing_proposal_dimensions(game: RoleplayGameState) -> List[str]:
    """
    Return missing required proposal dimensions for the active proposal.

    :param game: Active game state.
    :type game: RoleplayGameState
    :return: Missing dimension ids.
    :rtype: list[str]
    """
    if game.active_proposal is None:
        return game.required_dimension_ids()
    return game.active_proposal.missing_dimensions(game.required_dimension_ids())


def set_human_ready_to_vote(game: RoleplayGameState, role_id: str, ready: bool) -> None:
    """Update one human stakeholder's readiness flag and refresh negotiation metrics."""
    game.human_ready_to_vote[role_id] = ready
    evaluate_negotiation_progress(game)


def _requirement_addressed(text: str, requirement: str) -> bool:
    """Heuristic check for whether the negotiation text addresses a requirement."""
    words = [word.strip(".,:;()[]").lower() for word in requirement.split()]
    meaningful = [word for word in words if len(word) > 4]
    if not meaningful:
        return requirement.lower() in text
    overlap = sum(1 for word in set(meaningful) if word in text)
    return overlap >= max(1, min(2, len(set(meaningful))))


def _recent_conflict_count(game: RoleplayGameState, max_turns: int = 8) -> int:
    """Count conflict-heavy markers in recent transcript turns."""
    conflict_markers = (
        "cannot accept",
        "will not",
        "reject",
        "oppose",
        "unacceptable",
        "fails to",
        "without",
        "blocked",
        "refuse",
    )
    text = _render_recent_transcript(game, max_turns=max_turns).lower()
    return sum(text.count(marker) for marker in conflict_markers)


def evaluate_negotiation_progress(game: RoleplayGameState) -> RoleplayNegotiationMetrics:
    """
    Evaluate Round 2 negotiation convergence and refresh stakeholder internal state.

    The scoring is intentionally heuristic rather than game-theoretically exact:
    it looks at whether stakeholder requirements are being addressed in the
    proposal/transcript, how conflict-heavy the recent exchange is, and whether
    support appears to be stabilizing.
    """
    text = _render_full_negotiation_text(game)
    recent_text = _render_recent_transcript(game, max_turns=10).lower()
    support_markers = ("agree", "support", "acceptable", "can work with", "aligned", "ready")
    support_hits = sum(recent_text.count(marker) for marker in support_markers)
    conflict_hits = _recent_conflict_count(game)
    support_ratio = support_hits / max(1, support_hits + conflict_hits)
    missing_count = len(missing_proposal_dimensions(game))
    recent_turns = game.dialog.turns[-6:]
    unique_recent = len({turn.text.strip().lower() for turn in recent_turns if turn.text.strip()})
    stagnation_score = _clamp_score((1 - (unique_recent / max(1, len(recent_turns)))) * 100) if recent_turns else 0
    fatigue_score = _clamp_score((game.round_state.turns_taken / max(1, len(game.negotiation_states))) * 15 + conflict_hits * 4)

    total_requirements = 0
    total_addressed = 0
    unresolved_conflicts = 0
    ai_ready_weight = 0.0
    conditional_count = 0
    average_patience = 0

    for stakeholder in game.scenario.stakeholders:
        if stakeholder.id == game.moderator_role:
            continue
        state = game.negotiation_states[stakeholder.id]
        previous_ready = state.ready_to_vote
        previous_conditional = state.conditional_readiness
        requirements = stakeholder.negotiation.minimum_requirements or []
        preferred = stakeholder.negotiation.preferred_gains or []
        red_lines = stakeholder.negotiation.red_lines or []

        addressed_requirements = sum(1 for item in requirements if _requirement_addressed(text, item))
        addressed_preferred = sum(1 for item in preferred if _requirement_addressed(text, item))
        triggered_red_lines = sum(1 for item in red_lines if not _requirement_addressed(text, item))

        total_requirements += len(requirements)
        total_addressed += addressed_requirements
        unresolved_conflicts += triggered_red_lines

        requirement_ratio = addressed_requirements / max(1, len(requirements))
        preferred_ratio = addressed_preferred / max(1, len(preferred)) if preferred else requirement_ratio

        satisfaction = (
            requirement_ratio * 65
            + preferred_ratio * 20
            + state.flexibility_score * 0.15
            - triggered_red_lines * 12
            - missing_count * 5
        )
        confidence = (
            support_ratio * 45
            + (100 - conflict_hits * 8)
            + (100 - missing_count * 10)
            + state.flexibility_score * 0.1
            - stagnation_score * 0.2
        ) / 2.0

        patience = state.patience_score - 4 - conflict_hits * 2 + addressed_requirements * 3 - missing_count

        state.demands_addressed = addressed_requirements
        state.unresolved_conflicts = triggered_red_lines
        state.support_ratio = round(support_ratio, 2)
        state.satisfaction_score = _clamp_score(satisfaction)
        state.consensus_confidence = _clamp_score(confidence)
        state.patience_score = _clamp_score(patience)
        calculated_ready = (
            (
                state.satisfaction_score >= state.threshold_satisfaction
                and state.consensus_confidence >= state.threshold_confidence
            )
            or state.patience_score <= state.minimum_patience
        )
        state.ready_to_vote = calculated_ready or (
            previous_ready and state.satisfaction_score >= max(35, state.threshold_satisfaction - 20)
        )
        state.conditional_readiness = not state.ready_to_vote and (
            state.satisfaction_score >= max(45, state.threshold_satisfaction - 15)
            or state.consensus_confidence >= max(45, state.threshold_confidence - 10)
        )
        if previous_conditional and not state.ready_to_vote:
            state.conditional_readiness = True

        if state.ready_to_vote:
            state.last_action = "signal_full_readiness"
            ai_ready_weight += 1.0
        elif state.conditional_readiness:
            state.last_action = "signal_conditional_readiness"
            conditional_count += 1
            ai_ready_weight += 0.5
        elif state.flexibility_score >= 65 and state.satisfaction_score < state.threshold_satisfaction:
            state.last_action = "offer_compromise"
        elif state.unresolved_conflicts > 0:
            state.last_action = "request_revisions"
        else:
            state.last_action = "continue_discussion"

        average_patience += state.patience_score

    ai_count = max(1, len([role_id for role_id in game.negotiation_states if role_id not in game.human_roles]))
    human_count = max(1, len(game.human_roles))
    human_ready_ratio = sum(1 for ready in game.human_ready_to_vote.values() if ready) / human_count
    ai_ready_ratio = ai_ready_weight / ai_count
    revision_stability_score = _clamp_score(
        100 - min(80, len(game.active_proposal.amendment_history) * 12) if game.active_proposal else 25 + support_ratio * 35
    )
    proposal_quality_score = _clamp_score(
        (
            (total_addressed / max(1, total_requirements)) * 55
            + support_ratio * 20
            + revision_stability_score * 0.15
            + (1 - min(1.0, unresolved_conflicts / max(1, len(game.negotiation_states)))) * 10
        )
    )
    conflict_volatility_score = _clamp_score(conflict_hits * 12 + unresolved_conflicts * 10 + stagnation_score * 0.2)
    fatigue_score = max(fatigue_score, _clamp_score(100 - (average_patience / max(1, len(game.negotiation_states)))))

    suggested_transition = False
    suggested_reason = ""
    if human_ready_ratio >= 1.0 and ai_ready_ratio >= 0.5:
        suggested_transition = True
        suggested_reason = "The human player is ready and a clear majority of AI stakeholders are ready."
    elif human_ready_ratio > 0 and proposal_quality_score >= 60 and conflict_volatility_score <= 50:
        suggested_transition = True
        suggested_reason = "The proposal is strong and the remaining conflict appears limited."
    elif human_ready_ratio > 0 and stagnation_score >= 60 and fatigue_score >= 55:
        suggested_transition = True
        suggested_reason = "The discussion is stalling and negotiation fatigue is high."

    metrics = RoleplayNegotiationMetrics(
        proposal_quality_score=proposal_quality_score,
        conflict_volatility_score=conflict_volatility_score,
        revision_stability_score=revision_stability_score,
        support_ratio=round(support_ratio, 2),
        unresolved_conflicts=unresolved_conflicts,
        stakeholder_demands_addressed=total_addressed,
        ai_ready_ratio=round(ai_ready_ratio, 2),
        human_ready_ratio=round(human_ready_ratio, 2),
        stagnation_score=stagnation_score,
        fatigue_score=fatigue_score,
        suggested_transition=suggested_transition,
        suggested_reason=suggested_reason,
    )
    game.negotiation_metrics = metrics
    return metrics


def should_transition_to_final_vote(game: RoleplayGameState) -> bool:
    """Return whether the Round 2 negotiation is ready to move to Round 3."""
    metrics = evaluate_negotiation_progress(game)
    return metrics.suggested_transition


def record_check_vote(game: RoleplayGameState, role_id: str, label: str) -> None:
    """
    Record a Round 2 check-vote position.

    :param game: Active game state.
    :type game: RoleplayGameState
    :param role_id: Stakeholder id.
    :type role_id: str
    :param label: One of support / oppose / undecided.
    :type label: str
    """
    if label not in CHECK_VOTE_LABELS:
        raise ValueError(f"Invalid check-vote label: {label}.")
    game.check_votes[role_id] = RoleplayVote(role_id=role_id, label=label)


def record_final_vote(game: RoleplayGameState, role_id: str, label: str) -> None:
    """
    Record a final vote position in Round 3.

    :param game: Active game state.
    :type game: RoleplayGameState
    :param role_id: Stakeholder id.
    :type role_id: str
    :param label: Final vote label.
    :type label: str
    """
    if label not in FINAL_VOTE_LABELS:
        raise ValueError(f"Invalid final-vote label: {label}.")
    game.final_votes[role_id] = RoleplayVote(role_id=role_id, label=label)


def withdraw_role(game: RoleplayGameState, role_id: str) -> RoleplayOutcome:
    """
    Mark a stakeholder as withdrawn and resolve critical failure if applicable.

    :param game: Active game state.
    :type game: RoleplayGameState
    :param role_id: Withdrawing stakeholder id.
    :type role_id: str
    :return: Current outcome after the withdrawal.
    :rtype: RoleplayOutcome
    """
    if role_id not in game.withdrawn_roles:
        game.withdrawn_roles.append(role_id)

    trigger_roles = set(game.scenario.critical_failure.get("trigger_roles", []))
    if role_id in trigger_roles:
        game.outcome = RoleplayOutcome(
            outcome="critical_failure",
            endorsements=0,
            detail=game.scenario.critical_failure.get(
                "outcome",
                "The meeting collapses and a unilateral decision is imposed.",
            ),
        )
    return game.outcome


def resolve_game_outcome(game: RoleplayGameState) -> RoleplayOutcome:
    """
    Resolve the final outcome using final votes and critical-failure state.

    :param game: Active game state.
    :type game: RoleplayGameState
    :return: Resolved outcome object.
    :rtype: RoleplayOutcome
    """
    if game.outcome is not None:
        return game.outcome

    if game.active_proposal is None:
        game.outcome = RoleplayOutcome(
            outcome="lose",
            endorsements=0,
            detail="No final proposal was submitted.",
        )
        return game.outcome

    if missing_proposal_dimensions(game):
        game.outcome = RoleplayOutcome(
            outcome="lose",
            endorsements=0,
            detail="The final proposal was incomplete.",
        )
        return game.outcome

    endorsements = sum(1 for vote in game.final_votes.values() if vote.label == "yes")
    goals = {role_id: vote.label == "yes" for role_id, vote in game.final_votes.items()}

    thresholds = game.game_rules.outcome_thresholds or game.game_rules.voting.get("outcome_thresholds", {})
    win_min = thresholds.get("win", {}).get("minimum_endorsements", 4)
    partial_min = thresholds.get("partial_win", {}).get("minimum_endorsements", 3)

    if endorsements >= win_min:
        game.outcome = RoleplayOutcome(outcome="win", endorsements=endorsements, detail="Proposal passed.", goals=goals)
    elif endorsements >= partial_min:
        game.outcome = RoleplayOutcome(
            outcome="partial_win",
            endorsements=endorsements,
            detail="Proposal achieved limited endorsement.",
            goals=goals,
        )
    else:
        game.outcome = RoleplayOutcome(
            outcome="lose",
            endorsements=endorsements,
            detail="Not enough stakeholders endorsed the proposal.",
            goals=goals,
        )
    return game.outcome


def _render_recent_transcript(game: RoleplayGameState, max_turns: int = 8) -> str:
    """Render the most recent turns as plain text."""
    turns = game.dialog.turns[-max_turns:]
    if not turns:
        return "No turns have been recorded yet."
    return "\n".join(f"{turn.speaker}: {turn.text}" for turn in turns)


def _render_proposal_summary(game: RoleplayGameState) -> str:
    """Render the current proposal status."""
    if game.active_proposal is None:
        return "No working proposal has been submitted yet."

    lines = [f"Working proposal version {game.active_proposal.version}:"]
    for dimension_id in game.required_dimension_ids():
        value = game.active_proposal.dimensions.get(dimension_id, "").strip() or "[missing]"
        lines.append(f"- {dimension_id}: {value}")
    return "\n".join(lines)


def build_roleplay_turn_prompt(game: RoleplayGameState, role_id: str) -> str:
    """
    Build a self-contained prompt for a stakeholder's next turn.

    :param game: Active game state.
    :type game: RoleplayGameState
    :param role_id: Stakeholder id who is about to speak.
    :type role_id: str
    :return: Prompt text.
    :rtype: str
    """
    stakeholder = game.scenario.stakeholder_map()[role_id]
    round_info = game.current_round()
    current_event = game.dialog.notes.get("last_event") if game.dialog.notes else None

    sections = [
        f"You are about to speak as {stakeholder.display_name}.",
        f"Current round: {round_info.get('title', game.round_state.round_title)}.",
        f"Round purpose: {round_info.get('purpose', '')}",
        f"Current speaker expected: {role_id}.",
        "Recent transcript:",
        _render_recent_transcript(game),
        "Current proposal status:",
        _render_proposal_summary(game),
    ]

    if current_event:
        sections.extend(
            [
                "Latest meeting event:",
                current_event.get("announcement", ""),
            ]
        )

    negotiation_state = game.negotiation_states.get(role_id)
    if game.round_state.round_id == "round_2_negotiation" and negotiation_state:
        sections.extend(
            [
                "Your current internal negotiation state:",
                (
                    f"satisfaction={negotiation_state.satisfaction_score}/100; "
                    f"confidence={negotiation_state.consensus_confidence}/100; "
                    f"flexibility={negotiation_state.flexibility_score}/100; "
                    f"patience={negotiation_state.patience_score}/100; "
                    f"last_action={negotiation_state.last_action}; "
                    f"ready_to_vote={negotiation_state.ready_to_vote}."
                ),
                (
                    "If you speak, choose one move implicitly through your response: continue discussion, "
                    "request revisions, offer compromise, signal conditional readiness, or signal full readiness."
                ),
            ]
        )

    if game.round_state.round_id == "round_3_final_proposal":
        missing = missing_proposal_dimensions(game)
        if missing:
            sections.append(
                "Important: the working proposal is incomplete. Prioritize missing dimensions: "
                + ", ".join(missing)
                + "."
            )

    sections.append(
        "Speak in 1 short paragraph from your stakeholder perspective. Advance negotiation rather than summarizing the whole meeting."
    )
    return "\n\n".join(section for section in sections if section)


def build_moderator_prompt(
    game: RoleplayGameState,
    purpose: str,
    event: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build a moderator prompt for structured meeting management.

    :param game: Active game state.
    :type game: RoleplayGameState
    :param purpose: Moderator task, such as opening, summary, event, vote_call, or debrief.
    :type purpose: str
    :param event: Optional event payload for event announcements.
    :type event: Optional[dict]
    :return: Prompt text.
    :rtype: str
    """
    round_info = game.current_round()
    stakeholder_names = ", ".join(
        stakeholder.display_name for stakeholder in game.scenario.stakeholders
    )
    base = [
        "You are facilitating a multi-stakeholder SWM negotiation meeting.",
        f"Current round: {round_info.get('title', game.round_state.round_title)}.",
        f"Stakeholders: {stakeholder_names}.",
        "Recent transcript:",
        _render_recent_transcript(game),
        "Current proposal status:",
        _render_proposal_summary(game),
    ]

    if purpose == "opening":
        narrative = game.scenario.narrative
        tensions = narrative.get("public_tensions", [])
        base.append(
            "Open the meeting clearly. State the crisis, why it matters now, the deadline, and the consequence of failure."
        )
        if narrative.get("public_crisis"):
            base.append(f"Public crisis: {narrative['public_crisis']}")
        if tensions:
            base.append("Key tensions to mention: " + "; ".join(tensions))
    elif purpose == "round_summary":
        base.append(
            "Summarize the main positions and tensions neutrally in 3-5 sentences."
        )
    elif purpose == "event":
        announcement = event.get("announcement", "") if event else ""
        base.append(
            "Announce the new event clearly and explain in one sentence why it changes negotiation pressure."
        )
        if announcement:
            base.append(f"Event to announce: {announcement}")
    elif purpose == "vote_call":
        base.append(
            "Call the vote clearly and instruct each stakeholder to state only yes or no based on whether the proposal meets their needs and goals."
        )
    elif purpose == "proposal_check":
        missing = missing_proposal_dimensions(game)
        if missing:
            base.append(
                "Tell the room the proposal is incomplete and name the missing dimensions: "
                + ", ".join(missing)
                + "."
            )
        else:
            base.append("Confirm that the proposal is complete and ready for the final vote.")
    elif purpose == "convergence_check":
        metrics = evaluate_negotiation_progress(game)
        base.append(
            "Summarize negotiation progress neutrally. Identify unresolved issues, whether convergence is emerging, "
            "and whether the room should keep revising or start finalizing a proposal."
        )
        base.append(
            "Current convergence signals: "
            f"proposal quality {metrics.proposal_quality_score}/100; "
            f"conflict volatility {metrics.conflict_volatility_score}/100; "
            f"AI readiness ratio {metrics.ai_ready_ratio:.0%}; "
            f"human readiness ratio {metrics.human_ready_ratio:.0%}."
        )
        if metrics.suggested_reason:
            base.append("System note: " + metrics.suggested_reason)
    elif purpose == "debrief":
        base.append(
            "Provide a short debrief covering the proposal, yes/no vote outcome, which stakeholders reached their goals, and unresolved tensions."
        )
    else:
        base.append("Respond as a concise moderator managing the meeting process.")

    return "\n\n".join(base)


def generate_ai_turn(runtime: RoleplayRuntime, role_id: Optional[str] = None) -> str:
    """
    Generate and record the next stakeholder turn using an AI agent.

    :param runtime: Runtime bundle.
    :type runtime: RoleplayRuntime
    :param role_id: Optional explicit stakeholder id; defaults to the current speaker.
    :type role_id: Optional[str]
    :return: Generated text.
    :rtype: str
    """
    game = runtime.game
    role_id = role_id or game.current_speaker()
    if role_id is None:
        raise ValueError("No current speaker is set.")
    if role_id not in runtime.agents:
        raise ValueError(f"No AI agent is available for role '{role_id}'.")

    prompt = build_roleplay_turn_prompt(game, role_id)
    text = runtime.agents[role_id](prompt, current_dialog=game.dialog)
    record_turn(game, role_id, text)
    return text


def generate_moderator_message(
    runtime: RoleplayRuntime,
    purpose: str,
    event: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate and record a moderator message.

    :param runtime: Runtime bundle.
    :type runtime: RoleplayRuntime
    :param purpose: Moderator task name.
    :type purpose: str
    :param event: Optional event payload for event announcements.
    :type event: Optional[dict]
    :return: Generated moderator text.
    :rtype: str
    """
    game = runtime.game
    role_id = game.moderator_role
    if role_id is None:
        raise ValueError("No moderator role is configured for this game.")
    if role_id not in runtime.agents:
        raise ValueError(f"No AI agent is available for moderator role '{role_id}'.")

    prompt = build_moderator_prompt(game, purpose=purpose, event=event)
    text = runtime.agents[role_id](prompt, current_dialog=game.dialog)

    moderator_name = game.scenario.stakeholder_map()[role_id].display_name
    game.dialog.turns.append(Turn(speaker=moderator_name, text=text))
    return text
