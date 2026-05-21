"""Single source of truth for palette, stakeholder identity, and global CSS.

Drop-in replacement for ``examples/swm_roleplay/ui/theme.py``.

Changes vs upstream:
- Added animated aurora field on .stApp (cxAurora keyframes).
- Added .cx-chrome top bar styling for the SWM wordmark chrome.
- Added .wm-bubble-row + .wm-bubble-av + .wm-typing for the new transcript
  bubbles that include an inline avatar + typing-dot animation.
- Added .wm-pill v-green / v-yellow / v-red / v-neutral as canonical names
  (kept alongside the existing styles).
- Added wmTypingDot, wmSpeakDot, cxAurora, cxLogoIn, cxDot keyframes.

Stakeholder palette + colors are unchanged.
"""
from typing import Dict

# --- Core palette ---------------------------------------------------------
PALETTE: Dict[str, str] = {
    "olive_deep": "#3f6b3c",
    "olive": "#5e7d4f",
    "sage": "#a8aa9b",
    "stone": "#d8d5cc",
    "paper": "#c89c62",
    "kraft": "#8e6b3f",
    "charcoal": "#2a2d26",
    "cream": "#f7f3e8",
    "danger": "#b76554",
    "amber": "#c89c62",
}

# --- Stakeholder identity (the ONLY place colors/emoji are defined) -------
STAKEHOLDER_THEME: Dict[str, Dict[str, str]] = {
    "national_government": {"emoji": "🏛️", "color": "#245c4a", "bg": "#eef8f1", "short": "National"},
    "municipal_government": {"emoji": "🏙️", "color": "#2f6f5e", "bg": "#effaf6", "short": "Municipal"},
    "private_sector_company": {"emoji": "💼", "color": "#7a5a1f", "bg": "#f8f4e8", "short": "Private"},
    "ngo_civil_society": {"emoji": "🌿", "color": "#1f7a4c", "bg": "#edf9f1", "short": "NGO"},
    "community_member": {"emoji": "🏘️", "color": "#3d6f59", "bg": "#f3fbf4", "short": "Community Leader"},
    "informal_sector_worker": {"emoji": "♻️", "color": "#157347", "bg": "#edf9f0", "short": "Workers"},
}

_DEFAULT_ROLE = {"emoji": "👤", "color": "#475569", "bg": "#f8fafc", "short": "Role"}


def role_theme(role_id: str) -> Dict[str, str]:
    """Resolve a stakeholder's visual identity (never raises)."""
    return STAKEHOLDER_THEME.get(role_id, _DEFAULT_ROLE)


