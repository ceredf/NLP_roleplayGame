"""
Terminal CLI for the SWM role-play game.

This is a pragmatic MVP interface for single-console play:

- one or more human-controlled roles
- AI-filled remaining roles
- moderator opening / summaries when available
- round progression and transcript capture
- structured proposal entry in Round 3
- check votes and final votes with AI vote helpers
"""
# SPDX-FileCopyrightText: Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-License-Identifier: MIT
import argparse
import json
import re

from typing import Dict, Optional, Tuple

from .roleplay import (
    default_city_x_game_rules_path,
    default_city_x_scenario_path,
    load_and_prepare_roleplay_session,
    load_roleplay_scenario,
)
from .roleplay_engine import (
    advance_round,
    amend_working_proposal,
    create_roleplay_runtime,
    create_working_proposal,
    generate_ai_turn,
    generate_moderator_message,
    maybe_inject_midpoint_event,
    missing_proposal_dimensions,
    record_check_vote,
    record_final_vote,
    record_turn,
    resolve_game_outcome,
    withdraw_role,
)


def parse_ai_vote_response(text: str, stage: str) -> Tuple[str, str]:
    """
    Parse a free-form AI vote response into a canonical vote label and optional condition.

    :param text: Raw model text.
    :type text: str
    :param stage: Either "check" or "final".
    :type stage: str
    :return: Tuple of (label, unused_detail).
    :rtype: tuple[str, str]
    """
    normalized = text.strip().lower()
    if stage == "check":
        for label in ["undecided", "oppose", "support"]:
            if re.search(rf"\b{re.escape(label)}\b", normalized):
                return label, ""
        return "undecided", ""

    if re.search(r"\byes\b", normalized):
        return "yes", ""
    if re.search(r"\bno\b", normalized):
        return "no", ""
    return "no", ""


def _print_block(title: str, text: str) -> None:
    """Print a small titled text block."""
    print()
    print(f"== {title} ==")
    print(text)


def _safe_generate_moderator(runtime, purpose: str, event: Optional[Dict] = None) -> str:
    """Generate moderator text with a fallback path."""
    try:
        return generate_moderator_message(runtime, purpose=purpose, event=event)
    except Exception:
        if purpose == "opening":
            narrative = runtime.game.scenario.narrative
            deadline = narrative.get("deadline_days", "unknown")
            tensions = narrative.get("public_tensions", [])
            tension_text = ""
            if tensions:
                tension_text = " Key tensions: " + "; ".join(tensions[:3]) + "."
            return (
                f"This emergency meeting is now open. The city faces a waste crisis, "
                f"and stakeholders have {deadline} days to produce an action plan."
                f"{tension_text}"
            )
        if purpose == "round_summary":
            return "The round ends with visible tension, overlapping demands, and no full consensus yet."
        if purpose == "event" and event:
            return event.get("announcement", "A new event changes the political dynamics.")
        if purpose == "proposal_check":
            missing = missing_proposal_dimensions(runtime.game)
            return (
                "The proposal is incomplete. Missing dimensions: " + ", ".join(missing)
                if missing else
                "The proposal is complete and ready for the final vote."
            )
        if purpose == "debrief":
            return "The meeting has ended. Review the final proposal, vote positions, and unresolved tensions."
        return "The moderator moves the meeting forward."


def _safe_generate_ai_turn(runtime, role_id: str) -> str:
    """Generate an AI turn with a fallback if the model call fails."""
    try:
        return generate_ai_turn(runtime, role_id=role_id)
    except Exception as exc:
        fallback = f"I need more concrete guarantees before I can move from my current position. [{exc}]"
        record_turn(runtime.game, role_id, fallback)
        return fallback


def _safe_generate_ai_vote(runtime, role_id: str, stage: str) -> Tuple[str, str]:
    """Ask an AI role to vote without mutating its dialogue memory."""
    agent = runtime.agents[role_id]
    stakeholder = runtime.game.scenario.stakeholder_map()[role_id]
    prompt = [
        f"You are voting as {stakeholder.display_name}.",
        "Recent meeting transcript:",
        "\n".join(f"{turn.speaker}: {turn.text}" for turn in runtime.game.dialog.turns[-8:]) or "No turns yet.",
        "Current proposal:",
        json.dumps(
            runtime.game.active_proposal.dimensions if runtime.game.active_proposal else {},
            indent=2,
        ),
    ]
    if stage == "check":
        prompt.append("Return only one word: support, oppose, or undecided.")
    else:
        prompt.append(
            "Vote only yes or no."
        )
        prompt.append(
            "Base your vote on whether this proposal meets your needs, minimum requirements, and main goals."
        )

    try:
        text = agent.response_lookahead("\n\n".join(prompt))
    except Exception:
        text = "undecided" if stage == "check" else "no"

    return parse_ai_vote_response(text, stage=stage)


