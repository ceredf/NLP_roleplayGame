"""Parametric SVG avatar + City X skyline engine.

Drop-in replacement for ``examples/swm_roleplay/ui/sprites.py``.

Changes vs upstream:
- Avatar refinements: face-shading radial gradient, proper ears with inner
  detail, cheek blush, lip color hint, subtle nose bridge + tip, hair-shine
  highlight, and a distinct hair shape per ``ROLE_LOOK.garment`` style
  (suit_tie / blazer / jacket / shawl / workwear / cap).
- City banner: drifting clouds (animateTransform), sun whose intensity grows
  with progress, lit window grid, refuse texture on the mound when dirty,
  multiple trees emerging mid-cleanup, birds at high cleanup, varied
  building heights with antennas.

Stable swap point unchanged: ``avatar(role_id, state, size)`` and
``city(progress, ruined)`` keep their signatures.
"""
import base64
import os
from functools import lru_cache
from typing import List, Optional

from .theme import role_theme

STATES: List[str] = ["idle", "speaking", "approve", "wary", "block", "endorse", "walkout"]

_ASSET_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
_EXPRESSION = {
    "idle": "neutral", "speaking": "neutral",
    "approve": "happy", "endorse": "happy",
    "wary": "concerned", "walkout": "concerned",
    "block": "angry",
}
EXPRESSIONS = ["neutral", "happy", "concerned", "angry"]


@lru_cache(maxsize=64)
def _asset_uri(role_id: str, expression: str) -> Optional[str]:
    """Return a base64 data URI for an illustrated asset, or None if absent."""
    path = os.path.join(_ASSET_DIR, role_id, f"{expression}.png")
    if not os.path.isfile(path):
        return None
    with open(path, "rb") as fh:
        return "data:image/png;base64," + base64.b64encode(fh.read()).decode("ascii")


ROLE_LOOK = {
    "national_government": dict(skin="#c98a5e", hair="#2b241d", garment="suit_tie", acc="glasses"),
    "municipal_government": dict(skin="#d8a06f", hair="#3a2f24", garment="blazer", acc="glasses"),
    "private_sector_company": dict(skin="#e3b98c", hair="#4a3725", garment="suit_tie", acc="none"),
    "ngo_civil_society": dict(skin="#b6794a", hair="#241d18", garment="jacket", acc="lanyard"),
    "community_member": dict(skin="#a9693f", hair="#1f1a15", garment="shawl", acc="headscarf"),
    "informal_sector_worker": dict(skin="#9c5f38", hair="#1c1713", garment="workwear", acc="cap"),
}
_DEFAULT_LOOK = dict(skin="#c98a5e", hair="#2b241d", garment="blazer", acc="none")


def _mix(c1: str, c2: str, t: float) -> str:
    t = max(0.0, min(1.0, t))
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    m = [round(a[i] + (b[i] - a[i]) * t) for i in range(3)]
    return "#%02x%02x%02x" % tuple(m)


def _shade(hex_color: str, t: float) -> str:
    target = "#ffffff" if t >= 0 else "#000000"
    return _mix(hex_color, target, abs(t))


def _brows(expr: str, ink: str) -> str:
    d = {
        "neutral": ("M-11 -10 q4 -1.5 8 0", "M3 -10 q4 -1.5 8 0"),
        "happy": ("M-11 -12 q4 -2.5 8 0", "M3 -12 q4 -2.5 8 0"),
        "concerned": ("M-11 -12 q4 1.5 8 -0.5", "M3 -11.5 q4 -1.5 8 1.5"),
        "angry": ("M-11 -11 q4 2.5 8 1", "M3 -10 q4 -2.5 8 1"),
    }.get(expr, ("M-11 -10 q4 -1.5 8 0", "M3 -10 q4 -1.5 8 0"))
    return (
        f'<path d="{d[0]}" stroke="{ink}" stroke-width="2.1" fill="none" stroke-linecap="round"/>'
        f'<path d="{d[1]}" stroke="{ink}" stroke-width="2.1" fill="none" stroke-linecap="round"/>'
    )