_EFFECTS_CSS = r"""
/* ===== Effects pack (claude_design/effects) ===== */
/* Background delivered as a fixed, behind-content layer (no overflow clip). */
.cx-bg-fx {
    position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden;
}
.cx-bg-grain {
    position: absolute; inset: 0; opacity: 0.30; mix-blend-mode: multiply;
    background-image:
        radial-gradient(circle at 1px 1px, rgba(72,66,43,0.05) 1px, transparent 1.5px),
        radial-gradient(circle at 3px 4px, rgba(72,66,43,0.04) 1px, transparent 1px);
    background-size: 6px 6px, 11px 9px;
}
.cx-bg-conveyor {
    position: absolute; left: 0; right: 0; bottom: 0; height: 80px; overflow: hidden;
    background: linear-gradient(180deg, transparent 0%, rgba(142,107,63,0.12) 100%);
}
.cx-bg-conveyor::before {
    content: ""; position: absolute; left: -10%; right: -10%; bottom: 0; height: 100%;
    background:
        radial-gradient(circle at 10% 90%, rgba(94,125,79,0.18) 0%, transparent 6%),
        radial-gradient(circle at 30% 88%, rgba(142,107,63,0.14) 0%, transparent 5%),
        radial-gradient(circle at 55% 92%, rgba(94,125,79,0.16) 0%, transparent 6%),
        radial-gradient(circle at 78% 87%, rgba(142,107,63,0.12) 0%, transparent 5%),
        radial-gradient(circle at 92% 91%, rgba(94,125,79,0.14) 0%, transparent 6%);
    animation: cxConveyor 40s linear infinite;
}
@keyframes cxConveyor { 0% { transform: translateX(0); } 100% { transform: translateX(-12%); } }
.cx-particle {
    position: absolute; bottom: -40px; width: 16px; height: 16px; opacity: 0;
    animation: cxFloatUp linear infinite; will-change: transform, opacity;
}
.cx-particle svg { display: block; width: 100%; height: 100%; }
@keyframes cxFloatUp {
    0%   { transform: translate(0,0) rotate(0); opacity: 0; }
    10%  { opacity: 0.6; }
    50%  { transform: translate(20px,-50vh) rotate(180deg); opacity: 0.7; }
    90%  { opacity: 0.45; }
    100% { transform: translate(-20px,-110vh) rotate(360deg); opacity: 0; }
}
.cx-sparkle {
    position: absolute; width: 6px; height: 6px; opacity: 0; border-radius: 50%;
    background:
        linear-gradient(45deg, transparent 40%, #fff7d4 50%, transparent 60%),
        linear-gradient(-45deg, transparent 40%, #fff7d4 50%, transparent 60%);
    box-shadow: 0 0 8px rgba(255,247,212,0.8);
    animation: cxTwinkle 4s ease-in-out infinite;
}
@keyframes cxTwinkle {
    0%,100% { opacity: 0; transform: scale(0.5); }
    50%     { opacity: 0.9; transform: scale(1.4); }
}
/* ---- Animation library (inert until a cx- class is applied) ---- */
@keyframes cxConfettiPop {
    0%  { opacity: 0; transform: translate(0,0) rotate(0) scale(0.2); }
    20% { opacity: 1; }
    100%{ opacity: 0; transform: translate(var(--dx),var(--dy)) rotate(var(--rot)) scale(1); }
}
.cx-confetti { position: relative; display: inline-block; width: 0; height: 0; }
.cx-confetti i {
    position: absolute; left: 0; top: 0; width: 8px; height: 14px; border-radius: 2px;
    animation: cxConfettiPop 1.2s cubic-bezier(.22,1,.36,1) forwards;
}
.cx-confetti i:nth-child(1)  { background:#3f6b3c; --dx:-60px;  --dy:-80px;  --rot:280deg; }
.cx-confetti i:nth-child(2)  { background:#c89c62; --dx:40px;   --dy:-100px; --rot:360deg; animation-delay:.04s; }
.cx-confetti i:nth-child(3)  { background:#5e7d4f; --dx:80px;   --dy:-60px;  --rot:200deg; animation-delay:.08s; }
.cx-confetti i:nth-child(4)  { background:#b76554; --dx:-90px;  --dy:-40px;  --rot:420deg; animation-delay:.02s; }
.cx-confetti i:nth-child(5)  { background:#8e6b3f; --dx:20px;   --dy:-120px; --rot:540deg; animation-delay:.06s; }
.cx-confetti i:nth-child(6)  { background:#157347; --dx:-30px;  --dy:-110px; --rot:320deg; animation-delay:.10s; }
.cx-confetti i:nth-child(7)  { background:#c89c62; --dx:100px;  --dy:-30px;  --rot:180deg; animation-delay:.12s; }
.cx-confetti i:nth-child(8)  { background:#3f6b3c; --dx:-110px; --dy:-90px;  --rot:460deg; animation-delay:.14s; }
.cx-confetti i:nth-child(9)  { background:#1f7a4c; --dx:60px;   --dy:-120px; --rot:600deg; animation-delay:.16s; }
.cx-confetti i:nth-child(10) { background:#245c4a; --dx:-70px;  --dy:-130px; --rot:240deg; animation-delay:.18s; }
.cx-confetti i:nth-child(11) { background:#c89c62; --dx:30px;   --dy:-70px;  --rot:380deg; animation-delay:.20s; }
.cx-confetti i:nth-child(12) { background:#5e7d4f; --dx:-50px;  --dy:-150px; --rot:720deg; animation-delay:.22s; }
@keyframes cxStampThump {
    0%  { transform: scale(2)    rotate(-12deg); opacity: 0; }
    50% { transform: scale(0.95) rotate(-6deg);  opacity: 1; }
    65% { transform: scale(1.05) rotate(-6deg);  opacity: 1; }
    100%{ transform: scale(1)    rotate(-6deg);  opacity: 1; }
}
.cx-stamp {
    display: inline-block; padding: 8px 16px; border: 3px solid #b76554;
    border-radius: 4px; color: #b76554; font-family: var(--font-display, Georgia, serif);
    font-size: 14px; font-weight: 700; letter-spacing: 0.18em; text-transform: uppercase;
    background: rgba(247,243,232,0.4);
    animation: cxStampThump 0.5s cubic-bezier(.34,1.56,.64,1) both;
}
.cx-stamp.green { border-color: #3f6b3c; color: #3f6b3c; }
@keyframes cxGlowPulse {
    0%,100% { box-shadow: 0 0 0 0 rgba(63,107,60,0.55), 0 8px 18px rgba(63,107,60,0.24); }
    50%     { box-shadow: 0 0 0 8px rgba(63,107,60,0),  0 12px 24px rgba(63,107,60,0.36); }
}
.cx-anim-glow { animation: cxGlowPulse 2s ease-in-out infinite; }
.cx-meter-shimmer { position: relative; overflow: hidden; }
.cx-meter-shimmer::after {
    content: ""; position: absolute; inset: 0; transform: translateX(-100%);
    background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.5) 50%, transparent 100%);
    animation: cxMeterShimmer 2.5s linear infinite;
}
@keyframes cxMeterShimmer { 0% { transform: translateX(-100%); } 100% { transform: translateX(200%); } }
@keyframes cxScreenShake {
    0%,100% { transform: translate(0,0); } 20% { transform: translate(4px,-2px); }
    40% { transform: translate(-5px,2px); } 60% { transform: translate(3px,2px); }
    80% { transform: translate(-2px,-1px); }
}
.cx-anim-shake { animation: cxScreenShake 0.55s cubic-bezier(.36,.07,.19,.97); }
@keyframes cxCardFlip {
    0%  { transform: perspective(800px) rotateY(180deg); opacity: 0; }
    60% { opacity: 1; }
    100%{ transform: perspective(800px) rotateY(0deg); opacity: 1; }
}
.cx-anim-flip { animation: cxCardFlip 0.8s cubic-bezier(.22,1,.36,1) both; }
@keyframes cxPopBubble {
    0%  { opacity: 0; transform: scale(0.4) translateY(8px); }
    60% { opacity: 1; transform: scale(1.08) translateY(0); }
    100%{ opacity: 1; transform: scale(1) translateY(0); }
}
.cx-anim-pop { animation: cxPopBubble 0.45s cubic-bezier(.34,1.56,.64,1) both; }
@keyframes cxLevelUp {
    0%  { opacity: 0; transform: translateY(20px) scale(0.7); }
    15% { opacity: 1; transform: translateY(0) scale(1.2); }
    30% { transform: translateY(0) scale(1); }
    70% { opacity: 1; }
    100%{ opacity: 0; transform: translateY(-30px) scale(1); }
}
.cx-level-up {
    font-family: var(--font-display, Georgia, serif); font-size: 32px; font-weight: 700;
    font-style: italic; color: #3f6b3c;
    text-shadow: 0 0 12px rgba(255,220,130,0.7), 0 4px 12px rgba(63,107,60,0.5);
    animation: cxLevelUp 2.2s ease-out forwards;
}
@media (prefers-reduced-motion: reduce) {
    .cx-bg-fx, .cx-particle, .cx-sparkle, .cx-bg-conveyor::before,
    .cx-anim-glow, .cx-meter-shimmer::after { animation: none !important; }
}
"""