def _prompt_human_turn(role_id: str, display_name: str) -> str:
    """Prompt a human-controlled role for a turn."""
    print()
    print(f"Your turn as {display_name} ({role_id}).")
    print("Enter your statement, or type /skip or /withdraw.")
    return input("> ").strip()


def _suggest_moves(runtime, role_id: str) -> str:
    """Return practical move suggestions for the current human role."""
    game = runtime.game
    stakeholder = game.scenario.stakeholder_map()[role_id]
    round_id = game.round_state.round_id
    suggestions = []

    if round_id == "round_1_opening_positions":
        suggestions.extend([
            "State your main goal clearly and explain why the crisis affects your role.",
            "Name one non-negotiable need or red line.",
            "Challenge another stakeholder's framing if it hurts your interests.",
        ])
    elif round_id == "round_2_negotiation":
        suggestions.extend([
            "Ask for one concrete concession from another stakeholder.",
            "Offer a trade: what can you support if one of your needs is met?",
            "Build a coalition by naming a point of agreement with one other role.",
        ])
    else:
        suggestions.extend([
            "Push to fill any missing proposal dimensions.",
            "Amend one part of the proposal so it better serves your needs.",
            "Explain plainly what would make you vote yes or no.",
        ])

    if stakeholder.public_profile.special_move:
        suggestions.append(f"Special move available: {stakeholder.public_profile.special_move}")

    if stakeholder.public_profile.negotiating_leverage:
        suggestions.append(
            "Leverage idea: " + stakeholder.public_profile.negotiating_leverage[0]
        )

    return "\n".join(f"- {item}" for item in suggestions)


def _advance_speaker(game) -> None:
    """Advance the round speaker cursor without recording a turn."""
    order_len = len(game.round_state.turn_order)
    if order_len:
        game.round_state.current_turn_index = (game.round_state.current_turn_index + 1) % order_len


def _safe_generate_ai_turn_or_skip(runtime, role_id: str) -> Tuple[bool, str]:
    """Let an AI role either speak or skip if it has nothing new to add."""
    agent = runtime.agents[role_id]
    stakeholder = runtime.game.scenario.stakeholder_map()[role_id]
    prompt = [
        f"You are {stakeholder.display_name}.",
        "Recent meeting transcript:",
        "\n".join(f"{turn.speaker}: {turn.text}" for turn in runtime.game.dialog.turns[-10:]) or "No turns yet.",
        "If you have nothing new or useful to add right now, reply with only SKIP.",
        "Otherwise, reply with one short paragraph that advances the discussion.",
    ]
    try:
        text = agent.response_lookahead("\n\n".join(prompt)).strip()
    except Exception:
        text = "SKIP"
    if text.upper() == "SKIP":
        return True, "SKIP"
    return False, text


def _run_round_turns(runtime) -> bool:
    """
    Run the current round until every stakeholder skips.

    :return: True if the game should continue, False if it ended.
    :rtype: bool
    """
    game = runtime.game
    skipped_roles = set()
    while True:
        role_id = game.current_speaker()
        stakeholder = game.scenario.stakeholder_map()[role_id]

        if role_id in game.human_roles:
            _print_block("Possible Moves", _suggest_moves(runtime, role_id))
            text = _prompt_human_turn(role_id, stakeholder.display_name)
            if text == "/withdraw":
                outcome = withdraw_role(game, role_id)
                _print_block("Critical Failure", outcome.detail)
                return False
            if text in {"", "/pass", "/skip"}:
                skipped_roles.add(role_id)
                print(f"{stakeholder.display_name} skips for now.")
                _advance_speaker(game)
            else:
                record_turn(game, role_id, text)
                skipped_roles.discard(role_id)
                print(f"{stakeholder.display_name}: {text}")
        else:
            should_skip, text = _safe_generate_ai_turn_or_skip(runtime, role_id)
            print()
            if should_skip:
                skipped_roles.add(role_id)
                print(f"{stakeholder.display_name} skips for now.")
                _advance_speaker(game)
            else:
                record_turn(game, role_id, text)
                skipped_roles.discard(role_id)
                print(f"{stakeholder.display_name}: {text}")

        event = maybe_inject_midpoint_event(game)
        if event:
            announcement = _safe_generate_moderator(runtime, purpose="event", event=event)
            _print_block("Event", announcement)

        if game.outcome is not None:
            return False
        if len(skipped_roles) == len(game.scenario.stakeholders):
            return True