def _eyes(expr: str, iris: str) -> str:
    lid = {"angry": 1.7, "concerned": 0.7, "neutral": 0.0, "happy": 0.4}.get(expr, 0.0)
    out = ""
    for sx in (-6.5, 6.5):
        out += (
            f'<g transform="translate({sx},-3)">'
            f'<ellipse cx="0" cy="0" rx="3" ry="3.4" fill="#fbf7ee"/>'
            f'<circle cx="0" cy="0.4" r="2" fill="{iris}"/>'
            f'<circle cx="0" cy="0.4" r="1" fill="#1c1714"/>'
            f'<circle cx="0.7" cy="-0.5" r="0.5" fill="#fff"/>'
            f'<path d="M-3.3 -{3.4 - lid} q3.3 -{2.2 - lid} 6.6 0" '
            f'fill="none" stroke="#caa377" stroke-width="0.8" opacity="0.7"/>'
            f'</g>'
        )
    return out


def _mouth(expr: str, ink: str, speaking: bool) -> str:
    if speaking:
        return f'<ellipse cx="0" cy="11" rx="3.6" ry="3" fill="{_shade(ink, -0.35)}"/>'
    d = {
        "neutral": 'M-5 11 q5 1.5 10 0',
        "happy": 'M-6 10 q6 6 12 0',
        "concerned": 'M-5 12 q5 -2 10 0',
        "angry": 'M-6 12.5 q6 -3 12 0',
    }.get(expr, 'M-5 11 q5 1.5 10 0')
    return f'<path d="{d}" stroke="{ink}" stroke-width="2.2" fill="none" stroke-linecap="round"/>'


def _hair(style: str, color: str) -> str:
    """Distinct hair shape per garment style."""
    if style == "headscarf":
        return ""
    if style == "cap":
        return f'<path d="M30 38 q-2 -16 18 -17 q20 1 18 17 q-3 -8 -18 -8 q-15 0 -18 8 Z" fill="{color}"/>'
    if style == "suit_tie":
        return (
            f'<path d="M30 38 q-2 -24 18 -25 q20 1 18 25 q-3 -14 -18 -14 q-15 0 -18 14 Z" fill="{color}"/>'
            f'<path d="M48 13 q-6 4 -10 11 q3 -5 10 -5 q7 0 10 5 q-4 -7 -10 -11 Z" fill="{_shade(color, -0.3)}"/>'
            f'<path d="M32 28 q-1 5 0 9 q1 -4 3 -7 Z" fill="{_shade(color, 0.35)}" opacity="0.7"/>'
        )
    if style == "blazer":
        return (
            f'<path d="M30 38 q-2 -25 18 -25 q20 0 18 25 '
            f'q-3 -13 -10 -13 q-3 0 -4 4 q-2 -4 -7 -4 q-5 0 -7 4 q-1 -4 -4 -4 q-7 0 -10 13 Z" fill="{color}"/>'
            f'<path d="M30 38 q0 -10 5 -16 q-2 8 -1 14 Z" fill="{_shade(color, -0.3)}"/>'
        )
    if style == "jacket":
        return (
            f'<path d="M30 38 q-3 -27 18 -27 q21 0 18 27 q-1 -10 -6 -12 '
            f'q-1 4 -4 5 q-1 -5 -6 -5 q-5 0 -6 5 q-3 -1 -4 -5 q-5 2 -10 12 Z" fill="{color}"/>'
            f'<path d="M62 24 q4 4 5 12 q-3 -5 -7 -7 Z" fill="{_shade(color, -0.3)}"/>'
        )
    return (
        f'<path d="M30 38 q-2 -24 18 -25 q20 1 18 25 '
        f'q-3 -12 -18 -12 q-15 0 -18 12 Z" fill="{color}"/>'
        f'<path d="M30 38 q-1 -8 3 -13 l2 4 q-3 5 -2 11 Z" fill="{_shade(color, -0.25)}"/>'
    )


