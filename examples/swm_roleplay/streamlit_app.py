"""
City X — Negotiation Game (Streamlit)

This interface runs a structured three-round negotiation:
- Phase 0: setup + role reveal
- Round 1: opening positions in fixed order
- Round 2: proposal building through one dimension at a time
- Round 3: resolve contested dimensions, then cast final votes
"""

import json
import os
import re
from typing import Dict, List, Tuple

import streamlit as st

from langchain_core.messages import HumanMessage

from ui import theme, components

from sdialog.roleplay import (
    default_city_x_game_rules_path,
    default_city_x_scenario_path,
    load_and_prepare_roleplay_session,
    load_roleplay_scenario,
)
from sdialog.roleplay_engine import (
    advance_round,
    amend_working_proposal,
    create_roleplay_runtime,
    create_working_proposal,
    record_final_vote,
    resolve_game_outcome,
)


NEGOTIABLE_DIMENSIONS = [
    "financing",
    "community_health_protections",
    "livelihoods",
    "monitoring_and_enforcement",
]
PREFILLED_DIMENSIONS = {
    "core_action": "Eastfield landfill begins formal operational transition within 18 months.",
    "timeline": "At least one concrete action begins within 30 days of any agreement.",
}
FLAG_LABELS = ["accept", "accept_with_condition", "reject"]
FINAL_VOTE_LABELS = [
    "unconditional_endorsement",
    "conditional_endorsement",
    "abstention",
    "rejection",
]
ROUND1_ORDER = [
    "national_government",
    "municipal_government",
    "private_sector_company",
    "ngo_civil_society",
    "community_member",
    "informal_sector_worker",
]
REACTION_PRIORITY = {
    "financing": [
        "national_government",
        "municipal_government",
        "private_sector_company",
        "ngo_civil_society",
    ],
    "community_health_protections": [
        "community_member",
        "ngo_civil_society",
        "municipal_government",
        "national_government",
    ],
    "livelihoods": [
        "informal_sector_worker",
        "private_sector_company",
        "ngo_civil_society",
        "municipal_government",
    ],
    "monitoring_and_enforcement": [
        "ngo_civil_society",
        "community_member",
        "national_government",
        "municipal_government",
    ],
}
# Stakeholder colors/emoji live in ui.theme (single source of truth) so cards,
# avatars, badges, meters and transcript bubbles stay consistent.
CHAR_CONFIG: Dict[str, dict] = {
    role_id: {"emoji": t["emoji"], "color": t["color"], "bg": t["bg"]}
    for role_id, t in theme.STAKEHOLDER_THEME.items()
}
SECTION_LABELS = {
    "core_action": "Core action",
    "timeline": "Timeline",
    "financing": "Financing",
    "community_health_protections": "Community health protections",
    "livelihoods": "Livelihood protections",
    "monitoring_and_enforcement": "Monitoring and accountability",
}
MOVE_LABELS = {
    "propose": "Propose",
    "amend": "Amend",
    "block": "Block",
}
FLAG_DISPLAY = {
    "accept": "Accept",
    "accept_with_condition": "Accept with condition",
    "reject": "Reject",
}
FINAL_VOTE_DISPLAY = {
    "unconditional_endorsement": "Unconditional endorsement",
    "conditional_endorsement": "Conditional endorsement",
    "abstention": "Abstention",
    "rejection": "Rejection",
}


st.set_page_config(page_title="City X — Negotiation Game", layout="wide", page_icon="🏙️")
st.markdown(theme.css(), unsafe_allow_html=True)


def default_model_value() -> str:
    """Prefer a hosted Google model automatically when a Gemini key is present."""
    if (
        os.getenv("GOOGLE_CLOUD_PROJECT")
        or os.getenv("GCLOUD_PROJECT")
        or os.getenv("GCP_PROJECT")
        or os.getenv("K_SERVICE")
    ):
        return "vertexai:gemini-2.5-flash"
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        return "google:gemini-2.5-flash"
    return "ollama:qwen2.5:latest"


