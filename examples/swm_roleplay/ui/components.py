"""Composed game UI: pipeline spine, city banner, avatar roster, transcript
bubbles, vote tally, outcome scorecard, badges.

Drop-in replacement for ``examples/swm_roleplay/ui/components.py``.

Changes vs upstream:
- ``transcript_bubble`` now includes an inline 36px avatar at the start of
  every stakeholder bubble (and an emoji disc for the moderator). It also
  accepts a ``typing=True`` flag that renders three bouncing dots instead of
  the message text — useful when an agent is mid-generation.
- New ``chrome_bar(stage)`` returns the top SWM wordmark + phase chip.
- New ``setup_hero(logo_path)`` returns the centered SWM logo block for the
  setup screen.
"""
import base64
import os
from typing import Dict, List, Optional

from .theme import role_theme
from . import sprites

# Stage -> pipeline phase. The waste-processing metaphor.
_PHASES = [
    ("INTAKE", "🚚"),
    ("SORTING", "♻️"),
    ("PROCESSING", "🛠️"),
    ("TRANSFORM", "🌱"),
    ("VERDICT", "🏆"),
]
_STAGE_TO_PHASE = {
    "setup": 0, "role_reveal": 0,
    "round1": 1,
    "round2_bids": 2, "round2_table": 2, "round2_flagging": 2, "round2_results": 2,
    "round3": 3, "final_vote": 3,
    "outcome": 4,
}

_NEGOTIABLE = ["financing", "community_health_protections", "livelihoods", "monitoring_and_enforcement"]
_MODULE_LABEL = {
    "financing": "💰 Financing",
    "community_health_protections": "🛡️ Health",
    "livelihoods": "♻️ Livelihoods",
    "monitoring_and_enforcement": "📋 Monitoring",
}

_PHASE_LABELS = {
    "setup": "SETUP", "role_reveal": "PHASE 0 · SETUP",
    "round1": "ROUND 1 · OPENING POSITIONS",
    "round2_bids": "ROUND 2 · BIDS",
    "round2_table": "ROUND 2 · NEGOTIATION TABLE",
    "round2_flagging": "ROUND 2 · FLAGGING",
    "round2_results": "ROUND 2 · RESULTS",
    "round3": "ROUND 3 · RESOLUTION",
    "final_vote": "FINAL VOTE",
    "outcome": "OUTCOME",
}


def progress_from_statuses(dim_statuses: Dict[str, str]) -> float:
    """Cleanup progress in [0,1] from the 4 negotiable dimension statuses."""
    score = 0.0
    for dim in _NEGOTIABLE:
        s = dim_statuses.get(dim, "neutral")
        score += 1.0 if s == "green" else 0.5 if s == "yellow" else 0.0
    return score / len(_NEGOTIABLE)


def chrome_bar(stage: str = "setup") -> str:
    """SWM wordmark + phase chip — render at the top of every page.

    Call from streamlit_app.py just BEFORE ``render_game_header(...)`` (or at
    the very top of the page on setup). Streamlit doesn't easily let us mount
    a real top bar, so this is just an HTML block.
    """
    phase = _PHASE_LABELS.get(stage, "LIVE")
    return (
        '<div class="cx-chrome">'
        '<a class="cx-chrome-logo" href="#">'
        '<span><span class="wordmark">S<em>W</em>M</span>'
        '<span class="tag">Negotiation Game</span></span>'
        '</a>'
        '<div class="cx-chrome-right">'
        f'<span class="cx-chip"><span class="dot"></span>{phase}</span>'
        '</div></div>'
    )


def setup_hero(logo_path: Optional[str] = None) -> str:
    """Centered SWM logo block for the setup screen.

    Reads ``logo_path`` (relative to the examples/swm_roleplay folder) and
    inlines it as a base64 data URI so Streamlit can render it directly.
    Falls back to a typographic wordmark if the file is missing.
    """
    if logo_path:
        full = os.path.join(os.path.dirname(__file__), "..", logo_path)
        if os.path.isfile(full):
            with open(full, "rb") as fh:
                data = base64.b64encode(fh.read()).decode("ascii")
            mime = "image/svg+xml" if full.endswith(".svg") else "image/png"
            return (
                '<div class="cx-setup-hero">'
                f'<img class="logo" src="data:{mime};base64,{data}" alt="SWM"/>'
                '</div>'
            )
    return (
        '<div class="cx-setup-hero" style="font-family:Georgia,serif;font-size:96px;'
        'font-weight:700;color:#2a2d26;letter-spacing:-2px;">'
        'S<em style="color:#3f6b3c;">W</em>M</div>'
    )