def _garment(style: str, accent: str) -> str:
    dark = _shade(accent, -0.32)
    base = f'<path d="M14 92 q34 -34 68 0 Z" fill="{accent}"/>'
    if style == "suit_tie":
        return (
            f'<path d="M14 92 q34 -34 68 0 Z" fill="{dark}"/>'
            f'<path d="M40 64 L48 92 L56 64 L48 70 Z" fill="#f4efe2"/>'
            f'<path d="M45 66 L48 72 L51 66 L48 64 Z" fill="{accent}"/>'
            f'<path d="M48 72 L44 90 L52 90 Z" fill="{_shade(accent, -0.12)}"/>'
            f'<path d="M40 64 L30 78 L34 92 L42 70 Z" fill="{_shade(accent, -0.45)}"/>'
            f'<path d="M56 64 L66 78 L62 92 L54 70 Z" fill="{_shade(accent, -0.45)}"/>'
        )
    if style == "blazer":
        return (
            base
            + '<path d="M40 64 L48 90 L56 64 L48 70 Z" fill="#f1ece0"/>'
            + f'<path d="M40 64 L31 80 L36 92 L44 70 Z" fill="{_shade(accent, -0.3)}"/>'
            + f'<path d="M56 64 L65 80 L60 92 L52 70 Z" fill="{_shade(accent, -0.3)}"/>'
        )
    if style == "jacket":
        return (
            base
            + f'<rect x="46.5" y="64" width="3" height="28" fill="{_shade(accent, -0.4)}"/>'
            + f'<path d="M38 66 q10 -5 20 0 l-2 5 q-8 -4 -16 0 Z" fill="{_shade(accent, -0.28)}"/>'
        )
    if style == "shawl":
        return (
            base
            + f'<path d="M22 92 q26 -30 52 0 q-26 -14 -52 0 Z" fill="{_shade(accent, 0.22)}"/>'
            + f'<path d="M40 66 q8 6 16 0 l-3 9 q-5 3 -10 0 Z" fill="{_shade(accent, 0.34)}"/>'
        )
    if style == "workwear":
        return (
            base
            + f'<path d="M38 66 q10 5 20 0 l-1 7 q-9 4 -18 0 Z" fill="{_shade(accent, -0.22)}"/>'
            + '<path d="M30 74 L40 70 L42 92 L30 92 Z" fill="#d6c34a"/>'
            + '<path d="M66 74 L56 70 L54 92 L66 92 Z" fill="#d6c34a"/>'
        )
    return base


def _accessory(acc: str, accent: str) -> str:
    if acc == "glasses":
        return (
            f'<g fill="none" stroke="{_shade(accent, -0.5)}" stroke-width="1.5">'
            f'<rect x="38" y="33" width="9" height="7.5" rx="2"/>'
            f'<rect x="49" y="33" width="9" height="7.5" rx="2"/>'
            f'<path d="M47 36 h2"/><path d="M38 35 l-4 -1"/><path d="M58 35 l4 -1"/></g>'
        )
    if acc == "headscarf":
        return (
            f'<path d="M30 40 q-4 -28 18 -29 q22 1 18 29 '
            f'q-2 -6 -6 -9 q3 14 -6 18 q4 -16 -6 -22 '
            f'q-10 6 -6 22 q-9 -4 -6 -18 q-4 3 -6 9 Z" fill="{accent}"/>'
            f'<path d="M30 40 q2 -7 7 -10 q-2 6 -1 11 Z" fill="{_shade(accent, 0.22)}"/>'
        )
    if acc == "cap":
        return (
            f'<path d="M33 30 q15 -15 30 0 q-15 -7 -30 0 Z" fill="{_shade(accent, -0.2)}"/>'
            f'<path d="M30 30 q-7 1 -9 4 q10 -1 12 -3 Z" fill="{_shade(accent, -0.35)}"/>'
        )
    if acc == "lanyard":
        return (
            f'<path d="M44 60 L47 78" stroke="{_shade(accent, -0.45)}" stroke-width="2" fill="none"/>'
            f'<path d="M54 60 L51 78" stroke="{_shade(accent, -0.45)}" stroke-width="2" fill="none"/>'
            f'<rect x="44" y="78" width="10" height="7" rx="1.5" fill="#f4efe2" '
            f'stroke="{_shade(accent, -0.3)}" stroke-width="0.8"/>'
        )
    return ""