def ensure_state() -> None:
    defaults = {
        "runtime": None,
        "stage": "setup",
        "notice": "",
        "proposal_form": {},
        "round1_spoken": set(),
        "round1_summary": "",
        "round2_human_bid": None,
        "round2_ai_bids": {},
        "round2_dimension_index": 0,
        "round2_addressed": set(),
        "round2_event_fired": False,
        "round2_force_revisit": [],
        "round2_discussions": {},
        "reaction_counts": {},
        "round2_flags": {},
        "round2_dimension_status": {},
        "round2_pending_reaction": {},
        "round2_followup_done": False,
        "round3_pending_reaction": {},
        "round3_followup_done": False,
        "round3_dimensions": [],
        "round3_index": 0,
        "round3_addressed": set(),
        "final_vote_labels": {},
        "goal_evaluations": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def scenario():
    return load_roleplay_scenario(default_city_x_scenario_path())


def rt():
    return st.session_state.runtime


def game():
    return st.session_state.runtime.game


def stakeholder_map():
    return game().scenario.stakeholder_map()


def cfg(role_id: str) -> dict:
    return CHAR_CONFIG.get(role_id, {"emoji": "👤", "color": "#475569", "bg": "#f8fafc"})


def human_role() -> str:
    return game().human_roles[0]


def ai_roles() -> List[str]:
    return [role_id for role_id in ROUND1_ORDER if role_id != human_role()]


def _append_turn(speaker: str, text: str, human: bool = False) -> None:
    from sdialog import Turn

    game().dialog.turns.append(Turn(speaker=speaker, text=text))
    if human:
        game().dialog.notes["last_human_statement"] = text


def _recent_transcript(max_turns: int = 10) -> str:
    turns = game().dialog.turns[-max_turns:]
    if not turns:
        return "No statements yet."
    return "\n".join(f"{turn.speaker}: {turn.text}" for turn in turns)


_THINK_RE = re.compile(r"<think(?:ing)?>.*?</think(?:ing)?>", re.DOTALL | re.IGNORECASE)


def _handle_llm_error(exc: Exception) -> None:
    """Convert backend failures into a user-facing notice instead of a crash."""
    msg = str(exc)
    lowered = msg.lower()
    if any(token in lowered for token in ("resource_exhausted", "quota exceeded", "rate limit", "429")):
        st.session_state.notice = (
            "The Gemini backend hit a quota limit, so the game is temporarily using scripted stakeholder "
            "fallbacks. Wait a bit, switch backend, or redeploy with a billed backend if you want full AI turns."
        )
    elif any(token in lowered for token in ("service_disabled", "agent platform api", "invalid_argument", "api key", "permission denied", "unauthenticated")):
        st.session_state.notice = (
            "The selected AI backend rejected a request. The game will keep going with scripted stakeholder "
            "fallbacks until the backend configuration is fixed."
        )


def _call_agent(role_id: str, prompt: str) -> str:
    agent = rt().agents[role_id]
    # STATELESS call: pass the prompt as a one-message list. sdialog keeps the
    # agent's persona/system prompt (memory[0]) but does NOT accumulate the
    # growing dialog into context. Previously we passed the full game dialog,
    # so by Round 2 the most-used reactor (NGO covers 2 dimensions) overflowed
    # the model context and returned empty -> canned fallback every turn.
    raw = ""
    last_error = None
    for payload in ([HumanMessage(content=prompt)], prompt):
        try:
            raw = agent(payload) or ""
            break
        except Exception as exc:
            last_error = exc
    if not raw and last_error is not None:
        _handle_llm_error(last_error)
    # Some models emit a <think>...</think> block and nothing else; stripping it
    # naively would leave an empty turn. Remove the block, then fall back.
    text = _THINK_RE.sub("", raw).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.replace("(bye bye!)", "").strip()
    return text


def _defer(msg: str, fn, *args) -> None:
    """Hand a slow AI step to the next run so the input form is NOT re-drawn
    underneath a spinner (that was the duplicated-form-during-loading bug).
    The next run shows ONLY a spinner, runs ``fn`` (which itself reruns)."""
    st.session_state["_pending"] = (msg, fn, args)
    st.rerun()


def _drain_pending() -> bool:
    """If a deferred step is queued, show one clean spinner and run it.
    Returns True when it handled work (caller must return immediately)."""
    pending = st.session_state.get("_pending")
    if not pending:
        return False
    st.session_state["_pending"] = None
    msg, fn, args = pending
    with st.spinner(msg):
        fn(*args)  # fn ends in st.rerun(); control leaves here
    return True


def _advance_r2() -> None:
    _advance_round2_dimension()
    st.rerun()


def _advance_r3() -> None:
    _advance_round3_dimension()
    st.rerun()


def _do_collect_bids(dimension: str, reason_txt: str, bid_text: str) -> None:
    st.session_state.round2_human_bid = {
        "dimension": dimension, "reason": reason_txt, "text": bid_text,
    }
    ai_bids = {}
    for role_id in ai_roles():
        ai_bids[role_id] = _generate_round2_bid(
            role_id, dimension, reason_txt or "no specific reason given"
        )
    st.session_state.round2_ai_bids = ai_bids
    st.rerun()


def _do_lock_flags(human_flags: Dict[str, str]) -> None:
    ai_flags = _generate_ai_flags(NEGOTIABLE_DIMENSIONS)
    full_flags: Dict[str, Dict[str, Dict[str, str]]] = {
        human_role(): {
            dim: {"flag": human_flags[dim], "reason": "Player-selected position."}
            for dim in NEGOTIABLE_DIMENSIONS
        }
    }
    full_flags.update(ai_flags)
    for dim in NEGOTIABLE_DIMENSIONS:
        status = _classify_dimension(dim, full_flags)
        st.session_state.round2_dimension_status[dim] = status
        st.session_state.round2_flags[dim] = {
            "status": status,
            "summary": _flag_reason_summary(dim, full_flags),
            "flags": {rid: rf[dim] for rid, rf in full_flags.items()},
        }
    contested = [d for d in NEGOTIABLE_DIMENSIONS
                 if st.session_state.round2_dimension_status[d] in {"yellow", "red"}]
    st.session_state.round3_dimensions = contested
    st.session_state.round3_index = 0
    st.session_state.stage = "round2_results"
    st.rerun()


def _do_final_vote(human_vote: str) -> None:
    ai_votes = _generate_ai_final_votes()
    all_votes = {human_role(): {"vote": human_vote, "reason": "Player-selected vote."}}
    all_votes.update(ai_votes)
    st.session_state.final_vote_labels = all_votes
    for role_id, payload in all_votes.items():
        record_final_vote(game(), role_id, _map_to_engine_vote(payload["vote"]))
    resolve_game_outcome(game())
    st.session_state.goal_evaluations = _evaluate_goal_achievement()
    st.session_state.stage = "outcome"
    st.rerun()


def _stakeholder_fallback(role_id: str, dimension_id: str, player_text: str = "") -> str:
    """A concrete, in-character line so a stakeholder is never silent.

    Only used when the model returns nothing usable. Rotates through the
    stakeholder's own requirements / red lines (indexed by how many times they
    have already spoken on this dimension) and references the player's move, so
    consecutive fallbacks differ instead of looking like one canned answer.
    """
    sk = stakeholder_map()[role_id]
    label = SECTION_LABELS.get(dimension_id, dimension_id)
    reqs = list(getattr(sk.negotiation, "minimum_requirements", []) or [])
    reds = list(getattr(sk.negotiation, "red_lines", []) or [])
    turn = st.session_state.get("reaction_counts", {}).get(role_id, 0)
    lead = (
        f"On {label}, what you proposed still falls short for me. "
        if player_text.strip()
        else f"On {label}, I'm not there yet. "
    )
    parts = []
    if reqs:
        parts.append(f"I need {reqs[turn % len(reqs)].rstrip('.').strip().lower()}")
    if reds:
        parts.append(f"and I will not accept {reds[turn % len(reds)].rstrip('.').strip().lower()}")
    if not parts:
        parts.append("this still needs concrete actors, money and timelines")
    body = " ".join(parts)
    return lead + body[0].upper() + body[1:] + "."


def _moderator_text(task: str, extra: str = "") -> str:
    g = game()
    role_id = g.moderator_role or "national_government"
    if role_id in rt().agents:
        prompt = (
            "Ignore your normal stakeholder voice for this one reply. "
            "Act only as a neutral meeting moderator.\n\n"
            f"Task: {task}\n"
            f"Scenario crisis: {g.scenario.narrative.get('public_crisis', '')}\n"
            f"Deadline: {g.scenario.narrative.get('deadline_days', 60)} days\n"
            f"Consequence of failure: {g.scenario.narrative.get('if_no_agreement', '')}\n"
            f"Recent transcript:\n{_recent_transcript(8)}\n\n"
            f"{extra}\n\n"
            "Return 2-4 short sentences in clear English."
        )
        try:
            return _call_agent(role_id, prompt)
        except Exception:
            pass

    narrative = g.scenario.narrative
    if task == "opening":
        return (
            f"The Eastfield landfill crisis has entered a dangerous stage. "
            f"You have {narrative.get('deadline_days', 60)} days to produce an emergency agreement, "
            f"or {narrative.get('if_no_agreement', 'a unilateral solution will be imposed')}."
        )
    if task == "round1_summary":
        return "The room is divided over responsibility, urgency, and who should carry the cost of transition."
    if task == "event":
        return extra
    if task == "round3_intro":
        return extra
    return extra or "The moderator asks the room to stay concrete and focused."


def _sync_proposal_to_game() -> None:
    dims = {
        key: value.strip()
        for key, value in st.session_state.proposal_form.items()
        if isinstance(value, str) and value.strip()
    }
    if not dims:
        return
    if game().active_proposal is None:
        create_working_proposal(game(), human_role(), dims)
    else:
        amend_working_proposal(game(), human_role(), dims, note="Streamlit proposal update")


def _record_dimension_discussion(dimension_id: str, speaker_name: str, text: str) -> None:
    notes = st.session_state.round2_discussions.setdefault(dimension_id, [])
    notes.append(f"{speaker_name}: {text}")


def _dimension_discussion_text(dimension_id: str) -> str:
    notes = st.session_state.round2_discussions.get(dimension_id, [])
    if not notes:
        return "No focused discussion yet."
    return "\n".join(notes[-12:])


def _stakeholder_threshold_text(role_id: str) -> str:
    thresholds = stakeholder_map()[role_id].negotiation.minimum_thresholds
    if not thresholds:
        return "No hidden minimum thresholds recorded."
    return "; ".join(f"{SECTION_LABELS.get(dim, dim)}: {text}" for dim, text in thresholds.items())


def _dimension_is_concrete(dimension_id: str, text: str) -> bool:
    normalized = text.lower()
    words = [word for word in re.findall(r"[a-zA-Z0-9$%-]+", normalized) if word]
    has_number = bool(re.search(r"\b\d+\b|\$\s*\d+|%|days?|months?|years?", normalized))
    if dimension_id == "financing":
        return has_number and any(term in normalized for term in ["fund", "budget", "million", "allocate", "pay", "cost"])
    if dimension_id == "community_health_protections":
        return any(term in normalized for term in ["clinic", "health", "monitor", "compensation", "water", "leachate"])
    if dimension_id == "livelihoods":
        return any(term in normalized for term in ["worker", "income", "transition", "job", "recycl", "support"])
    if dimension_id == "monitoring_and_enforcement":
        return any(term in normalized for term in ["monitor", "report", "penalt", "audit", "oversight", "public"])
    return len(words) >= 10


def _synthesize_dimension_proposal(dimension_id: str) -> str:
    current = st.session_state.proposal_form.get(dimension_id, "").strip()
    discussion = _dimension_discussion_text(dimension_id)
    prompt = (
        "You are a neutral moderator summarizing one negotiated proposal dimension.\n"
        f"Dimension: {SECTION_LABELS[dimension_id]}\n"
        f"Current draft text: {current or '[blank]'}\n"
        f"Focused discussion:\n{discussion}\n\n"
        "Write a concise final proposal text for this one dimension only.\n"
        "Rules:\n"
        "- Use only what was actually agreed, proposed, or conditionally accepted in the discussion.\n"
        "- Keep concrete numbers, actors, deadlines, and enforcement details when they exist.\n"
        "- If the discussion stayed vague or unrealistic, say that the dimension remains weak or incomplete instead of inventing certainty.\n"
        "- Return 1-3 sentences maximum.\n"
    )
    try:
        text = _call_agent(game().moderator_role or "national_government", prompt).strip()
    except Exception:
        text = current
    return text or current


def _dimension_options(role_id: str, dimension_id: str) -> Dict[str, List[str]]:
    generic = {
        "financing": {
            "propose": [
                "Create a national emergency fund with a named first-year amount.",
                "Split costs between national government, municipality, and operator by milestone.",
                "Ring-fence funding shares for health protections and worker transition."
            ],
            "amend": [
                "Add exact amounts for clinics, leachate control, and worker support.",
                "Release money in tranches tied to public reporting deadlines.",
                "Shift more short-term cost to the actor with the fastest available funds."
            ],
            "block": [
                "No named funding source is attached to this promise.",
                "The budget ignores health and livelihood costs.",
                "The municipality is being asked to carry money it does not have."
            ],
        },
        "community_health_protections": {
            "propose": [
                "Fund independent health screening and mobile clinics immediately.",
                "Create compensation and safe-water support for affected households.",
                "Commit to leachate control, public test results, and emergency mitigation."
            ],
            "amend": [
                "Add a fixed start date and named implementing body.",
                "Require third-party medical and environmental monitoring.",
                "Tie compensation to verified harm and public reporting."
            ],
            "block": [
                "This treats money as a substitute for protection.",
                "Monitoring is controlled by the same actors people do not trust.",
                "The proposal does not create visible action in the first month."
            ],
        },
        "livelihoods": {
            "propose": [
                "Guarantee a transition income package and formal inclusion pathway for informal workers.",
                "Reserve material access or contracted sorting roles for existing workers.",
                "Create a worker registry, training fund, and grievance mechanism."
            ],
            "amend": [
                "State exactly who qualifies and how long income support lasts.",
                "Ban exclusive recyclables control unless workers are explicitly protected.",
                "Add worker representation to implementation decisions."
            ],
            "block": [
                "This uses vague language instead of real livelihood protections.",
                "The proposal lets modernization erase existing workers.",
                "No one has explained what happens to recyclables access."
            ],
        },
        "monitoring_and_enforcement": {
            "propose": [
                "Create an independent oversight committee with public monthly reporting.",
                "Require named penalties if deadlines or protections fail.",
                "Give communities and civil society a formal escalation channel."
            ],
            "amend": [
                "Add third-party data publication and site access rights.",
                "Specify reporting frequency, responsible body, and sanctions.",
                "Require community and worker seats in the monitoring structure."
            ],
            "block": [
                "The same actors cannot mark their own homework.",
                "There is no consequence for broken promises here.",
                "The proposal says oversight exists but does not define how."
            ],
        },
    }
    options = generic[dimension_id]
    if role_id == "community_member" and dimension_id == "community_health_protections":
        options["propose"][0] = "Set up independent health monitoring, compensation, and a public harm registry for Eastfield households."
    if role_id == "informal_sector_worker" and dimension_id == "livelihoods":
        options["propose"][0] = "Guarantee income continuity and reserved roles for current informal workers before any new operator takes over."
    if role_id == "municipal_government" and dimension_id == "financing":
        options["block"][2] = "The city cannot accept another unfunded mandate."
    if role_id == "private_sector_company" and dimension_id == "financing":
        options["propose"][2] = "Use private capital for infrastructure but protect public-interest spending with a separate guaranteed fund."
    return options


def _proposal_prompt(role_id: str, dimension_id: str, move_kind: str, player_text: str) -> str:
    stakeholder = stakeholder_map()[role_id]
    current = st.session_state.proposal_form.get(dimension_id, "").strip() or "[blank]"
    return (
        f"You are {stakeholder.display_name}. Respond to the player's move on {SECTION_LABELS[dimension_id]}.\n"
        f"Player move type: {MOVE_LABELS[move_kind]}\n"
        f"Player move text: {player_text}\n"
        f"Current proposal text for this dimension: {current}\n"
        f"Your goal: {stakeholder.public_profile.primary_goal}\n"
        f"Your minimum requirements: {'; '.join(stakeholder.negotiation.minimum_requirements)}\n"
        f"Your hidden minimum thresholds for judged success: {_stakeholder_threshold_text(role_id)}\n"
        f"Your red lines: {'; '.join(stakeholder.negotiation.red_lines)}\n"
        "Rules:\n"
        "- Answer the player's move directly in your first sentence.\n"
        "- Stay on this one dimension only.\n"
        "- Give 1-2 sentences maximum.\n"
        "- If relevant, name one concrete concern, threshold, or condition.\n"
        "- Do not summarize the whole meeting.\n"
    )


def _select_reactor(dimension_id: str) -> str:
    """The single AI stakeholder with the biggest stake in this dimension.

    Deterministic on purpose: the same stakeholder carries the entire
    back-and-forth for one dimension, and only changes when the dimension
    changes (a new topic has a different most-affected stakeholder).
    """
    for role_id in REACTION_PRIORITY[dimension_id]:
        if role_id != human_role():
            return role_id
    for role_id in ai_roles():
        return role_id
    return human_role()


def _generate_round1_ai_statement(role_id: str) -> str:
    stakeholder = stakeholder_map()[role_id]
    prompt = (
        f"You are {stakeholder.display_name} in Round 1 of the City X waste crisis negotiation.\n"
        f"Your role: {stakeholder.public_profile.title}\n"
        f"Your primary goal: {stakeholder.public_profile.primary_goal}\n"
        f"Opening position: {stakeholder.public_profile.opening_position}\n"
        f"Hidden goal: {stakeholder.public_profile.hidden_goal}\n"
        f"Recent statements:\n{_recent_transcript(6)}\n\n"
        "Answer these two questions in 2-3 short sentences total:\n"
        "1. What is your opening position on the crisis in City X?\n"
        "2. Who do you believe is responsible and what outcome do you want?\n"
    )
    try:
        text = _call_agent(role_id, prompt)
    except Exception:
        text = ""
    if not text.strip():
        sk = stakeholder_map()[role_id]
        text = (
            f"{sk.public_profile.opening_position} "
            f"My priority is {sk.public_profile.primary_goal}"
        ).strip()
    return text


def _generate_round2_bid(role_id: str, chosen_dimension: str, reason: str) -> str:
    stakeholder = stakeholder_map()[role_id]
    prompt = (
        f"You are {stakeholder.display_name}. The human player said their top priority is {SECTION_LABELS[chosen_dimension]} because: {reason}\n"
        f"Your goal: {stakeholder.public_profile.primary_goal}\n"
        "State your own priority bid in exactly one sentence. "
        "Name one proposal dimension and what you most need in it."
    )
    text = _call_agent(role_id, prompt)
    if text.strip():
        return text

    fallback_dimension = {
        "national_government": "financing",
        "municipal_government": "timeline",
        "private_sector_company": "financing",
        "ngo_civil_society": "monitoring_and_enforcement",
        "community_member": "community_health_protections",
        "informal_sector_worker": "livelihoods",
    }.get(role_id, "financing")
    fallback_need = {
        "financing": "a named funding source with exact allocations",
        "timeline": "a realistic first 30-day action schedule",
        "community_health_protections": "independent health protections that start immediately",
        "livelihoods": "explicit livelihood guarantees for affected workers",
        "monitoring_and_enforcement": "independent oversight with public reporting and penalties",
    }[fallback_dimension]
    return f"My priority is {SECTION_LABELS[fallback_dimension]} because I need {fallback_need}."


def _generate_ai_reaction(dimension_id: str, move_kind: str, player_text: str) -> Tuple[str, str]:
    reactor = _select_reactor(dimension_id)
    try:
        text = _call_agent(reactor, _proposal_prompt(reactor, dimension_id, move_kind, player_text))
    except Exception:
        text = ""
    if not text.strip():
        # The model produced nothing usable; retry once with a short, direct
        # prompt before resorting to the scripted fallback.
        sk = stakeholder_map()[reactor]
        retry = (
            f"You are {sk.display_name}. In ONE or TWO sentences, react to this "
            f"move on {SECTION_LABELS[dimension_id]}: \"{player_text}\". "
            f"Your goal: {sk.public_profile.primary_goal}. "
            "Be specific and stay in character. Do not output any tags."
        )
        try:
            text = _call_agent(reactor, retry)
        except Exception:
            text = ""
    if not text.strip():
        text = _stakeholder_fallback(reactor, dimension_id, player_text)
    st.session_state.reaction_counts[reactor] = st.session_state.reaction_counts.get(reactor, 0) + 1
    return reactor, text


def _advance_round2_dimension() -> None:
    dimension_id = _current_round2_dimension()
    if dimension_id:
        summary_text = _synthesize_dimension_proposal(dimension_id).strip()
        if summary_text:
            st.session_state.proposal_form[dimension_id] = summary_text
        st.session_state.round2_dimension_status[dimension_id] = (
            "yellow" if not _dimension_is_concrete(dimension_id, st.session_state.proposal_form.get(dimension_id, "")) else "neutral"
        )
        _sync_proposal_to_game()
    st.session_state.round2_pending_reaction = {}
    st.session_state.round2_followup_done = False
    st.session_state.round2_dimension_index += 1
    if st.session_state.round2_dimension_index >= len(NEGOTIABLE_DIMENSIONS):
        st.session_state.stage = "round2_flagging"


def _flag_prompt(role_id: str, dimensions: List[str]) -> str:
    stakeholder = stakeholder_map()[role_id]
    dims = "\n".join(
        f"- {dim}: {st.session_state.proposal_form.get(dim, '').strip() or '[blank]'}"
        for dim in dimensions
    )
    return (
        f"You are {stakeholder.display_name}. Review the proposal card.\n"
        f"Goal: {stakeholder.public_profile.primary_goal}\n"
        f"Minimum requirements: {'; '.join(stakeholder.negotiation.minimum_requirements)}\n"
        f"Hidden minimum thresholds: {_stakeholder_threshold_text(role_id)}\n"
        f"Red lines: {'; '.join(stakeholder.negotiation.red_lines)}\n\n"
        f"Dimensions:\n{dims}\n\n"
        "Return strict JSON. Each key must be one dimension id. "
        "Each value must be an object with 'flag' and 'reason'.\n"
        "Allowed flags: accept, accept_with_condition, reject.\n"
        "Reject or condition any section that is vague, unrealistic, unsupported "
        "by the actual discussion, or missing concrete actors / money / timelines.\n"
        "The 'reason' MUST be specific: name exactly what is missing or unacceptable "
        "and, for accept_with_condition, state the precise condition that would make "
        "it acceptable (e.g. 'add a named fund and a 30-day start date'). "
        "Never answer 'needs more clarity' without saying clarity on what.\n"
        "Example: {\"financing\": {\"flag\": \"accept_with_condition\", "
        "\"reason\": \"No funding source is named; condition: commit a national "
        "fund with a first-year amount and quarterly public reporting\"}}\n"
    )


def _safe_parse_json(raw: str) -> dict:
    text = raw.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return {}
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return {}


def _generate_ai_flags(dimensions: List[str]) -> Dict[str, Dict[str, str]]:
    results: Dict[str, Dict[str, str]] = {}
    for role_id in ai_roles():
        try:
            parsed = _safe_parse_json(_call_agent(role_id, _flag_prompt(role_id, dimensions)))
        except Exception:
            parsed = {}
        role_flags: Dict[str, Dict[str, str]] = {}
        for dim in dimensions:
            item = parsed.get(dim, {}) if isinstance(parsed, dict) else {}
            flag = item.get("flag", "accept_with_condition")
            if flag not in FLAG_LABELS:
                flag = "accept_with_condition"
            reason = (item.get("reason") or "").strip()
            if not reason or reason.lower().rstrip(".") in ("needs more clarity", "more clarity"):
                # Specific, in-character fallback instead of a generic phrase.
                reason = _stakeholder_fallback(role_id, dim)
            role_flags[dim] = {"flag": flag, "reason": reason}
        results[role_id] = role_flags
    return results


def _classify_dimension(dim: str, flags: Dict[str, Dict[str, Dict[str, str]]]) -> str:
    values = [role_flags[dim]["flag"] for role_flags in flags.values()]
    if dim in st.session_state.round2_force_revisit and "reject" not in values:
        return "yellow"
    if any(flag == "reject" for flag in values):
        return "red"
    if any(flag == "accept_with_condition" for flag in values):
        return "yellow"
    return "green"


def _flag_reason_summary(dim: str, flags: Dict[str, Dict[str, Dict[str, str]]]) -> str:
    rejects = []
    conditions = []
    for role_id, role_flags in flags.items():
        flag = role_flags[dim]["flag"]
        reason = role_flags[dim]["reason"]
        label = stakeholder_map()[role_id].display_name
        if flag == "reject":
            rejects.append(f"{label}: {reason}")
        elif flag == "accept_with_condition":
            conditions.append(f"{label}: {reason}")
    if rejects:
        return "Main objections: " + " | ".join(rejects[:2])
    if conditions:
        return "Remaining conditions: " + " | ".join(conditions[:2])
    return "No major objections remain."


def _final_vote_prompt(role_id: str) -> str:
    stakeholder = stakeholder_map()[role_id]
    proposal = "\n".join(
        f"- {SECTION_LABELS[dim['id']]}: {st.session_state.proposal_form.get(dim['id'], '').strip()}"
        for dim in game().scenario.proposal_dimensions
    )
    return (
        f"You are {stakeholder.display_name}. Cast your final vote on the City X proposal.\n"
        f"Goal: {stakeholder.public_profile.primary_goal}\n"
        f"Minimum requirements: {'; '.join(stakeholder.negotiation.minimum_requirements)}\n"
        f"Hidden minimum thresholds: {_stakeholder_threshold_text(role_id)}\n"
        f"Red lines: {'; '.join(stakeholder.negotiation.red_lines)}\n"
        f"Final proposal:\n{proposal}\n\n"
        "Return strict JSON with keys 'vote' and 'reason'.\n"
        "Allowed vote values: unconditional_endorsement, conditional_endorsement, abstention, rejection.\n"
        "If your vote is anything other than unconditional_endorsement, the "
        "'reason' MUST name the specific unmet requirement, condition, or red "
        "line that stopped you from fully endorsing (cite the proposal section). "
        "A vague reason is not acceptable.\n"
    )


def _generate_ai_final_votes() -> Dict[str, Dict[str, str]]:
    votes = {}
    for role_id in ai_roles():
        try:
            parsed = _safe_parse_json(_call_agent(role_id, _final_vote_prompt(role_id)))
        except Exception:
            parsed = {}
        vote = parsed.get("vote", "conditional_endorsement")
        if vote not in FINAL_VOTE_LABELS:
            vote = "conditional_endorsement"
        reason = (parsed.get("reason") or "").strip()
        generic = reason.lower().rstrip(".") in (
            "", "no reason provided", "needs more clarity", "more clarity",
        )
        # Anything short of an unconditional endorsement must carry a concrete,
        # in-character reason — never a placeholder.
        if vote != "unconditional_endorsement" and generic:
            reason = _stakeholder_fallback(role_id, NEGOTIABLE_DIMENSIONS[0])
        elif not reason:
            reason = "The proposal meets my key requirements."
        votes[role_id] = {"vote": vote, "reason": reason}
    return votes


def _evaluate_goal_achievement() -> Dict[str, Dict[str, str]]:
    proposal = "\n".join(
        f"- {SECTION_LABELS[dim]}: {st.session_state.proposal_form.get(dim, '').strip() or '[blank]'}"
        for dim in NEGOTIABLE_DIMENSIONS
    )
    role_evaluations: Dict[str, Dict[str, str]] = {}
    moderator_role = game().moderator_role or "national_government"
    for role_id in ROUND1_ORDER:
        stakeholder = stakeholder_map()[role_id]
        prompt = (
            "You are a neutral AI moderator evaluating one stakeholder's outcome against hidden thresholds.\n"
            f"Stakeholder: {stakeholder.display_name}\n"
            f"Primary goal: {stakeholder.public_profile.primary_goal}\n"
            f"Hidden minimum thresholds: {_stakeholder_threshold_text(role_id)}\n"
            f"Negotiated proposal dimensions only:\n{proposal}\n\n"
            "Return strict JSON with keys 'rating' and 'explanation'.\n"
            "Allowed rating values: fully_achieved, partially_achieved, not_achieved.\n"
            "The explanation must be one sentence and must mention at least one concrete part of the proposal or one missing threshold.\n"
        )
        try:
            parsed = _safe_parse_json(_call_agent(moderator_role, prompt))
        except Exception:
            parsed = {}
        rating = parsed.get("rating", "partially_achieved")
        if rating not in {"fully_achieved", "partially_achieved", "not_achieved"}:
            rating = "partially_achieved"
        explanation = parsed.get("explanation", "The final proposal only partially matches the hidden thresholds.")
        role_evaluations[role_id] = {"rating": rating, "explanation": explanation}
    return role_evaluations


def _map_to_engine_vote(label: str) -> str:
    return "yes" if label in {"unconditional_endorsement", "conditional_endorsement"} else "no"


def init_game(model: str, role_id: str, think: bool) -> None:
    session = load_and_prepare_roleplay_session(
        default_city_x_scenario_path(),
        rules_path=default_city_x_game_rules_path(),
        human_roles=[role_id],
        model=model or None,
        think=think,
    )
    runtime = create_roleplay_runtime(session)
    st.session_state.runtime = runtime
    st.session_state.stage = "role_reveal"
    st.session_state.notice = _moderator_text("opening")
    st.session_state.proposal_form = dict(PREFILLED_DIMENSIONS)
    st.session_state.round1_spoken = set()
    st.session_state.round1_summary = ""
    st.session_state.round2_human_bid = None
    st.session_state.round2_ai_bids = {}
    st.session_state.round2_dimension_index = 0
    st.session_state.round2_addressed = set()
    st.session_state.round2_event_fired = False
    st.session_state.round2_force_revisit = []
    st.session_state.round2_discussions = {}
    st.session_state.reaction_counts = {}
    st.session_state.round2_flags = {}
    st.session_state.round2_dimension_status = {dim: "neutral" for dim in PREFILLED_DIMENSIONS}
    st.session_state.round2_pending_reaction = {}
    st.session_state.round2_followup_done = False
    st.session_state.round3_pending_reaction = {}
    st.session_state.round3_followup_done = False
    st.session_state.round3_dimensions = []
    st.session_state.round3_index = 0
    st.session_state.final_vote_labels = {}
    st.session_state.goal_evaluations = {}
    _sync_proposal_to_game()


def render_transcript() -> None:
    turns = game().dialog.turns
    if not turns:
        st.info("No statements yet.")
        return
    for turn in turns[-18:]:
        role_id = next(
            (sid for sid, stakeholder in stakeholder_map().items() if stakeholder.display_name == turn.speaker),
            "",
        )
        st.markdown(
            components.transcript_bubble(
                role_id, turn.speaker, turn.text, is_human=(role_id == human_role())
            ),
            unsafe_allow_html=True,
        )


def render_moderator_notice() -> None:
    if st.session_state.notice:
        st.markdown(
            components.transcript_bubble("", "Moderator", st.session_state.notice, is_moderator=True),
            unsafe_allow_html=True,
        )
        st.session_state.notice = ""


def render_proposal_card(compact: bool = False) -> None:
    statuses = st.session_state.round2_dimension_status
    for dim in game().scenario.proposal_dimensions:
        dim_id = dim["id"]
        value = st.session_state.proposal_form.get(dim_id, "").strip() or "[blank]"
        status = statuses.get(dim_id, "neutral")
        cls = {
            "green": "proposal-green",
            "yellow": "proposal-yellow",
            "red": "proposal-red",
            "neutral": "proposal-neutral",
        }.get(status, "proposal-neutral")
        st.markdown(
            f'<div class="proposal-box {cls}"><b>{dim["label"]}</b><br>{value}</div>',
            unsafe_allow_html=True,
        )
        if not compact and dim_id in st.session_state.round2_flags:
            st.caption(st.session_state.round2_flags[dim_id]["summary"])


def render_sidebar() -> None:
    s = stakeholder_map()[human_role()]
    c = cfg(human_role())
    st.sidebar.markdown(f"### {c['emoji']} {s.display_name}")
    st.sidebar.caption(s.public_profile.title)
    st.sidebar.markdown(f"**Goal:** {s.public_profile.primary_goal}")
    if s.public_profile.hidden_goal:
        st.sidebar.markdown(f"**Hidden goal:** {s.public_profile.hidden_goal}")
    if s.negotiation.red_lines:
        st.sidebar.markdown("**Red lines**")
        for item in s.negotiation.red_lines:
            st.sidebar.markdown(f"- {item}")
    if s.private_info:
        st.sidebar.markdown("**Private information**")
        for item in s.private_info:
            st.sidebar.markdown(f"- {item}")


def render_setup() -> None:
    st.markdown(components.setup_hero("assets/swm-logo.svg"), unsafe_allow_html=True)
    sc = scenario()
    st.info(sc.summary)
    cols = st.columns(3)
    for index, stakeholder in enumerate(sc.stakeholders):
        c = cfg(stakeholder.id)
        with cols[index % 3]:
            st.markdown(
                f"<div class='proposal-box' style='background:{c['bg']};border-left:6px solid {c['color']};'>"
                f"<b>{c['emoji']} {stakeholder.display_name}</b><br>"
                f"<small>{stakeholder.public_profile.primary_goal}</small></div>",
                unsafe_allow_html=True,
            )
    with st.form("setup_form"):
        role_id = st.selectbox(
            "Choose your stakeholder role",
            options=[stakeholder.id for stakeholder in sc.stakeholders],
            format_func=lambda rid: f"{cfg(rid)['emoji']} {sc.stakeholder_map()[rid].display_name}",
        )
        model = st.text_input("AI model", value=default_model_value())
        st.caption(
            "Examples: `vertexai:gemini-2.5-flash` for billed Google Cloud Vertex AI, "
            "`google:gemini-2.5-flash` for Gemini API, or "
            "`ollama:qwen2.5:latest` for a local Ollama server."
        )
        think = st.checkbox("Enable extended thinking", value=False)
        submit = st.form_submit_button(
            "Start the negotiation", type="primary", use_container_width=True
        )
    if submit:
        with st.spinner("Preparing the negotiation room and briefing the AI stakeholders…"):
            init_game(model, role_id, think)
        st.rerun()


def render_role_reveal() -> None:
    stakeholder = stakeholder_map()[human_role()]
    c = cfg(human_role())
    st.markdown(
        f"<div class='round-hdr'><h3>Phase 0: Setup</h3><p>Read your role card before you enter the room.</p></div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='proposal-box' style='background:{c['bg']};border-left:6px solid {c['color']};'>"
        f"<h3>{c['emoji']} {stakeholder.display_name}</h3>"
        f"<p><b>{stakeholder.public_profile.title}</b></p>"
        f"<p>{stakeholder.public_profile.background}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"**Primary goal:** {stakeholder.public_profile.primary_goal}")
    if stakeholder.public_profile.hidden_goal:
        st.markdown(f"**Hidden goal:** {stakeholder.public_profile.hidden_goal}")
    if stakeholder.negotiation.red_lines:
        st.markdown("**Red lines**")
        for item in stakeholder.negotiation.red_lines:
            st.markdown(f"- {item}")
    if stakeholder.private_info:
        st.markdown("**Private information**")
        for item in stakeholder.private_info:
            st.markdown(f"- {item}")
    render_moderator_notice()
    if st.button("Enter the meeting room", type="primary", use_container_width=True):
        st.session_state.stage = "round1"
        st.rerun()


def _next_round1_speaker() -> str:
    for role_id in ROUND1_ORDER:
        if role_id not in st.session_state.round1_spoken:
            return role_id
    return ""


def _finish_round1() -> None:
    if not st.session_state.round1_summary:
        st.session_state.round1_summary = _moderator_text(
            "round1_summary",
            "Summarize the main tensions and likely coalition lines after the opening positions.",
        )
    st.subheader("Moderator summary")
    st.markdown(
        f"<div class='proposal-box proposal-neutral'><b>Moderator summary</b><br>{st.session_state.round1_summary}</div>",
        unsafe_allow_html=True,
    )
    if st.button("Enter Round 2: Proposal Building", type="primary", use_container_width=True):
        advance_round(game())
        st.session_state.stage = "round2_bids"
        st.rerun()


def render_round1() -> None:
    st.markdown(
        "<div class='round-hdr'><h3>Round 1: Opening Positions</h3>"
        "<p>Each stakeholder states their position, who they hold responsible, and what outcome they want.</p></div>",
        unsafe_allow_html=True,
    )
    render_moderator_notice()
    render_transcript()

    current = _next_round1_speaker()
    if not current:
        _finish_round1()
        return

    if current != human_role():
        speaker = stakeholder_map()[current]
        placeholder = st.empty()
        placeholder.markdown(
            components.transcript_bubble(current, speaker.display_name, "", typing=True),
            unsafe_allow_html=True,
        )
        text = _generate_round1_ai_statement(current)
        _append_turn(speaker.display_name, text)
        st.session_state.round1_spoken.add(current)
        placeholder.empty()
        st.rerun()
        return

    stakeholder = stakeholder_map()[current]
    st.info(f"It is your turn as {stakeholder.display_name}.")
    with st.form("round1_form", clear_on_submit=True):
        answer_one = st.text_area(
            "What is your opening position on the crisis in City X?",
            height=100,
        )
        answer_two = st.text_area(
            "Who do you believe is responsible and what outcome do you want?",
            height=100,
        )
        submitted = st.form_submit_button("Submit opening position", type="primary")
    if submitted and answer_one.strip() and answer_two.strip():
        text = f"{answer_one.strip()} {answer_two.strip()}"
        _append_turn(stakeholder.display_name, text, human=True)
        st.session_state.round1_spoken.add(current)
        st.rerun()


def render_round2_bids() -> None:
    st.markdown(
        "<div class='round-hdr'><h3>Round 2: Opening Bids</h3>"
        "<p>Choose the dimension that matters most to your role. The moderator will collect all priority bids before the proposal table opens.</p></div>",
        unsafe_allow_html=True,
    )
    render_moderator_notice()
    if _drain_pending():
        return

    if st.session_state.round2_human_bid is None:
        with st.form("round2_bid_form", clear_on_submit=True):
            dimension = st.radio(
                "Which dimension matters most to your character and why?",
                NEGOTIABLE_DIMENSIONS,
                format_func=lambda dim: SECTION_LABELS[dim],
            )
            reason = st.text_area("Short reason (optional)", height=90)
            submitted = st.form_submit_button("Collect all bids", type="primary", use_container_width=True)
        if submitted:
            reason_txt = reason.strip()
            bid_text = (
                f"My priority is {SECTION_LABELS[dimension]} because {reason_txt}"
                if reason_txt
                else f"My priority is {SECTION_LABELS[dimension]}."
            )
            _defer("Collecting priority bids from the other stakeholders…",
                   _do_collect_bids, dimension, reason_txt, bid_text)
        return

    st.subheader("Collected priority bids")
    st.markdown(f"- **You:** {st.session_state.round2_human_bid['text']}")
    for role_id in ROUND1_ORDER:
        if role_id == human_role():
            continue
        st.markdown(f"- **{stakeholder_map()[role_id].display_name}:** {st.session_state.round2_ai_bids.get(role_id, '')}")
    if st.button("Open the proposal table", type="primary", use_container_width=True):
        st.session_state.stage = "round2_table"
        st.session_state.notice = (
            "The proposal card opens with Core action and Timeline pre-filled. "
            "The room will now negotiate the remaining four dimensions one by one."
        )
        st.rerun()


def _current_round2_dimension() -> str:
    if st.session_state.round2_dimension_index >= len(NEGOTIABLE_DIMENSIONS):
        return ""
    return NEGOTIABLE_DIMENSIONS[st.session_state.round2_dimension_index]


def _submit_dimension_move(dimension_id: str, text: str) -> None:
    speaker = stakeholder_map()[human_role()]
    move_kind = "propose"
    final_text = f"{MOVE_LABELS[move_kind]} on {SECTION_LABELS[dimension_id]}: {text}"
    _append_turn(speaker.display_name, final_text, human=True)
    _record_dimension_discussion(dimension_id, speaker.display_name, final_text)
    st.session_state.proposal_form[dimension_id] = text.strip()
    st.session_state.round2_addressed.add(dimension_id)
    _sync_proposal_to_game()
    reactor, reaction = _generate_ai_reaction(dimension_id, move_kind, text)
    _append_turn(stakeholder_map()[reactor].display_name, reaction)
    _record_dimension_discussion(dimension_id, stakeholder_map()[reactor].display_name, reaction)
    st.session_state.round2_pending_reaction = {
        "dimension_id": dimension_id,
        "reactor": reactor,
        "reaction": reaction,
    }
    st.session_state.round2_followup_done = False

    if dimension_id == "livelihoods" and not st.session_state.round2_event_fired:
        event_text = game().scenario.events[0]["announcement"]
        st.session_state.round2_event_fired = True
        if "financing" not in st.session_state.round2_force_revisit:
            st.session_state.round2_force_revisit.append("financing")
        if "monitoring_and_enforcement" not in st.session_state.round2_force_revisit:
            st.session_state.round2_force_revisit.append("monitoring_and_enforcement")
        st.session_state.notice = _moderator_text("event", event_text)

    st.rerun()


def _submit_dimension_reply(dimension_id: str, text: str) -> None:
    """One reply in the ongoing back-and-forth; the same stakeholder answers."""
    speaker = stakeholder_map()[human_role()]
    followup_text = f"Follow-up on {SECTION_LABELS[dimension_id]}: {text}"
    _append_turn(speaker.display_name, followup_text, human=True)
    _record_dimension_discussion(dimension_id, speaker.display_name, followup_text)
    reactor, reaction = _generate_ai_reaction(dimension_id, "amend", text)
    _append_turn(stakeholder_map()[reactor].display_name, reaction)
    _record_dimension_discussion(dimension_id, stakeholder_map()[reactor].display_name, reaction)
    st.rerun()


def _render_dimension_thread(dimension_id: str) -> None:
    """Render the focused back-and-forth for one dimension as chat bubbles."""
    thread = st.session_state.round2_discussions.get(dimension_id, [])
    if not thread:
        return
    st.markdown("**Discussion on this dimension**")
    for line in thread[-8:]:
        speaker, _, body = line.partition(": ")
        role_id = next(
            (sid for sid, sk in stakeholder_map().items() if sk.display_name == speaker),
            "",
        )
        st.markdown(
            components.transcript_bubble(
                role_id, speaker, body, is_human=(role_id == human_role())
            ),
            unsafe_allow_html=True,
        )


def render_round2_table() -> None:
    dimension_id = _current_round2_dimension()
    if not dimension_id:
        st.session_state.stage = "round2_flagging"
        st.rerun()
        return

    idx = st.session_state.round2_dimension_index + 1
    total = len(NEGOTIABLE_DIMENSIONS)
    primary = _select_reactor(dimension_id)
    pc = cfg(primary)
    pname = stakeholder_map()[primary].display_name
    label = SECTION_LABELS[dimension_id]

    st.markdown(
        f"<div class='round-hdr'><h3>Round 2 · Build the Blueprint &nbsp;"
        f"<span style='opacity:.85;font-size:.8em'>({idx} of {total})</span></h3>"
        "<p>Negotiate one dimension at a time. Make a proposal, go back and "
        "forth with the stakeholder who cares most about it, then click "
        "<b>Move to next dimension</b> when you're satisfied.</p></div>",
        unsafe_allow_html=True,
    )
    render_moderator_notice()
    if _drain_pending():
        return

    st.subheader(f"Now negotiating: {label}")
    st.markdown(
        f"<div class='proposal-box' style='border-left:6px solid {pc['color']};'>"
        f"<b>{pc['emoji']} {pname}</b> has the biggest stake in <b>{label}</b> "
        "and is the one responding to you on this dimension.</div>",
        unsafe_allow_html=True,
    )

    with st.expander("Draft proposal so far", expanded=False):
        render_proposal_card(compact=True)

    _render_dimension_thread(dimension_id)

    proposed = dimension_id in st.session_state.round2_addressed

    if not proposed:
        st.info(f"✍️ Your move — make an opening proposal on **{label}**.")
        options = _dimension_options(human_role(), dimension_id)
        with st.form(f"dim_propose_{dimension_id}", clear_on_submit=True):
            preset = st.radio("Pick a ready-made option…", options["propose"])
            free_text = st.text_area("…or write your own instead", height=90)
            submitted = st.form_submit_button(
                f"Submit proposal on {label}", type="primary", use_container_width=True
            )
        if submitted:
            _defer(f"💬 {pname} is responding to your proposal…",
                   _submit_dimension_move, dimension_id, free_text.strip() or preset)
        return

    st.info(f"✍️ Reply to **{pname}** to keep negotiating, or move on when you're satisfied.")
    with st.form(f"dim_reply_{dimension_id}", clear_on_submit=True):
        reply_text = st.text_area(f"Your reply to {pname}", height=90)
        sent = st.form_submit_button(
            f"Send reply to {pname}", type="primary", use_container_width=True
        )
    if sent and reply_text.strip():
        _defer(f"💬 {pname} is responding…",
               _submit_dimension_reply, dimension_id, reply_text.strip())

    st.divider()
    if st.button(
        f"✅ Done with {label} — move to the next dimension", use_container_width=True
    ):
        _defer("Summarizing what was agreed on this dimension…", _advance_r2)


def render_round2_flagging() -> None:
    st.markdown(
        "<div class='round-hdr'><h3>Round 2: Flagging</h3>"
        "<p>Each stakeholder now flags every negotiated dimension as Accept, Accept with condition, or Reject. Green sections lock. Yellow and red reopen in Round 3.</p></div>",
        unsafe_allow_html=True,
    )
    render_moderator_notice()
    if _drain_pending():
        return
    render_proposal_card()

    dimensions = NEGOTIABLE_DIMENSIONS
    with st.form("flag_form"):
        human_flags = {}
        for dim in dimensions:
            human_flags[dim] = st.radio(
                SECTION_LABELS[dim],
                FLAG_LABELS,
                format_func=lambda flag: FLAG_DISPLAY[flag],
                horizontal=True,
                key=f"flag_{dim}",
            )
        submitted = st.form_submit_button("Lock the flags", type="primary", use_container_width=True)

    if submitted:
        _defer("Stakeholders are reviewing the proposal and flagging each section…",
               _do_lock_flags, dict(human_flags))


def render_round2_results() -> None:
    st.markdown(
        "<div class='round-hdr'><h3>Round 2: Flag Results</h3>"
        "<p>Each stakeholder's position on each negotiated dimension is shown here before the room reopens any contested sections.</p></div>",
        unsafe_allow_html=True,
    )
    status_label = {
        "green": ("Accepted — locked", "proposal-green"),
        "yellow": ("Conditional — reopens in Round 3", "proposal-yellow"),
        "red": ("Rejected — reopens in Round 3", "proposal-red"),
        "neutral": ("Pending", "proposal-neutral"),
    }
    for dim in NEGOTIABLE_DIMENSIONS:
        result = st.session_state.round2_flags.get(dim)
        if not result:
            continue
        status = result["status"]
        label, cls = status_label.get(status, status_label["neutral"])
        text = st.session_state.proposal_form.get(dim, "").strip() or "[blank]"
        # The dimension header color IS its aggregate vote outcome, so the
        # color always matches the votes shown directly below it.
        st.markdown(
            f'<div class="proposal-box {cls}">'
            f'<b>{SECTION_LABELS[dim]}</b> &nbsp;'
            f'<span class="badge">{label}</span><br>'
            f'<small>{text}</small></div>',
            unsafe_allow_html=True,
        )
        rows = [
            {
                "role_id": role_id,
                "name": stakeholder_map()[role_id].display_name,
                "vote": result["flags"][role_id]["flag"],
                "reason": result["flags"][role_id]["reason"],
            }
            for role_id in ROUND1_ORDER
            if role_id in result["flags"]
        ]
        st.markdown(components.vote_tally(rows), unsafe_allow_html=True)
        st.divider()

    contested = st.session_state.round3_dimensions
    if contested:
        if st.button("Reopen contested dimensions", type="primary", use_container_width=True):
            advance_round(game())
            st.session_state.round3_addressed = set()
            reasons = [f"{SECTION_LABELS[dim]}: {st.session_state.round2_flags[dim]['summary']}" for dim in contested]
            st.session_state.notice = _moderator_text(
                "round3_intro",
                "Only contested dimensions reopen.\n" + "\n".join(reasons),
            )
            st.session_state.stage = "round3"
            st.rerun()
    else:
        if st.button("Proceed to final vote", type="primary", use_container_width=True):
            advance_round(game())
            st.session_state.notice = "All negotiated dimensions were accepted. The room moves to the final endorsement vote."
            st.session_state.stage = "final_vote"
            st.rerun()


def _current_round3_dimension() -> str:
    dims = st.session_state.round3_dimensions
    if st.session_state.round3_index >= len(dims):
        return ""
    return dims[st.session_state.round3_index]


def _round3_objections(dimension_id: str) -> List[Tuple[str, str, str]]:
    """(role_id, name, reason) for every stakeholder who didn't fully accept."""
    flags = st.session_state.round2_flags.get(dimension_id, {}).get("flags", {})
    out = []
    for role_id in ROUND1_ORDER:
        rf = flags.get(role_id)
        if not rf or rf.get("flag") == "accept":
            continue
        out.append((role_id, stakeholder_map()[role_id].display_name,
                    (rf.get("reason") or "").strip()))
    return out


def _objection_amendments(dimension_id: str) -> List[str]:
    """Amendment presets tied directly to the actual main objections."""
    opts = []
    for _role, name, reason in _round3_objections(dimension_id):
        short = reason.rstrip(".")
        if len(short) > 110:
            short = short[:107] + "…"
        opts.append(f"Address {name}'s objection — {short}")
    if not opts:
        opts = _dimension_options(human_role(), dimension_id)["amend"]
    return opts[:5]


def _submit_round3_move(dimension_id: str, text: str) -> None:
    speaker = stakeholder_map()[human_role()]
    move_kind = "amend"
    final_text = f"Round 3 {MOVE_LABELS[move_kind]} on {SECTION_LABELS[dimension_id]}: {text}"
    _append_turn(speaker.display_name, final_text, human=True)
    _record_dimension_discussion(dimension_id, speaker.display_name, final_text)
    st.session_state.proposal_form[dimension_id] = text.strip()
    st.session_state.round3_addressed.add(dimension_id)
    _sync_proposal_to_game()
    reactor, reaction = _generate_ai_reaction(dimension_id, move_kind, text)
    _append_turn(stakeholder_map()[reactor].display_name, reaction)
    _record_dimension_discussion(dimension_id, stakeholder_map()[reactor].display_name, reaction)
    st.rerun()


def _advance_round3_dimension() -> None:
    dimension_id = _current_round3_dimension()
    if dimension_id:
        summary_text = _synthesize_dimension_proposal(dimension_id).strip()
        if summary_text:
            st.session_state.proposal_form[dimension_id] = summary_text
        st.session_state.round2_dimension_status[dimension_id] = (
            "yellow" if not _dimension_is_concrete(dimension_id, st.session_state.proposal_form.get(dimension_id, "")) else "green"
        )
        _sync_proposal_to_game()
    st.session_state.round3_pending_reaction = {}
    st.session_state.round3_followup_done = False
    st.session_state.round3_index += 1
    if st.session_state.round3_index >= len(st.session_state.round3_dimensions):
        st.session_state.stage = "final_vote"
        st.session_state.notice = "The moderator presents the consolidated final proposal and calls the final endorsement vote."


def render_round3() -> None:
    dimension_id = _current_round3_dimension()
    if not dimension_id:
        st.session_state.stage = "final_vote"
        st.rerun()
        return

    dims = st.session_state.round3_dimensions
    idx = (st.session_state.round3_index + 1)
    total = len(dims)
    primary = _select_reactor(dimension_id)
    pc = cfg(primary)
    pname = stakeholder_map()[primary].display_name
    label = SECTION_LABELS[dimension_id]
    status = st.session_state.round2_flags.get(dimension_id, {}).get("status", "yellow")
    box_cls = "proposal-red" if status == "red" else "proposal-yellow"

    st.markdown(
        f"<div class='round-hdr'><h3>Round 3 · Resolve Contested &nbsp;"
        f"<span style='opacity:.85;font-size:.8em'>({idx} of {total})</span></h3>"
        "<p>Only contested dimensions reopen. Amend to clear the objections "
        "below, go back and forth, then move on when they're satisfied.</p></div>",
        unsafe_allow_html=True,
    )
    render_moderator_notice()
    if _drain_pending():
        return

    st.subheader(f"Reopened: {label}")
    objections = _round3_objections(dimension_id)
    obj_html = "".join(
        f"<li><b>{cfg(rid)['emoji']} {nm}</b>: {rsn or 'objection on record'}</li>"
        for rid, nm, rsn in objections
    ) or "<li>General concerns remain on this dimension.</li>"
    st.markdown(
        f'<div class="proposal-box {box_cls}"><b>Main objections to resolve</b>'
        f'<ul style="margin:6px 0 0;padding-left:18px;">{obj_html}</ul></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='proposal-box' style='border-left:6px solid {pc['color']};'>"
        f"<b>{pc['emoji']} {pname}</b> has the biggest stake in <b>{label}</b> "
        "and is responding to you here.</div>",
        unsafe_allow_html=True,
    )

    with st.expander("Draft proposal so far", expanded=False):
        render_proposal_card(compact=True)

    _render_dimension_thread(dimension_id)

    if dimension_id not in st.session_state.round3_addressed:
        st.info(f"✍️ Propose an amendment that resolves the objections on **{label}**.")
        with st.form(f"r3_propose_{dimension_id}", clear_on_submit=True):
            preset = st.radio(
                "Pick an amendment (each one targets a real objection)…",
                _objection_amendments(dimension_id),
            )
            free_text = st.text_area("…or write your own amendment", height=90)
            submitted = st.form_submit_button(
                f"Submit amendment on {label}", type="primary", use_container_width=True
            )
        if submitted:
            _defer(f"💬 {pname} is responding to your amendment…",
                   _submit_round3_move, dimension_id, free_text.strip() or preset)
        return

    st.info(f"✍️ Reply to **{pname}**, or move on when the objections are addressed.")
    with st.form(f"r3_reply_{dimension_id}", clear_on_submit=True):
        reply_text = st.text_area(f"Your reply to {pname}", height=90)
        sent = st.form_submit_button(
            f"Send reply to {pname}", type="primary", use_container_width=True
        )
    if sent and reply_text.strip():
        _defer(f"💬 {pname} is responding…",
               _submit_dimension_reply, dimension_id, reply_text.strip())

    st.divider()
    if st.button(
        f"✅ Done with {label} — move to the next reopened dimension",
        use_container_width=True,
    ):
        _defer("Summarizing what was agreed on this dimension…", _advance_r3)


def render_final_vote() -> None:
    st.markdown(
        "<div class='round-hdr'><h3>Final Vote</h3>"
        "<p>Stakeholders now cast their final endorsement vote on the full six-part proposal.</p></div>",
        unsafe_allow_html=True,
    )
    render_moderator_notice()
    if _drain_pending():
        return

    total = len(game().scenario.stakeholders)
    st.markdown(
        '<div class="proposal-box proposal-neutral">'
        "<b>How the proposal passes</b><br>"
        f"All {total} stakeholders cast one final vote. An "
        "<b>endorsement</b> is an <i>unconditional</i> or <i>conditional</i> "
        "endorsement (abstention and rejection do not count).<br>"
        "&nbsp;•&nbsp; <b>4 or more</b> endorsements → the proposal <b>passes</b><br>"
        "&nbsp;•&nbsp; exactly <b>3</b> → <b>partial</b> agreement<br>"
        "&nbsp;•&nbsp; <b>2 or fewer</b> → the proposal <b>fails</b>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="proposal-box proposal-neutral">'
        "<b>What the section colors mean</b> (set by the Round 2/3 flag votes):"
        "<br>🟩 <b>Accepted</b> — locked &nbsp;|&nbsp; 🟨 <b>Conditional</b> — "
        "accepted with conditions &nbsp;|&nbsp; 🟥 <b>Contested</b> — a "
        "stakeholder rejected it &nbsp;|&nbsp; ⬜ <b>Pre-set</b> — fixed "
        "core action / timeline, not negotiated"
        "</div>",
        unsafe_allow_html=True,
    )
    render_proposal_card()
    with st.form("final_vote_form"):
        human_vote = st.radio(
            "Your final vote",
            FINAL_VOTE_LABELS,
            format_func=lambda label: FINAL_VOTE_DISPLAY[label],
            horizontal=True,
        )
        submitted = st.form_submit_button("Cast final vote", type="primary", use_container_width=True)
    if submitted:
        _defer("Stakeholders are casting their final votes and the outcome is being judged…",
               _do_final_vote, human_vote)


def render_outcome() -> None:
    outcome = game().outcome
    if outcome is None:
        st.error("No outcome recorded.")
        return
    st.markdown(
        "<div class='round-hdr'><h3>Outcome</h3><p>The meeting closes with a final endorsement result and stakeholder-by-stakeholder outcome summary.</p></div>",
        unsafe_allow_html=True,
    )
    passed = outcome.outcome in {"win", "partial_win"}
    if passed:
        st.success(f"Passed: {outcome.detail}")
        st.balloons()
        st.markdown(
            "<div style='text-align:center;margin:10px 0 4px;'>"
            f"{components.confetti()}&nbsp;&nbsp;"
            f"{components.stamp('ENDORSED', good=True)}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.error(f"Did not pass: {outcome.detail}")
        st.markdown(
            "<div style='text-align:center;margin:10px 0 4px;'>"
            f"{components.stamp('REJECTED', good=False)}</div>",
            unsafe_allow_html=True,
        )
    st.write(f"Endorsements counted by the engine: {outcome.endorsements} / {len(game().scenario.stakeholders)}")

    earned = components.derive_badges(
        passed, outcome.endorsements, len(game().scenario.stakeholders),
        st.session_state.round2_dimension_status,
    )
    st.markdown(components.badges(earned), unsafe_allow_html=True)

    render_proposal_card()

    st.subheader("Final vote board")
    vote_rows = [
        {"role_id": rid, "name": stakeholder_map()[rid].display_name,
         "vote": st.session_state.final_vote_labels[rid]["vote"],
         "reason": st.session_state.final_vote_labels[rid]["reason"]}
        for rid in ROUND1_ORDER if rid in st.session_state.final_vote_labels
    ]
    st.markdown(components.vote_tally(vote_rows), unsafe_allow_html=True)

    st.subheader("Were the goals reached?")
    st.markdown(
        '<div class="proposal-box proposal-neutral">'
        "<b>Passing ≠ everyone winning.</b> The proposal passes on "
        "<i>endorsement count</i>: a stakeholder who votes <i>conditional "
        "endorsement</i> still counts as a yes, because they accept the deal "
        "moving forward <i>despite</i> unmet conditions. So a deal can pass "
        "(≥4 endorsements) while the scorecard below shows several "
        "stakeholders only partially achieved their goals — that's a weak, "
        "barely-passed agreement, which is a realistic negotiation outcome, "
        "not a bug. A strong win is passing <i>and</i> a green scorecard."
        "</div>",
        unsafe_allow_html=True,
    )
    score_rows = [
        {"role_id": rid, "name": stakeholder_map()[rid].display_name,
         "rating": st.session_state.goal_evaluations.get(rid, {}).get("rating", ""),
         "explanation": st.session_state.goal_evaluations.get(rid, {}).get("explanation", "")}
        for rid in ROUND1_ORDER
    ]
    st.markdown(components.scorecard(score_rows), unsafe_allow_html=True)
    data = game().dialog.json(string=True, indent=2)
    st.download_button(
        "Download dialog JSON",
        data=data,
        file_name="swm_dialog.json",
        mime="application/json",
    )
    if st.button("Play again", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


def _role_signal(role_id: str) -> Tuple[str, float]:
    """Best-known avatar (state, satisfaction 0-1) for a stakeholder.

    Priority: final vote > goal evaluation > round-2 flags > neutral default.
    """
    votes = st.session_state.get("final_vote_labels") or {}
    if role_id in votes:
        v = votes[role_id]["vote"]
        return (
            {"unconditional_endorsement": ("endorse", 0.95),
             "conditional_endorsement": ("wary", 0.65),
             "abstention": ("walkout", 0.4),
             "rejection": ("block", 0.12)}.get(v, ("idle", 0.55))
        )
    evals = st.session_state.get("goal_evaluations") or {}
    if role_id in evals:
        r = evals[role_id].get("rating", "")
        return {"fully_achieved": ("endorse", 0.92),
                "partially_achieved": ("wary", 0.6),
                "not_achieved": ("block", 0.2)}.get(r, ("idle", 0.55))
    flags = st.session_state.get("round2_flags") or {}
    if flags:
        score, n, worst = 0.0, 0, "idle"
        for fdata in flags.values():
            rf = fdata.get("flags", {}).get(role_id)
            if not rf:
                continue
            n += 1
            f = rf["flag"]
            score += {"accept": 1.0, "accept_with_condition": 0.5, "reject": 0.0}.get(f, 0.5)
            if f == "reject":
                worst = "block"
            elif f == "accept_with_condition" and worst != "block":
                worst = "wary"
        if n:
            return worst, score / n
    # No flags/votes/eval yet: estimate willingness from how well the current
    # proposal is shaping up on the dimensions this stakeholder cares about
    # most (their REACTION_PRIORITY membership). The meter then tracks goal
    # achievement live during Rounds 1-2.
    statuses = st.session_state.get("round2_dimension_status") or {}
    weight_total = 0.0
    sat = 0.0
    for dim, order in REACTION_PRIORITY.items():
        if role_id not in order:
            continue
        w = len(order) - order.index(role_id)  # higher = cares more
        s = statuses.get(dim, "neutral")
        val = {"green": 1.0, "yellow": 0.6, "neutral": 0.4, "red": 0.1}.get(s, 0.4)
        sat += w * val
        weight_total += w
    if weight_total:
        score = sat / weight_total
        state = (
            "endorse" if score >= 0.8
            else "wary" if score >= 0.5
            else "block" if score <= 0.25
            else "idle"
        )
        return state, score
    return "idle", 0.5


def render_game_header(stage: str) -> None:
    """Persistent gamified header: pipeline spine + City X + avatar roster."""
    active_dim = _current_round2_dimension() if stage == "round2_table" else None
    statuses = st.session_state.round2_dimension_status
    outcome = getattr(game(), "outcome", None)
    ruined = stage == "outcome" and outcome is not None and outcome.outcome not in {"win", "partial_win"}
    st.markdown(components.spine(stage, active_dim, statuses), unsafe_allow_html=True)
    st.markdown(components.city_banner(statuses, ruined=ruined), unsafe_allow_html=True)

    speaker = _next_round1_speaker() if stage == "round1" else None
    cards = []
    for role_id in ROUND1_ORDER:
        s = stakeholder_map()[role_id]
        state, sat = _role_signal(role_id)
        cards.append({
            "role_id": role_id,
            "name": s.display_name + (" (you)" if role_id == human_role() else ""),
            "title": s.public_profile.title,
            "state": state,
            "satisfaction": sat,
            "speaking": role_id == speaker,
        })
    st.markdown(components.roster(cards), unsafe_allow_html=True)


def main() -> None:
    ensure_state()
    st.markdown(components.background_fx(), unsafe_allow_html=True)
    if rt() is None:
        st.markdown(components.chrome_bar("setup"), unsafe_allow_html=True)
        render_setup()
        return

    st.markdown(components.chrome_bar(st.session_state.stage), unsafe_allow_html=True)
    st.markdown(
        "<div style='text-align:center;margin:4px 0 16px;'>"
        "<span style=\"display:inline-block;padding:6px 18px;border-radius:999px;"
        "font-family:var(--wm-font-display);font-size:0.82rem;font-weight:600;"
        "letter-spacing:0.16em;text-transform:uppercase;color:#3f6b3c;"
        "background:rgba(247,243,232,0.7);"
        "border:1px solid rgba(94,125,79,0.22);\">"
        "City X &nbsp;·&nbsp; Eastfield Landfill Crisis</span></div>",
        unsafe_allow_html=True,
    )
    render_sidebar()
    render_game_header(st.session_state.stage)

    stage = st.session_state.stage
    if stage == "role_reveal":
        render_role_reveal()
    elif stage == "round1":
        render_round1()
    elif stage == "round2_bids":
        render_round2_bids()
    elif stage == "round2_table":
        render_round2_table()
    elif stage == "round2_flagging":
        render_round2_flagging()
    elif stage == "round2_results":
        render_round2_results()
    elif stage == "round3":
        render_round3()
    elif stage == "final_vote":
        render_final_vote()
    elif stage == "outcome":
        render_outcome()


main()