def _collect_check_votes(runtime) -> None:
    """Collect Round 2 check votes from humans and AI."""
    game = runtime.game
    _print_block(
        "Temperature Check",
        "This is not the final vote. It measures where you stand right now.\n"
        "- support: you could support the current direction already\n"
        "- oppose: the current direction does not meet your needs\n"
        "- undecided: you still need changes, information, or negotiation",
    )
    for stakeholder in game.scenario.stakeholders:
        if stakeholder.id in game.human_roles:
            while True:
                vote = input(f"{stakeholder.display_name} vote [support/oppose/undecided]: ").strip().lower()
                if vote in {"support", "oppose", "undecided"}:
                    break
                print("Please enter support, oppose, or undecided.")
            record_check_vote(game, stakeholder.id, vote)
        else:
            vote, _ = _safe_generate_ai_vote(runtime, stakeholder.id, stage="check")
            record_check_vote(game, stakeholder.id, vote)
            print(f"{stakeholder.display_name} check vote: {vote}")


def _draft_dimension_with_ai(runtime, dimension: Dict[str, str]) -> str:
    """Ask the moderator to suggest wording for one proposal dimension."""
    moderator_id = runtime.game.moderator_role
    if moderator_id is None or moderator_id not in runtime.agents:
        return ""
    prompt = [
        "Draft one concise proposal element from the discussion so far.",
        f"Dimension: {dimension['label']}",
        f"Description: {dimension['description']}",
        "Recent discussion:",
        "\n".join(f"{turn.speaker}: {turn.text}" for turn in runtime.game.dialog.turns[-12:]) or "No turns yet.",
        "Return only the draft text for this one dimension.",
    ]
    try:
        return runtime.agents[moderator_id].response_lookahead("\n\n".join(prompt)).strip()
    except Exception:
        return ""


def _prompt_proposal_dimensions(runtime) -> Dict[str, str]:
    """Prompt the user to fill every required proposal dimension with optional AI help."""
    game = runtime.game
    values: Dict[str, str] = {}
    print()
    print("Finalize the proposal. Keep each answer short.")
    print("Type /ai to ask for a draft suggestion for one dimension.")
    for dimension in game.scenario.proposal_dimensions:
        label = dimension["label"]
        description = dimension["description"]
        print()
        print(f"{label}: {description}")
        while True:
            value = input("> ").strip()
            if value == "/ai":
                suggestion = _draft_dimension_with_ai(runtime, dimension)
                if suggestion:
                    print(f"AI suggestion: {suggestion}")
                else:
                    print("No AI suggestion available. Please enter your own text.")
                continue
            values[dimension["id"]] = value
            break
    return values


def _proposal_brainstorm(runtime) -> bool:
    """Run a collaborative proposal discussion before the final draft is entered."""
    _print_block(
        "Proposal Discussion",
        "Discuss the proposal first. Everyone can contribute more than once.\n"
        "The round ends only when every stakeholder skips.",
    )
    return _run_round_turns(runtime)


def _draft_or_update_proposal(runtime) -> None:
    """Create or amend the working proposal from terminal input."""
    game = runtime.game
    proposer = game.human_roles[0] if game.human_roles else game.moderator_role
    dimensions = _prompt_proposal_dimensions(runtime)

    if game.active_proposal is None:
        create_working_proposal(game, proposer_role_id=proposer, dimensions=dimensions)
    else:
        amend_working_proposal(game, proposer_role_id=proposer, amendments=dimensions, note="CLI proposal update")

    proposal_lines = [f"{key}: {value}" for key, value in game.active_proposal.dimensions.items()]
    _print_block("Working Proposal", "\n".join(proposal_lines))
    _print_block("Proposal Check", _safe_generate_moderator(runtime, purpose="proposal_check"))