def _state_accent(state: str, color: str) -> str:
    if state == "speaking":
        return (
            f'<circle cx="78" cy="34" r="2.6" fill="{color}" opacity="0.5">'
            f'<animate attributeName="opacity" values="0.2;0.9;0.2" dur="1.1s" repeatCount="indefinite"/></circle>'
            f'<circle cx="86" cy="34" r="3.4" fill="none" stroke="{color}" stroke-width="2" opacity="0.4">'
            f'<animate attributeName="r" values="3;7;3" dur="1.4s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0.5;0;0.5" dur="1.4s" repeatCount="indefinite"/></circle>'
        )
    if state in ("approve", "endorse"):
        return (
            '<g transform="translate(75,17)"><circle r="11" fill="#2f7a4c"/>'
            '<path d="M-5 0 l3 4 l6 -8" stroke="#fff" stroke-width="2.6" fill="none" '
            'stroke-linecap="round" stroke-linejoin="round"/></g>'
        )
    if state == "wary":
        return ('<g transform="translate(75,17)"><circle r="11" fill="#c89c62"/>'
                '<text x="0" y="4" font-size="13" text-anchor="middle" fill="#fff" font-weight="700">!</text></g>')
    if state == "block":
        return ('<g transform="translate(75,17)"><circle r="11" fill="#b76554"/>'
                '<path d="M-4 -4 l8 8 M4 -4 l-8 8" stroke="#fff" stroke-width="2.6" stroke-linecap="round"/></g>')
    return ""