def css() -> str:
    """Return the full global stylesheet (base theme + gamified additions)."""
    p = PALETTE
    # Web-font pairing from the City X design system (Newsreader / Public Sans /
    # JetBrains Mono). Built as one line via concatenation so no source line
    # exceeds the lint limit while the emitted @import stays a single statement.
    font_import = (
        '@import url("https://fonts.googleapis.com/css2?'
        'family=Newsreader:opsz,wght@6..72,400;6..72,600;6..72,700&'
        'family=Public+Sans:ital,wght@0,400;0,600;0,700;1,400&'
        'family=JetBrains+Mono:wght@400;600&display=swap");'
    )
    # Effects pack (claude_design/effects). Plain string (literal braces) so it
    # is injected verbatim into the f-string below without brace-escaping.
    # NOTE: the pack's .cx-bg-game uses overflow:hidden which would clip
    # Streamlit's scroll, so the background is delivered as a fixed,
    # behind-content .cx-bg-fx layer instead.
    effects_css = _EFFECTS_CSS
    return f"""
<style>
{font_import}
:root {{
    --wm-font-display: "Newsreader", Georgia, "Times New Roman", serif;
    --wm-font-body: "Public Sans", "Source Sans 3", system-ui,
        -apple-system, "Segoe UI", Roboto, sans-serif;
    --wm-font-mono: "JetBrains Mono", ui-monospace, "SF Mono", Menlo, monospace;
    --font-display: var(--wm-font-display);
    --font-body: var(--wm-font-body);
    --wm-olive-deep: {p['olive_deep']};
    --wm-olive: {p['olive']};
    --wm-sage: {p['sage']};
    --wm-stone: {p['stone']};
    --wm-paper: {p['paper']};
    --wm-kraft: {p['kraft']};
    --wm-charcoal: {p['charcoal']};
    --wm-cream: {p['cream']};
    --wm-danger: {p['danger']};
}}

/* --- App field: animated olive aurora over warm gradient --- */
.stApp {{
    position: relative;
    background:
        radial-gradient(ellipse at 50% 0%, rgba(255,253,225,0.60), transparent 55%),
        radial-gradient(circle at 88% 92%, rgba(120,170,95,0.30), transparent 55%),
        radial-gradient(circle at 8% 90%, rgba(150,196,110,0.24), transparent 50%),
        linear-gradient(145deg,
            #f6ef9e 0%, #e3ec85 28%, #c7e07a 52%,
            #aed47e 76%, #cfe78a 100%);
    background-size: 100% 100%, 100% 100%, 100% 100%, 300% 300%;
    animation: cxShades 30s ease-in-out infinite alternate;
}}
@keyframes cxShades {{
    0%   {{ background-position: 0 0, 0 0, 0 0, 0% 50%; }}
    50%  {{ background-position: 0 0, 0 0, 0 0, 100% 50%; }}
    100% {{ background-position: 0 0, 0 0, 0 0, 50% 100%; }}
}}
/* Aurora sits BEHIND content: absolute (not fixed) + negative z-index so it
   never overlays or clips Streamlit's scrollable view. */
.stApp::before,
.stApp::after {{
    content: ""; position: absolute; inset: 0; pointer-events: none; z-index: 0;
    background:
        radial-gradient(circle at 25% 65%, rgba(246,239,158,0.45), transparent 40%),
        radial-gradient(circle at 75% 35%, rgba(174,212,126,0.40), transparent 36%);
    filter: blur(28px);
    animation: cxAurora 17s ease-in-out infinite alternate;
}}
/* Outer wrappers stay transparent so the animated gradient shows around the
   content; the block-container is ONE big paper panel that holds all the
   text, so nothing floats and paragraphs share a single box. */
[data-testid="stAppViewContainer"], [data-testid="stMain"],
section.main, .main {{
    position: relative; z-index: 1; background: transparent !important;
}}
.block-container {{
    position: relative; z-index: 1;
    background: rgba(248,245,235,0.78) !important;
    border: 1px solid rgba(94,125,79,0.18);
    border-radius: 20px;
    padding: 22px 30px 34px !important;
    margin-top: 8px;
    box-shadow: 0 18px 40px rgba(72,66,43,0.10);
    backdrop-filter: blur(2px);
}}
/* The default Streamlit top bar reads as a solid black strip over the game;
   make it transparent so the aurora shows and it stops overlapping. */
header[data-testid="stHeader"], [data-testid="stHeader"],
[data-testid="stToolbar"] {{
    background: transparent !important; box-shadow: none !important;
}}
/* Our body-font override also hit Streamlit's Material icons, so the sidebar
   collapse control rendered the ligature text "keyboard_double_arrow_left".
   Restore the icon font on all Streamlit icon glyphs. */
[data-testid="stIconMaterial"], span[data-testid="stIconMaterial"],
[data-testid="stSidebarCollapseButton"] span,
[data-testid="baseButton-headerNoPadding"] span,
.material-icons, .material-symbols-rounded, .material-symbols-outlined {{
    font-family: "Material Symbols Rounded", "Material Symbols Outlined",
        "Material Icons" !important;
}}
/* Stop the "Draft proposal so far" expander / select dropdowns from
   overlapping neighbouring blocks. */
[data-testid="stExpander"] {{
    position: relative; z-index: 1; margin: 6px 0;
    background: rgba(247,243,232,0.6); border-radius: 12px;
}}
[data-testid="stExpander"] summary {{ position: relative; z-index: 1; }}
[data-baseweb="popover"], [data-baseweb="menu"] {{ z-index: 9999 !important; }}
/* All loose text lives on the single .block-container panel (above), so we
   do NOT add a second box per element. Widgets that already carry their own
   surface (buttons, inputs, alerts) keep it and must not be re-boxed. */
.block-container [data-testid="stMarkdownContainer"] {{ background: transparent; }}
/* Setup screen: dark olive control so the dropdown text reads white. */
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
    background: var(--wm-olive-deep) !important;
    border-color: var(--wm-olive-deep) !important;
}}
[data-testid="stSelectbox"] div[data-baseweb="select"] *,
[data-testid="stSelectbox"] div[data-baseweb="select"] svg {{
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    fill: #ffffff !important;
}}
.stApp::after {{
    background:
        radial-gradient(circle at 60% 80%, rgba(255,250,205,0.42), transparent 36%),
        radial-gradient(circle at 20% 30%, rgba(160,200,118,0.36), transparent 36%);
    animation-duration: 25s; animation-direction: alternate-reverse;
}}
@media (prefers-reduced-motion: reduce) {{
    .stApp, .stApp::before, .stApp::after {{ animation: none !important; }}
}}
.block-container {{ padding-top: 1rem !important; max-width: 1200px; position: relative; z-index: 1; }}

.stApp, .stApp p, .stApp li, .stApp label, .stApp span, .stApp div, .stApp small {{
    color: var(--wm-charcoal);
}}
.stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span {{ color: var(--wm-charcoal) !important; }}
.stApp, .stApp p, .stApp li, .stApp label, .stApp span, .stApp div, .stApp small,
.stMarkdown, [data-testid="stSidebar"] * {{ font-family: var(--wm-font-body); }}
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .round-hdr h3, .t-display {{
    font-family: var(--wm-font-display) !important; letter-spacing: -0.01em;
}}
code, kbd, pre, .t-mono {{ font-family: var(--wm-font-mono); }}
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, rgba(232,225,210,0.96) 0%, rgba(241,236,225,0.96) 100%);
    border-right: 1px solid rgba(94,125,79,0.16);
}}
[data-testid="stSidebar"] * {{ color: var(--wm-charcoal) !important; }}
[data-testid="stAlertContainer"], [data-testid="stAlertContainer"] * {{ color: var(--wm-charcoal) !important; }}
[data-testid="stAlertContainer"] > div {{
    border-radius: 14px !important;
    border: 1px solid rgba(94,125,79,0.14) !important;
    background: rgba(247,243,232,0.94) !important;
    box-shadow: 0 10px 24px rgba(72,66,43,0.07);
}}
[data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input {{
    color: var(--wm-charcoal) !important;
    -webkit-text-fill-color: var(--wm-charcoal) !important;
    background: rgba(247,243,232,0.95) !important;
    border-radius: 12px !important;
    border: 1px solid rgba(142,107,63,0.22) !important;
}}
[data-testid="stButton"] button {{
    border-radius: 999px !important;
    border: 1px solid rgba(94,125,79,0.18) !important;
    background: linear-gradient(180deg, #f5efe2 0%, #eadfcb 100%) !important;
    color: #4c402a !important;
    font-weight: 600 !important;
    box-shadow: 0 8px 20px rgba(72,66,43,0.08);
    transition: transform .12s ease, box-shadow .12s ease;
}}
[data-testid="stButton"] button:hover {{ transform: translateY(-1px); }}
[data-testid="stButton"] button[kind="primary"] {{
    background: linear-gradient(135deg, var(--wm-olive-deep) 0%, var(--wm-olive) 100%) !important;
    color: #fff !important;
    border-color: var(--wm-olive-deep) !important;
    box-shadow: 0 12px 26px rgba(63,107,60,0.24);
}}

/* --- SWM chrome bar (top of page, optional — render via components.chrome_bar()) --- */
.cx-chrome {{
    position: relative; z-index: 2;
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 18px; margin: 0 0 16px;
    gap: 16px;
}}
.cx-chrome-logo {{
    display: flex; align-items: center; gap: 10px;
    color: #2a2d26; text-decoration: none;
}}
.cx-chrome-logo .wordmark {{
    font-family: var(--wm-font-display);
    font-size: 22px; font-weight: 700; letter-spacing: -0.01em; line-height: 1;
    color: #2a2d26;
}}
.cx-chrome-logo .wordmark em {{ font-style: italic; color: #3f6b3c; }}
.cx-chrome-logo .tag {{
    font-size: 10.5px; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; color: #5b4a32; margin-top: 3px; display: block;
}}
.cx-chrome-right {{ display: flex; align-items: center; gap: 14px; font-size: 12.5px; color: #5b4a32; }}
.cx-chip {{
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 12px; border-radius: 999px;
    background: rgba(247,243,232,0.85); border: 1px solid rgba(142,107,63,0.22);
    font-weight: 600; font-size: 11.5px; color: #5b4a32;
    box-shadow: 0 4px 12px rgba(72,66,43,0.06);
}}
.cx-chip .dot {{
    width: 8px; height: 8px; border-radius: 50%;
    background: #3f6b3c; animation: cxDot 1.8s ease-out infinite;
}}

/* --- Transcript bubbles (now with inline avatar + typing dots) --- */
.msg-bubble {{
    border-radius: 14px; padding: 12px 15px; margin-bottom: 10px;
    border-left: 5px solid #92a07d; border: 1px solid rgba(94,125,79,0.10);
    background: rgba(247,243,232,0.92); color: var(--wm-charcoal);
    box-shadow: 0 10px 26px rgba(72,66,43,0.06);
    animation: wmFadeIn .35s ease both;
}}
.msg-human {{ background: linear-gradient(180deg,#efe8d7 0%,#faf7ef 100%); border-left-color: var(--wm-paper); }}
.msg-mod {{
    background: linear-gradient(180deg,#e4eadb 0%,#f4f5ee 100%);
    border-left-color: var(--wm-olive); text-align: left;
}}
.wm-bubble-row {{ display: flex; align-items: flex-start; gap: 12px; }}
.wm-bubble-av {{
    flex: 0 0 auto; width: 44px; height: 44px; border-radius: 50%;
    overflow: hidden; box-shadow: 0 6px 14px rgba(72,66,43,0.10);
}}
.wm-bubble-av svg {{ display: block; }}
.wm-mod-av {{
    background: linear-gradient(135deg, var(--wm-olive-deep), var(--wm-olive));
    color: #fff; display: grid; place-items: center; font-size: 22px;
    box-shadow: 0 6px 14px rgba(63,107,60,0.30);
}}
.wm-bubble-body {{ flex: 1; min-width: 0; }}
.wm-bubble-body b {{ font-size: .92rem; }}
.wm-bubble-text {{ margin-top: 4px; line-height: 1.5; font-size: .95rem; }}
.wm-typing {{ display: inline-flex; gap: 4px; align-items: center; padding: 4px 0; }}
.wm-typing span {{
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--dot-color, #5b4a32); opacity: .35;
    animation: wmTypingDot 1.2s ease-in-out infinite;
}}
.wm-typing span:nth-child(2) {{ animation-delay: .15s; }}
.wm-typing span:nth-child(3) {{ animation-delay: .3s; }}

/* --- Proposal / blueprint modules --- */
.proposal-box {{
    border: 1px solid rgba(142,107,63,0.15); border-radius: 16px; padding: 13px 15px;
    background: linear-gradient(180deg, rgba(242,235,220,0.96) 0%, rgba(248,243,232,0.96) 100%);
    margin-bottom: 12px; box-shadow: 0 14px 30px rgba(72,66,43,0.06);
    transition: border-color .4s ease, background .6s ease;
}}
.proposal-green {{
    border-left: 6px solid var(--wm-olive-deep);
    background: linear-gradient(180deg,#edf2e7 0%,#f6f7f1 100%);
    animation: wmSnap .5s ease both;
}}
.proposal-yellow {{
    border-left: 6px solid var(--wm-paper);
    background: linear-gradient(180deg,#f5ecd9 0%,#fbf7ed 100%);
}}
.proposal-red {{
    border-left: 6px solid var(--wm-danger);
    background: linear-gradient(180deg,#f5e8e3 0%,#fbf3ef 100%);
    animation: wmShake .45s ease both;
}}
.proposal-neutral {{
    border-left: 6px solid var(--wm-sage);
    background: linear-gradient(180deg,#f0eee7 0%,#f7f4ec 100%);
}}

/* --- Round header --- */
.round-hdr {{
    background: linear-gradient(135deg, rgba(74,80,66,0.98) 0%, rgba(94,125,79,0.98) 54%, rgba(126,145,101,0.98) 100%);
    color: #fff; border-radius: 18px; padding: 16px 20px; margin-bottom: 14px;
    box-shadow: 0 18px 34px rgba(28,64,46,0.18);
}}
.round-hdr h3, .round-hdr p, .round-hdr span, .round-hdr div {{ color: #fff !important; }}
.round-hdr h3 {{ margin: 0 0 2px 0; }}
.badge {{
    display: inline-block; border-radius: 999px; padding: 3px 10px; font-size: 12px;
    margin: 0 6px 4px 0; background: #e8dfcf; color: #5b4a32;
    border: 1px solid rgba(142,107,63,0.16);
}}

/* --- Game spine (waste-processing pipeline) --- */
.wm-spine {{
    display: flex; align-items: stretch; gap: 6px; margin: 4px 0 16px;
    padding: 10px 12px; border-radius: 16px;
    background: linear-gradient(180deg, rgba(244,239,228,0.9), rgba(236,229,214,0.9));
    border: 1px solid rgba(142,107,63,0.16); box-shadow: 0 10px 24px rgba(72,66,43,0.06);
}}
.wm-spine-step {{
    flex: 1; text-align: center; padding: 8px 6px; border-radius: 12px;
    font-size: .74rem; font-weight: 700; letter-spacing: .04em; text-transform: uppercase;
    color: #7c7666; background: rgba(255,255,255,0.35); position: relative;
    transition: all .4s ease;
}}
.wm-spine-step.done {{ color: var(--wm-olive-deep); background: rgba(63,107,60,0.10); }}
.wm-spine-step.active {{
    color: #fff; background: linear-gradient(135deg, var(--wm-olive-deep), var(--wm-olive));
    box-shadow: 0 8px 18px rgba(63,107,60,0.28); animation: wmPulse 2.4s ease-in-out infinite;
}}
.wm-spine-step .ico {{ display:block; font-size: 1.1rem; margin-bottom: 2px; }}
.wm-subtrack {{ display:flex; gap:6px; margin:-8px 0 14px; padding:0 4px; }}
.wm-module {{
    flex:1; font-size:.7rem; font-weight:700; text-align:center; padding:6px 4px;
    border-radius:10px; border:1px dashed rgba(142,107,63,0.3); color:#8a7d63;
    background:rgba(255,255,255,0.3); transition: all .4s ease;
}}
.wm-module.s-green {{
    color:#fff; border-style:solid; animation: wmSnap .5s ease both;
    background:linear-gradient(135deg,var(--wm-olive-deep),var(--wm-olive));
}}
.wm-module.s-yellow {{
    color:#6a5320; background:#f3e6cc;
    border-color:var(--wm-paper); border-style:solid;
}}
.wm-module.s-red {{ color:#fff; background:var(--wm-danger); border-style:solid; }}
.wm-module.s-active {{
    color:#fff; border-style:solid; animation: wmPulse 2s ease-in-out infinite;
    background:linear-gradient(135deg,#4a5042,#5e7d4f);
}}

/* --- Avatar roster + satisfaction meters --- */
.wm-roster {{ display:flex; flex-wrap:wrap; gap:10px; margin:6px 0 14px; }}
.wm-av-card {{
    flex:1 1 150px; min-width:140px; border-radius:16px; padding:10px;
    background:rgba(247,243,232,0.9); border:1px solid rgba(142,107,63,0.15);
    box-shadow:0 10px 22px rgba(72,66,43,0.06); text-align:center;
    transition: transform .25s ease, box-shadow .25s ease;
}}
.wm-av-card.speaking {{ transform: translateY(-4px) scale(1.02); box-shadow:0 16px 30px rgba(63,107,60,0.22); }}
.wm-av-name {{ font-weight:700; font-size:.86rem; margin-top:4px; }}
.wm-av-title {{ font-size:.7rem; color:#7c7666; }}
.wm-meter {{ height:8px; border-radius:999px; background:rgba(142,107,63,0.16); margin-top:7px; overflow:hidden; }}
.wm-meter > span {{
    display:block; height:100%; border-radius:999px;
    background:linear-gradient(90deg,var(--wm-olive),var(--wm-olive-deep));
    transition: width 1.1s cubic-bezier(.22,1,.36,1);
}}
.wm-meter.low > span {{ background:linear-gradient(90deg,#d8a25a,var(--wm-danger)); }}

/* --- City banner --- */
.wm-city {{
    border-radius:18px; overflow:hidden; margin-bottom:14px;
    border:1px solid rgba(142,107,63,0.18); box-shadow:0 14px 30px rgba(72,66,43,0.10);
}}
.wm-city svg {{ display:block; width:100%; height:auto; }}
.wm-city-cap {{
    font-size:.78rem; padding:6px 12px; color:#5b4a32;
    background:rgba(244,239,228,0.92); border-top:1px solid rgba(142,107,63,0.14);
}}

/* --- Vote tally board --- */
.wm-vote-row {{
    display:flex; align-items:center; gap:10px; padding:8px 12px; margin-bottom:8px;
    border-radius:14px; background:rgba(247,243,232,0.9); border:1px solid rgba(142,107,63,0.14);
    animation: wmVoteIn .5s ease both;
}}
.wm-pill {{ font-size:.72rem; font-weight:700; padding:3px 10px; border-radius:999px; color:#fff; }}
.wm-pill.v-green {{ background:var(--wm-olive-deep); }}
.wm-pill.v-yellow {{ background:var(--wm-paper); color:#5b4a32; }}
.wm-pill.v-neutral {{ background:var(--wm-sage); }}
.wm-pill.v-red {{ background:var(--wm-danger); }}

/* --- Earned badges --- */
.wm-badge-trophy {{
    display:inline-flex; align-items:center; gap:8px; padding:8px 14px; margin:0 8px 8px 0;
    border-radius:14px; font-weight:700; font-size:.84rem; color:#5b4a32;
    background:linear-gradient(180deg,#f6edd6,#ecdcbb); border:1px solid rgba(142,107,63,0.25);
    box-shadow:0 8px 18px rgba(72,66,43,0.10); animation: wmSnap .6s ease both;
}}

/* --- SWM hero logo (on setup screen) --- */
.cx-setup-hero {{ text-align: center; padding: 28px 0 16px; position: relative; }}
.cx-setup-hero img.logo {{
    width: 100%; max-width: 420px; height: auto; display: block; margin: 0 auto;
    filter: drop-shadow(0 6px 14px rgba(72, 66, 43, 0.08));
    animation: cxLogoIn 0.8s cubic-bezier(.22,1,.36,1) both;
}}

/* --- Keyframes --- */
@keyframes wmFadeIn {{ from {{ opacity:0; transform:translateY(6px); }} to {{ opacity:1; transform:none; }} }}
@keyframes wmSnap {{
    0% {{ opacity:0; transform:scale(.94); }}
    60% {{ transform:scale(1.03); }}
    100% {{ opacity:1; transform:scale(1); }}
}}
@keyframes wmShake {{
    0%,100% {{ transform:translateX(0); }}
    20% {{ transform:translateX(-5px); }} 40% {{ transform:translateX(5px); }}
    60% {{ transform:translateX(-3px); }} 80% {{ transform:translateX(3px); }}
}}
@keyframes wmPulse {{
    0%,100% {{ box-shadow:0 8px 18px rgba(63,107,60,0.28); }}
    50% {{ box-shadow:0 8px 26px rgba(63,107,60,0.45); }}
}}
@keyframes wmVoteIn {{ from {{ opacity:0; transform:translateX(-14px); }} to {{ opacity:1; transform:none; }} }}
@keyframes wmTypingDot {{
    0%, 60%, 100% {{ transform: translateY(0)   scale(.85); opacity: .35; }}
    30%           {{ transform: translateY(-4px) scale(1);   opacity: 1; }}
}}
@keyframes wmSpeakDot {{
    0%, 100% {{ transform: scale(1);   opacity: .4; }}
    50%      {{ transform: scale(1.5); opacity: .95; }}
}}
@keyframes cxAurora {{
    0%   {{ transform: translate(0, 0) scale(1);    opacity: 0.85; }}
    50%  {{ transform: translate(-3%, 2%) scale(1.06); opacity: 1; }}
    100% {{ transform: translate(2%, -3%) scale(0.98); opacity: 0.85; }}
}}
@keyframes cxLogoIn {{
    0%   {{ opacity: 0; transform: translateY(8px) scale(0.97); }}
    100% {{ opacity: 1; transform: translateY(0)   scale(1); }}
}}
@keyframes cxDot {{
    0%   {{ box-shadow: 0 0 0 0   rgba(63,107,60,0.55); }}
    70%  {{ box-shadow: 0 0 0 8px rgba(63,107,60,0); }}
    100% {{ box-shadow: 0 0 0 0   rgba(63,107,60,0); }}
}}
{effects_css}
</style>
"""