def _collect_final_votes(runtime) -> None:
    """Collect final votes from humans and AI."""
    game = runtime.game
    _print_block("Final Vote", _safe_generate_moderator(runtime, purpose="vote_call"))
    for stakeholder in game.scenario.stakeholders:
        if stakeholder.id in game.human_roles:
            while True:
                vote = input(
                    f"{stakeholder.display_name} final vote [yes/no]. "
                    "Vote based on whether your needs and goals were met: "
                ).strip().lower()
                if vote in {"yes", "no"}:
                    break
                print("Please enter yes or no.")
            record_final_vote(game, stakeholder.id, vote)
        else:
            vote, _ = _safe_generate_ai_vote(runtime, stakeholder.id, stage="final")
            record_final_vote(game, stakeholder.id, vote)
            print(f"{stakeholder.display_name} final vote: {vote}")


def _render_goal_summary(runtime) -> str:
    """Render whether each stakeholder's goals were reached."""
    game = runtime.game
    lines = []
    for stakeholder in game.scenario.stakeholders:
        reached = game.outcome.goals.get(stakeholder.id, False)
        status = "reached" if reached else "not reached"
        goal = stakeholder.public_profile.primary_goal or "No primary goal provided."
        lines.append(f"{stakeholder.display_name}: {status} | Goal: {goal}")
    return "\n".join(lines)


def run_cli_game(args) -> int:
    """Run the interactive CLI game loop."""
    session = load_and_prepare_roleplay_session(
        args.scenario,
        rules_path=args.rules,
        human_roles=args.human_role,
        model=args.model,
        think=args.think,
    )
    runtime = create_roleplay_runtime(session)
    scenario = runtime.game.scenario

    narrative = scenario.narrative
    scenario_text = [
        scenario.title,
        scenario.summary,
        "",
        f"Crisis: {narrative.get('public_crisis', '')}",
        f"Deadline: {narrative.get('deadline_days', 'unknown')} days",
        f"If no agreement: {narrative.get('if_no_agreement', '')}",
    ]
    tensions = narrative.get("public_tensions", [])
    if tensions:
        scenario_text.append("")
        scenario_text.append("Key tensions:")
        scenario_text.extend(f"- {item}" for item in tensions)
    _print_block("Scenario", "\n".join(line for line in scenario_text if line is not None))
    for role_id in runtime.game.human_roles:
        _print_block(
            f"Role Card: {scenario.stakeholder_map()[role_id].display_name}",
            session.get_role_card(role_id, reveal_private=True),
        )

    _print_block("Opening", _safe_generate_moderator(runtime, purpose="opening"))

    if not _run_round_turns(runtime):
        return 0
    _print_block("Round 1 Summary", _safe_generate_moderator(runtime, purpose="round_summary"))

    advance_round(runtime.game)
    if not _run_round_turns(runtime):
        return 0
    _collect_check_votes(runtime)

    advance_round(runtime.game)
    if not _proposal_brainstorm(runtime):
        return 0
    _draft_or_update_proposal(runtime)
    _collect_final_votes(runtime)
    outcome = resolve_game_outcome(runtime.game)

    _print_block("Outcome", f"{outcome.outcome} ({outcome.endorsements} endorsements)\n{outcome.detail}")
    _print_block("Goals Reached", _render_goal_summary(runtime))
    _print_block("Debrief", _safe_generate_moderator(runtime, purpose="debrief"))

    if args.save_transcript:
        runtime.game.dialog.to_file(args.save_transcript)
        print()
        print(f"Transcript saved to {args.save_transcript}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(description="Run the SWM role-play game in the terminal.")
    parser.add_argument("--scenario", default=default_city_x_scenario_path(), help="Scenario-pack JSON path.")
    parser.add_argument("--rules", default=default_city_x_game_rules_path(), help="Hidden game-rules JSON path.")
    parser.add_argument(
        "--human-role",
        action="append",
        default=None,
        help="Stakeholder id reserved for a human player. Repeat to add multiple roles.",
    )
    parser.add_argument("--model", default=None, help="Optional model override, for example ollama:qwen2.5:14b.")
    parser.add_argument("--think", action="store_true", help="Enable thinking mode for AI roles.")
    parser.add_argument("--save-transcript", default="", help="Optional output path for the final dialog JSON.")
    parser.add_argument("--inspect", action="store_true", help="Print scenario info and exit.")
    return parser


def main(argv=None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.inspect:
        scenario = load_roleplay_scenario(args.scenario)
        print(f"Scenario: {scenario.title}")
        print(f"ID: {scenario.scenario_id}")
        print("Stakeholders:")
        for stakeholder in scenario.stakeholders:
            print(f"- {stakeholder.id}: {stakeholder.display_name}")
        return 0

    if not args.human_role:
        args.human_role = ["community_member"]

    return run_cli_game(args)


if __name__ == "__main__":
    raise SystemExit(main())