def avatar(role_id: str, state: str = "idle", size: int = 76) -> str:
    """Return an inline SVG bust for ``role_id`` in a given reaction ``state``."""
    if state not in STATES:
        state = "idle"
    t = role_theme(role_id)
    color = t["color"]
    emoji = t["emoji"]
    opacity = "0.45" if state == "walkout" else "1"

    uri = _asset_uri(role_id, _EXPRESSION.get(state, "neutral"))
    if uri is not None:
        return (
            f'<img src="{uri}" width="{size}" height="{size}" '
            f'alt="{role_id} {state}" '
            f'style="border-radius:50%;object-fit:cover;opacity:{opacity};'
            f'border:3px solid {color};box-shadow:0 6px 16px rgba(72,66,43,0.18);"/>'
        )
    expr = _EXPRESSION.get(state, "neutral")
    look = ROLE_LOOK.get(role_id, _DEFAULT_LOOK)
    skin = look["skin"]
    skin_dk = _shade(skin, -0.2)
    skin_dkr = _shade(skin, -0.35)
    skin_lt = _shade(skin, 0.10)
    clip = f"clip{role_id}"
    face_shade_id = f"face{role_id}"
    hair_shine_id = f"hairshine{role_id}"
    return (
        f'<svg viewBox="0 0 96 96" width="{size}" height="{size}" '
        f'role="img" aria-label="{role_id} {state}" style="opacity:{opacity};">'
        f'<defs>'
        f'<radialGradient id="bg{role_id}" cx="50%" cy="36%" r="72%">'
        f'<stop offset="0%" stop-color="#fbf7ee"/><stop offset="100%" stop-color="{t["bg"]}"/>'
        f'</radialGradient>'
        f'<radialGradient id="{face_shade_id}" cx="30%" cy="40%" r="70%">'
        f'<stop offset="0%" stop-color="{skin_lt}" stop-opacity="0.5"/>'
        f'<stop offset="55%" stop-color="{skin}" stop-opacity="0"/>'
        f'<stop offset="100%" stop-color="{skin_dkr}" stop-opacity="0.45"/>'
        f'</radialGradient>'
        f'<linearGradient id="{hair_shine_id}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{_shade(look["hair"], 0.25)}" stop-opacity="0.55"/>'
        f'<stop offset="100%" stop-color="{look["hair"]}" stop-opacity="0"/>'
        f'</linearGradient>'
        f'<clipPath id="{clip}"><circle cx="48" cy="48" r="44"/></clipPath>'
        f'</defs>'
        f'<circle cx="48" cy="48" r="46" fill="url(#bg{role_id})" stroke="{color}" stroke-width="3"/>'
        f'<g clip-path="url(#{clip})">'
        # whole figure nudged down so the face sits centred in the circle
        f'<g transform="translate(0,6)">'
        # garment / shoulders
        f'{_garment(look["garment"], color)}'
        # neck + chin shadow
        f'<path d="M42 56 q6 7 12 0 l1 9 q-7 6 -14 0 Z" fill="{skin_dk}"/>'
        f'<path d="M40 56 q8 8 16 0 l-1 4 q-7 5 -14 0 Z" fill="{skin_dkr}" opacity="0.5"/>'
        # ears with inner detail
        f'<ellipse cx="32" cy="40" rx="3" ry="4.2" fill="{skin}"/>'
        f'<ellipse cx="31.5" cy="41" rx="1.4" ry="2.4" fill="{skin_dkr}" opacity="0.6"/>'
        f'<ellipse cx="64" cy="40" rx="3" ry="4.2" fill="{skin}"/>'
        f'<ellipse cx="64.5" cy="41" rx="1.4" ry="2.4" fill="{skin_dkr}" opacity="0.6"/>'
        # head shape
        f'<path d="M30 38 q0 -23 18 -23 q18 0 18 23 q0 17 -18 20 q-18 -3 -18 -20 Z" fill="{skin}"/>'
        # face shading overlay
        f'<path d="M30 38 q0 -23 18 -23 q18 0 18 23 q0 17 -18 20 q-18 -3 -18 -20 Z" fill="url(#{face_shade_id})"/>'
        # cheek blush
        f'<ellipse cx="36" cy="43" rx="3.2" ry="2.2" fill="#d8835a" opacity="0.18"/>'
        f'<ellipse cx="60" cy="43" rx="3.2" ry="2.2" fill="#d8835a" opacity="0.18"/>'
        # hair + hair shine
        f'{_hair(look["garment"], look["hair"])}'
        f'<path d="M30 38 q-2 -24 18 -25 q20 1 18 25 q-3 -12 -18 -12 q-15 0 -18 12 Z" fill="url(#{hair_shine_id})"/>'
        # face features (origin at face centre ~48,38)
        f'<g transform="translate(48,38)">'
        f'{_brows(expr, look["hair"])}'
        f'{_eyes(expr, _shade(look["hair"], 0.18))}'
        # nose: bridge shadow + tip
        f'<path d="M-1 -2 q-1 6 0 8 q1 -1 2 0" stroke="{skin_dkr}" stroke-width="1.1" '
        f'fill="none" stroke-linecap="round" opacity="0.55"/>'
        f'<ellipse cx="0" cy="6.2" rx="1.6" ry="0.9" fill="{skin_dkr}" opacity="0.35"/>'
        # upper-lip hint (skipped when speaking)
        + ('' if state == 'speaking' else
           '<path d="M-4 10.5 q4 -2 8 0" stroke="#8a4a3a" stroke-width="1.6" '
           'fill="none" stroke-linecap="round" opacity="0.5"/>')
        + f'{_mouth(expr, "#7a4a3c", state == "speaking")}'
        + '</g>'
        + f'{_accessory(look["acc"], color)}'
        + '</g></g>'
        # role glyph chip (small, lower-left)
        + f'<g transform="translate(20,80)"><circle r="9.5" fill="#fbf7ee" stroke="{color}" stroke-width="2"/>'
        + f'<text x="0" y="4" font-size="11" text-anchor="middle">{emoji}</text></g>'
        + f'{_state_accent(state, color)}'
        + '</svg>'
    )


def _smoke(x: int, intensity: float) -> str:
    if intensity <= 0:
        return ""
    op = min(0.7, 0.2 + intensity * 0.5)
    puffs = ""
    for i in range(3):
        puffs += (
            f'<circle cx="{x + i * 4 - 4}" cy="118" r="{5 + i}" fill="#7c7c70" opacity="{op}">'
            f'<animate attributeName="cy" values="118;80" dur="{2.4 + i * 0.4}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="{op};0" dur="{2.4 + i * 0.4}s" repeatCount="indefinite"/>'
            f'<animate attributeName="r" values="{5+i};{10+i}" dur="{2.4 + i * 0.4}s" repeatCount="indefinite"/>'
            f'</circle>'
        )
    return puffs


