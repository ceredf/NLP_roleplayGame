import { THEME, contentTitle, text, roundedCard, footerNote } from "./common.mjs";

function node(slide, ctx, left, top, width, height, accent, title, body) {
  roundedCard(slide, ctx, left, top, width, height, "#FFFDFC", THEME.line);
  roundedCard(slide, ctx, left, top, 12, height, accent, accent);
  text(slide, ctx, left + 24, top + 18, width - 36, 24, title, {
    fontSize: 22,
    bold: true,
    color: THEME.inkDark,
    typeface: "Aptos",
  });
  text(slide, ctx, left + 24, top + 52, width - 36, height - 68, body, {
    fontSize: 15,
    color: THEME.muted,
    typeface: "Aptos",
  });
}

export async function slide06(presentation, ctx) {
  const slide = presentation.slides.add();
  contentTitle(slide, ctx, "AI Structure", "SDIALOG TOOLKIT");
  bulletListBlock();

  function bulletListBlock() {
    text(slide, ctx, 132, 368, 430, 180, "• Foundation: Dialog / Turn / Event\n• Scenario: roleplay.py\n• Agents: agents.py + util.py\n• Engine: roleplay_engine.py\n• UI: Streamlit interface\n• Extensions: evaluation / audio / interpretability / orchestrators", {
      fontSize: 18,
      color: THEME.inkDark,
      typeface: "Aptos",
    });
  }

  node(slide, ctx, 705, 146, 220, 116, THEME.teal, "Foundation", "Dialog / Turn / Event hold transcript state, metadata, and events.");
  node(slide, ctx, 950, 146, 220, 116, THEME.orange, "Scenario", "roleplay.py loads scenario packs, hidden rules, and stakeholder definitions.");
  node(slide, ctx, 830, 294, 220, 126, THEME.red, "Agents", "agents.py wraps persona prompts around the selected model backend and manages AI stakeholder responses.");
  node(slide, ctx, 705, 454, 220, 126, THEME.green, "Engine", "roleplay_engine.py manages rounds, proposals, amendments, votes, and outcomes.");
  node(slide, ctx, 950, 454, 220, 126, THEME.teal, "UI", "Streamlit renders setup, negotiation screens, votes, outcomes, and transcript export.");

  roundedCard(slide, ctx, 760, 622, 470, 70, THEME.paper, THEME.line);
  text(slide, ctx, 782, 636, 420, 18, "Recommended cloud backend: vertexai:gemini-2.5-flash-lite", {
    fontSize: 18,
    color: THEME.inkDark,
    bold: true,
    typeface: "Aptos",
  });

  footerNote(slide, ctx, "Scenario data defines the world, agents generate stakeholder behavior, and the engine makes the negotiation progress in a controlled way.");
  return slide;
}