def spine(stage: str, round2_active_dim: Optional[str], dim_statuses: Dict[str, str]) -> str:
    cur = _STAGE_TO_PHASE.get(stage, 0)
    steps = ""
    for i, (name, ico) in enumerate(_PHASES):
        cls = "active" if i == cur else "done" if i < cur else ""
        check = " ✓" if i < cur else ""
        steps += (f'<div class="wm-spine-step {cls}">'
                  f'<span class="ico">{ico}</span>{name}{check}</div>')
    html = f'<div class="wm-spine">{steps}</div>'
    if cur == 2:
        mods = ""
        for dim in _NEGOTIABLE:
            st_ = dim_statuses.get(dim, "neutral")
            cls = {"green": "s-green", "yellow": "s-yellow", "red": "s-red"}.get(st_, "")
            if dim == round2_active_dim:
                cls = "s-active"
            mods += f'<div class="wm-module {cls}">{_MODULE_LABEL[dim]}</div>'
        html += f'<div class="wm-subtrack">{mods}</div>'
    return html


def city_banner(dim_statuses: Dict[str, str], ruined: bool = False) -> str:
    return sprites.city(progress_from_statuses(dim_statuses), ruined=ruined)


def avatar_card(role_id: str, name: str, title: str, state: str = "idle",
                satisfaction: Optional[float] = None, speaking: bool = False) -> str:
    meter = ""
    if satisfaction is not None:
        pct = int(max(0.0, min(1.0, satisfaction)) * 100)
        low = " low" if pct < 45 else ""
        # cx-meter-shimmer adds a light sweep over the filling bar (effects pack)
        meter = (
            f'<div class="wm-meter{low} cx-meter-shimmer">'
            f'<span style="width:{pct}%"></span></div>'
        )
    spk = " speaking" if speaking else ""
    # The active/speaking stakeholder gets the glow-pulse effect.
    glow = " cx-anim-glow" if speaking else ""
    return (
        f'<div class="wm-av-card{spk}{glow}">'
        f'{sprites.avatar(role_id, "speaking" if speaking else state, 70)}'
        f'<div class="wm-av-name">{name}</div>'
        f'<div class="wm-av-title">{title}</div>'
        f'{meter}</div>'
    )


def roster(cards: List[Dict]) -> str:
    inner = "".join(
        avatar_card(
            c["role_id"], c["name"], c.get("title", ""),
            c.get("state", "idle"), c.get("satisfaction"), c.get("speaking", False),
        )
        for c in cards
    )
    return f'<div class="wm-roster">{inner}</div>'


def _typing_dots(color: str = "#5b4a32") -> str:
    return (
        f'<span class="wm-typing" style="--dot-color:{color};">'
        '<span></span><span></span><span></span></span>'
    )


def transcript_bubble(role_id: str, speaker: str, text: str,
                      is_human: bool = False, is_moderator: bool = False,
                      typing: bool = False) -> str:
    """A themed transcript bubble with inline avatar + optional typing dots."""
    if is_moderator:
        body = _typing_dots("#5e7d4f") if typing else text
        return (
            '<div class="msg-bubble msg-mod wm-bubble-row">'
            '<div class="wm-bubble-av wm-mod-av">🎙️</div>'
            '<div class="wm-bubble-body"><b>Moderator</b>'
            f'<div class="wm-bubble-text">{body}</div></div></div>'
        )
    t = role_theme(role_id)
    av_state = "speaking" if typing else "idle"
    body_html = _typing_dots(t["color"]) if typing else text
    extra_cls = " msg-human" if is_human else ""
    return (
        f'<div class="msg-bubble{extra_cls} wm-bubble-row" '
        f'style="border-left-color:{t["color"]};">'
        f'<div class="wm-bubble-av">{sprites.avatar(role_id, av_state, 36)}</div>'
        f'<div class="wm-bubble-body">'
        f'<b style="color:{t["color"]};">{t["emoji"]} {speaker}</b>'
        f'<div class="wm-bubble-text">{body_html}</div>'
        '</div></div>'
    )


_VOTE_PILL = {
    "unconditional_endorsement": ("v-green", "Unconditional"),
    "conditional_endorsement": ("v-yellow", "Conditional"),
    "abstention": ("v-neutral", "Abstention"),
    "rejection": ("v-red", "Rejection"),
    "accept": ("v-green", "Accept"),
    "accept_with_condition": ("v-yellow", "With condition"),
    "reject": ("v-red", "Reject"),
}