def _windows(x: int, y: int, w: int, h: int, build_idx: int, lit_color: str, dim_color: str, progress: float) -> str:
    """Window grid for a building rect."""
    out = ""
    rows = max(1, h // 8)
    cols = max(1, w // 7)
    for row in range(rows):
        for col in range(cols):
            wx = x + 2 + col * 7
            wy = y + 4 + row * 8
            if wx + 3 > x + w - 1:
                continue
            lit = ((build_idx * 7 + row * 3 + col) % 5 == 0) and progress > 0.4
            fill = lit_color if lit else dim_color
            op = "0.95" if lit else "0.4"
            out += f'<rect x="{wx}" y="{wy}" width="3" height="3" fill="{fill}" opacity="{op}"/>'
    return out


def city(progress: float, ruined: bool = False) -> str:
    """Return an SVG of City X. ``progress`` in [0,1].

    Enhancements over the previous version: drifting clouds, sun whose
    intensity tracks progress, lit window grids on the buildings (evening
    city in late game), refuse texture on the mound when dirty, multiple
    trees emerging in mid-cleanup, and birds at high cleanup.
    """
    progress = 0.0 if ruined else max(0.0, min(1.0, progress))
    sky_top = "#5b5a4d" if ruined else _mix("#9bbcd6", "#cfe3f0", progress)
    sky_mid = "#7c7461" if ruined else _mix("#bcc8b2", "#dde9d3", progress)
    sky_bot = "#7c7a68" if ruined else _mix("#c6c4a8", "#eaf3e4", progress)
    ground = _mix("#9c8d63", "#6c9a52", progress)
    ground_dk = _shade(ground, -0.18)
    mound = _mix("#8a7c54", "#5e8a48", progress)
    build_tone = _mix("#6f6a55", "#5e7d4f", progress)
    build_shade = _shade(build_tone, -0.22)
    window_glow = _mix("#fdd98a", "#fff2c8", progress)
    sun_opacity = 0 if ruined else (0.2 + progress * 0.55)
    smoke_intensity = 1.0 if ruined else max(0.0, 1.0 - progress * 1.4)
    green_pct = int(progress * 100)
    show_birds = progress > 0.6
    uid = f"c{green_pct}"

    # skyline buildings: (x, y, w, h)
    buildings = [
        (20, 62, 26, 72),
        (50, 48, 22, 86),
        (76, 70, 30, 64),
        (112, 56, 24, 78),
        (142, 64, 18, 70),
        (164, 50, 26, 84),
        (196, 68, 20, 66),
    ]
    skyline = ""
    for i, (x, y, w, h) in enumerate(buildings):
        skyline += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{build_tone}"/>'
        skyline += f'<rect x="{x}" y="{y}" width="{int(w * 0.35)}" height="{h}" fill="{build_shade}" opacity="0.55"/>'
        if h > 80:
            skyline += (
                f'<line x1="{x + w / 2}" y1="{y}" x2="{x + w / 2}" y2="{y - 8}" '
                f'stroke="{build_shade}" stroke-width="1.5"/>'
            )
        skyline += _windows(x, y, w, h, i, window_glow, build_shade, progress)

    refuse = ""
    if progress < 0.5:
        for i, (cx, cy) in enumerate([(228, 118), (240, 114), (252, 110), (266, 108),
                                      (278, 112), (292, 116), (248, 122), (262, 120),
                                      (278, 122), (232, 124)]):
            op = max(0.0, 0.65 - progress)
            refuse += (
                f'<rect x="{cx}" y="{cy}" width="3" height="2.5" '
                f'fill="{_shade(mound, -0.45)}" opacity="{op}" '
                f'transform="rotate({(i * 23) % 60} {cx} {cy})"/>'
            )

    trees = ""
    if progress > 0.35:
        n = int(round(progress * 5))
        op = min(1.0, (progress - 0.35) * 2)
        for tx in [228, 248, 268, 288, 312][:n]:
            trees += (
                f'<g opacity="{op}">'
                f'<rect x="{tx - 1.5}" y="120" width="3" height="12" fill="#6b4f2a"/>'
                f'<circle cx="{tx}" cy="118" r="7" fill="#3f6b3c"/>'
                f'<circle cx="{tx + 2}" cy="116" r="4" fill="#5e7d4f"/>'
                f'</g>'
            )

    recycle_marker = ""
    if 0.3 < progress < 0.95:
        recycle_marker = (
            '<g transform="translate(254,108)">'
            '<circle r="10" fill="#fbf7ee" opacity="0.95"/>'
            '<text x="0" y="4" font-size="12" text-anchor="middle">♻️</text></g>'
        )

    clouds = "" if ruined else (
        f'<g opacity="{0.55 + progress * 0.25}">'
        '<g>'
        '<ellipse cx="60" cy="32" rx="22" ry="6" fill="#fff" opacity="0.9"/>'
        '<ellipse cx="78" cy="30" rx="14" ry="5" fill="#fff" opacity="0.9"/>'
        '<animateTransform attributeName="transform" type="translate" '
        'values="0,0;30,0;0,0" dur="38s" repeatCount="indefinite"/></g>'
        '<g>'
        '<ellipse cx="190" cy="22" rx="18" ry="5" fill="#fff" opacity="0.85"/>'
        '<ellipse cx="205" cy="21" rx="11" ry="4" fill="#fff" opacity="0.85"/>'
        '<animateTransform attributeName="transform" type="translate" '
        'values="0,0;-22,0;0,0" dur="46s" repeatCount="indefinite"/></g>'
        '</g>'
    )

    birds = ""
    if show_birds:
        birds = (
            '<g fill="none" stroke="#2a2d26" stroke-width="1.2" stroke-linecap="round">'
            '<g>'
            '<path d="M0 0 q3 -3 6 0 q3 -3 6 0" transform="translate(120,55)"/>'
            '<path d="M0 0 q2.5 -2 5 0 q2.5 -2 5 0" transform="translate(140,48)"/>'
            '<path d="M0 0 q3 -3 6 0 q3 -3 6 0" transform="translate(160,52)"/>'
            '<animateTransform attributeName="transform" type="translate" '
            'values="0,0;180,-6;360,0" dur="30s" repeatCount="indefinite"/>'
            '</g></g>'
        )

    return (
        '<div class="wm-city">'
        '<svg viewBox="0 0 360 160" preserveAspectRatio="none" height="160">'
        '<defs>'
        f'<linearGradient id="sky{uid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{sky_top}"/>'
        f'<stop offset="55%" stop-color="{sky_mid}"/>'
        f'<stop offset="100%" stop-color="{sky_bot}"/>'
        '</linearGradient>'
        f'<radialGradient id="sun{uid}" cx="50%" cy="50%" r="50%">'
        '<stop offset="0%" stop-color="#fff3c8" stop-opacity="1"/>'
        '<stop offset="60%" stop-color="#f7d98a" stop-opacity="0.5"/>'
        '<stop offset="100%" stop-color="#f7d98a" stop-opacity="0"/>'
        '</radialGradient>'
        f'<linearGradient id="mound{uid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{mound}"/>'
        f'<stop offset="100%" stop-color="{_shade(mound, -0.2)}"/>'
        '</linearGradient>'
        '</defs>'
        f'<rect width="360" height="160" fill="url(#sky{uid})"/>'
        f'<g opacity="{sun_opacity}">'
        f'<circle cx="295" cy="42" r="22" fill="url(#sun{uid})"/>'
        '<circle cx="295" cy="42" r="10" fill="#fff3c8" opacity="0.9"/>'
        '</g>'
        f'{clouds}'
        f'<path d="M0 110 q60 -22 120 -8 q60 14 120 -4 q60 -16 120 6 L360 130 L0 130 Z" '
        f'fill="{_mix("#94a780", "#7a9a5e", progress)}" opacity="0.55"/>'
        f'{skyline}'
        f'<rect x="0" y="130" width="360" height="30" fill="{ground}"/>'
        f'<rect x="0" y="130" width="360" height="3" fill="{ground_dk}" opacity="0.6"/>'
        f'<path d="M212 132 q42 -{36 - int(progress * 24)} 86 0 Z" fill="url(#mound{uid})"/>'
        f'{refuse}{trees}{recycle_marker}'
        f'{_smoke(250, smoke_intensity)}'
        f'{birds}'
        '</svg>'
        + '<div class="wm-city-cap">City X — '
        + ("⚠️ negotiation collapsed: the landfill crisis stands unresolved." if ruined
           else f"cleanup progress: {green_pct}% · the skyline clears as the plan takes shape.")
        + '</div></div>'
    )
