#!/usr/bin/env python3
"""Run a full City X game flow against a real cloud-backed Vertex AI model.

This is a smoke test for repeated local verification of the Streamlit game
without needing browser automation. It drives the same core game functions used
by the UI and reports whether each run reaches the final outcome stage.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import sys
import time
from contextlib import contextmanager
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "examples" / "swm_roleplay"
APP_PATH = APP_DIR / "streamlit_app.py"

DEFAULT_ROLES = [
    "community_member",
    "municipal_government",
    "informal_sector_worker",
]

ROUND2_TEXT = {
    "financing": (
        "Create a public Eastfield transition fund with national and municipal "
        "contributions, matched quarterly by the operator, with a published "
        "12-month budget and emergency reserve."
    ),
    "community_health_protections": (
        "Launch mobile clinics within 30 days, publish weekly air and water "
        "data, and give residents an independent complaint hotline with rapid response."
    ),
    "livelihoods": (
        "Guarantee protected access to work during transition, offer income "
        "support for disrupted households, and fund retraining and formalization pathways."
    ),
    "monitoring_and_enforcement": (
        "Create an independent oversight board with community seats, monthly "
        "public reports, inspection rights, and financial penalties for missed milestones."
    ),
}

for logger_name in (
    "streamlit",
    "streamlit.runtime.scriptrunner_utils.script_run_context",
    "streamlit.runtime.state.session_state_proxy",
):
    logging.getLogger(logger_name).setLevel(logging.ERROR)

ROUND3_TEXT = {
    "financing": (
        "The transition fund starts within 30 days, names each contributor, "
        "sets first-year amounts, and requires quarterly public disclosure."
    ),
    "community_health_protections": (
        "Independent clinics and testing begin within 30 days, results are "
        "public every week, and emergency protections activate automatically after violations."
    ),
    "livelihoods": (
        "Workers keep protected site access during transition, receive bridge "
        "income for disruptions, and get guaranteed retraining placements within six months."
    ),
    "monitoring_and_enforcement": (
        "An independent board with community voting seats can inspect the site, "
        "publish monthly scorecards, and trigger penalties when deadlines are missed."
    ),
}

ROLE_DIMENSION = {
    "community_member": "community_health_protections",
    "municipal_government": "financing",
    "informal_sector_worker": "livelihoods",
    "national_government": "timeline",
    "ngo_civil_society": "monitoring_and_enforcement",
    "private_sector_company": "financing",
}


def _load_app_module():
    module_name = "city_x_streamlit_smoke"
    if module_name in sys.modules:
        del sys.modules[module_name]
    sys.path.insert(0, str(APP_DIR))
    try:
        spec = importlib.util.spec_from_file_location(module_name, APP_PATH)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


class FakeState(dict):
    __getattr__ = dict.get

    def __setattr__(self, key, value):
        self[key] = value


@contextmanager
def _noop_spinner(_msg=""):
    yield


class FakeStreamlit:
    def __init__(self):
        self.session_state = FakeState()

    def rerun(self):
        return None

    def spinner(self, msg=""):
        return _noop_spinner(msg)


def _human_opening(app, role_id: str) -> str:
    stakeholder = app.stakeholder_map()[role_id]
    responsibility = (
        "Responsibility is shared across government and the operator, and I want a binding agreement "
        "with named actions, enforcement, and a rapid start date."
    )
    return f"{stakeholder.public_profile.opening_position} {responsibility}"


def _round2_bid_text(app, role_id: str, dimension: str) -> tuple[str, str]:
    reason_map = {
        "financing": "without named funding, none of the promised changes can start on time",
        "community_health_protections": "residents need visible health safeguards immediately, not after the site changes hands",
        "livelihoods": "workers and families cannot absorb the transition costs alone",
        "monitoring_and_enforcement": "the room needs independent oversight or the agreement will not be trusted",
        "timeline": "the agreement needs an immediate first action and clear deadlines",
    }
    reason = reason_map[dimension]
    return reason, f"My priority is {app.SECTION_LABELS[dimension]} because {reason}."


def play_once(role_id: str, model: str) -> dict:
    app = _load_app_module()
    app.st = FakeStreamlit()
    app.ensure_state()
    ai_stats = {"calls": 0, "empty_calls": 0, "backend_errors": []}

    original_handle_llm_error = app._handle_llm_error
    original_call_agent = app._call_agent

    def tracked_handle_llm_error(exc: Exception) -> None:
        ai_stats["backend_errors"].append(str(exc))
        original_handle_llm_error(exc)

    def tracked_call_agent(role: str, prompt: str) -> str:
        ai_stats["calls"] += 1
        text = original_call_agent(role, prompt)
        if not text.strip():
            ai_stats["empty_calls"] += 1
        return text

    app._handle_llm_error = tracked_handle_llm_error
    app._call_agent = tracked_call_agent

    from sdialog.roleplay_engine import advance_round

    started = time.perf_counter()
    app.init_game(model, role_id, False)

    if app.st.session_state.stage != "role_reveal":
        raise RuntimeError(f"Expected role_reveal after init, got {app.st.session_state.stage}")

    app.st.session_state.stage = "round1"
    for speaker_role in app.ROUND1_ORDER:
        if speaker_role == role_id:
            text = _human_opening(app, speaker_role)
            app._append_turn(app.stakeholder_map()[speaker_role].display_name, text, human=True)
        else:
            text = app._generate_round1_ai_statement(speaker_role)
            app._append_turn(app.stakeholder_map()[speaker_role].display_name, text)
        app.st.session_state.round1_spoken.add(speaker_role)

    app.st.session_state.round1_summary = app._moderator_text(
        "round1_summary",
        "Summarize the main tensions and likely coalition lines after the opening positions.",
    )
    advance_round(app.game())
    app.st.session_state.stage = "round2_bids"

    dimension = ROLE_DIMENSION.get(role_id, "financing")
    reason_txt, bid_text = _round2_bid_text(app, role_id, dimension)
    app._do_collect_bids(dimension, reason_txt, bid_text)

    app.st.session_state.stage = "round2_table"
    for dim in app.NEGOTIABLE_DIMENSIONS:
        app._submit_dimension_move(dim, ROUND2_TEXT[dim])
        app._advance_round2_dimension()

    if app.st.session_state.stage != "round2_flagging":
        raise RuntimeError(f"Expected round2_flagging, got {app.st.session_state.stage}")

    app._do_lock_flags({dim: "accept" for dim in app.NEGOTIABLE_DIMENSIONS})

    if app.st.session_state.stage != "round2_results":
        raise RuntimeError(f"Expected round2_results, got {app.st.session_state.stage}")

    if app.st.session_state.round3_dimensions:
        advance_round(app.game())
        app.st.session_state.round3_addressed = set()
        app.st.session_state.stage = "round3"
        for dim in app.st.session_state.round3_dimensions:
            app._submit_round3_move(dim, ROUND3_TEXT[dim])
            app._advance_round3_dimension()

    if app.st.session_state.stage != "final_vote":
        raise RuntimeError(f"Expected final_vote, got {app.st.session_state.stage}")

    app._do_final_vote("conditional_endorsement")

    if app.st.session_state.stage != "outcome":
        raise RuntimeError(f"Expected outcome, got {app.st.session_state.stage}")

    outcome = app.game().outcome
    return {
        "role": role_id,
        "model": model,
        "stage": app.st.session_state.stage,
        "outcome": getattr(outcome, "outcome", ""),
        "detail": getattr(outcome, "detail", ""),
        "votes": sorted(app.game().final_votes.keys()),
        "goal_evaluations": len(app.st.session_state.goal_evaluations),
        "round3_dimensions": list(app.st.session_state.round3_dimensions),
        "transcript_turns": len(app.game().dialog.turns),
        "ai_call_count": ai_stats["calls"],
        "empty_ai_call_count": ai_stats["empty_calls"],
        "backend_error_count": len(ai_stats["backend_errors"]),
        "first_backend_error": ai_stats["backend_errors"][0] if ai_stats["backend_errors"] else "",
        "duration_seconds": round(time.perf_counter() - started, 2),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        default="vertexai:gemini-2.5-flash",
        help="Model string to pass into the game, e.g. vertexai:gemini-2.5-flash-lite",
    )
    parser.add_argument(
        "--roles",
        nargs="+",
        default=DEFAULT_ROLES,
        help="Human roles to test sequentially.",
    )
    args = parser.parse_args()

    failures = 0
    for role_id in args.roles:
        try:
            result = play_once(role_id, args.model)
            print(json.dumps(result, ensure_ascii=True))
        except Exception as exc:
            failures += 1
            print(json.dumps({"role": role_id, "model": args.model, "error": str(exc)}, ensure_ascii=True))

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