def vote_tally(rows: List[Dict]) -> str:
    out = ""
    for r in rows:
        t = role_theme(r["role_id"])
        cls, label = _VOTE_PILL.get(r["vote"], ("v-neutral", "Vote"))
        out += (
            f'<div class="wm-vote-row" style="border-left:5px solid {t["color"]};">'
            f'{sprites.avatar(r["role_id"], _vote_state(r["vote"]), 44)}'
            f'<div style="flex:1;"><b>{t["emoji"]} {r["name"]}</b> '
            f'<span class="wm-pill {cls}">{label}</span><br>'
            f'<small>{r.get("reason", "")}</small></div></div>'
        )
    return out


def _vote_state(vote: str) -> str:
    if vote in ("unconditional_endorsement", "accept"):
        return "endorse"
    if vote in ("conditional_endorsement", "accept_with_condition"):
        return "wary"
    if vote in ("rejection", "reject"):
        return "block"
    return "walkout"


_RATING = {
    "fully_achieved": ("v-green", "Fully achieved"),
    "partially_achieved": ("v-yellow", "Partially achieved"),
    "not_achieved": ("v-red", "Not achieved"),
}


def scorecard(rows: List[Dict]) -> str:
    out = ""
    for r in rows:
        t = role_theme(r["role_id"])
        cls, label = _RATING.get(r["rating"], ("v-neutral", "Not rated"))
        face = "endorse" if cls == "v-green" else "wary" if cls == "v-yellow" else "block"
        out += (
            f'<div class="wm-vote-row" style="border-left:5px solid {t["color"]};">'
            f'{sprites.avatar(r["role_id"], face, 44)}'
            f'<div style="flex:1;"><b>{t["emoji"]} {r["name"]}</b> '
            f'<span class="wm-pill {cls}">{label}</span><br>'
            f'<small>{r.get("explanation", "")}</small></div></div>'
        )
    return out


def badges(earned: List[str]) -> str:
    if not earned:
        return ""
    chips = "".join(f'<span class="wm-badge-trophy">🏅 {b}</span>' for b in earned)
    return f'<div style="margin:10px 0;">{chips}</div>'


def derive_badges(passed: bool, endorsements: int, total: int,
                  dim_statuses: Dict[str, str]) -> List[str]:
    out: List[str] = []
    greens = sum(1 for d in _NEGOTIABLE if dim_statuses.get(d) == "green")
    if passed:
        out.append("Deal Brokered")
    if endorsements == total and total:
        out.append("Full Consensus")
    if greens == len(_NEGOTIABLE):
        out.append("Clean Sweep — every module solid")
    elif greens >= 2:
        out.append("Coalition Builder")
    if not any(dim_statuses.get(d) == "red" for d in _NEGOTIABLE):
        out.append("Red Line Held")
    return out


# --- Effects pack helpers (claude_design/effects) -------------------------

_PARTICLE_GLYPHS = ["♻️", "🌿", "📄", "🍃"]


def background_fx() -> str:
    """Fixed, behind-content atmospheric layer: grain + conveyor + drifting
    particles + sparkles. Render once, near the top of the page. Safe in
    Streamlit because it is position:fixed/z-index:0 and never clips content.
    """
    particles = ""
    for i in range(12):
        left = 4 + (i * 8) % 92
        dur = 16 + (i * 3) % 14
        delay = (i * 2) % 12
        size = 14 + (i % 3) * 5
        glyph = _PARTICLE_GLYPHS[i % len(_PARTICLE_GLYPHS)]
        particles += (
            f'<div class="cx-particle" style="left:{left}%;'
            f'width:{size}px;height:{size}px;'
            f'animation-duration:{dur}s;animation-delay:{delay}s;">'
            f'<span style="font-size:{size}px;line-height:1;">{glyph}</span></div>'
        )
    sparkles = ""
    for i in range(7):
        sparkles += (
            f'<div class="cx-sparkle" style="left:{(i * 14 + 6) % 96}%;'
            f'top:{(i * 13 + 8) % 80}%;animation-delay:{(i * 0.7) % 4}s;"></div>'
        )
    return (
        '<div class="cx-bg-fx" aria-hidden="true">'
        '<div class="cx-bg-grain"></div>'
        f'{particles}{sparkles}'
        '<div class="cx-bg-conveyor"></div>'
        '</div>'
    )


def confetti() -> str:
    """A 12-piece confetti burst (use sparingly — e.g. proposal passed)."""
    return '<span class="cx-confetti">' + ("<i></i>" * 12) + '</span>'


def stamp(text: str, good: bool = True) -> str:
    """An official-ink stamp that thumps down (e.g. ENDORSED / REJECTED)."""
    cls = "cx-stamp green" if good else "cx-stamp"
    return f'<span class="{cls}">{text}</span>'
