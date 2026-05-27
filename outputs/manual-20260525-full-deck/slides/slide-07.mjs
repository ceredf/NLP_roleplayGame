import { THEME, contentTitle, text, roundedCard, footerNote } from "./common.mjs";

function flowStep(slide, ctx, left, top, width, title, body, number) {
  roundedCard(slide, ctx, left, top, width, 142, THEME.paper, THEME.line);
  roundedCard(slide, ctx, left + 18, top + 18, 42, 42, THEME.green, THEME.green);
  text(slide, ctx, left + 18, top + 26, 42, 18, String(number), { fontSize: 20, color: "#FFFFFF", bold: true, align: "center", typeface: "Aptos" });
  text(slide, ctx, left + 76, top + 18, width - 94, 26, title, { fontSize: 22, color: THEME.inkDark, bold: true, typeface: "Aptos" });
  text(slide, ctx, left + 76, top + 52, width - 94, 74, body, { fontSize: 15, color: THEME.muted, typeface: "Aptos" });
}

export async function slide07(presentation, ctx) {
  const slide = presentation.slides.add();
  contentTitle(slide, ctx, "The game now", "CURRENT PLAYABLE FLOW");

  flowStep(slide, ctx, 92, 332, 380, "Setup and role selection", "The player chooses a stakeholder and the default cloud-backed AI model.", 1);
  flowStep(slide, ctx, 520, 332, 380, "Role reveal and private briefing", "The selected role card exposes goals, constraints, and negotiation posture.", 2);
  flowStep(slide, ctx, 948, 332, 380, "Opening statements", "Each stakeholder sets an initial position and establishes bargaining tone.", 3);
  flowStep(slide, ctx, 92, 510, 380, "Proposal building", "Actors negotiate dimensions, suggest amendments, and react to changes.", 4);
  flowStep(slide, ctx, 520, 510, 380, "Final vote", "Support or resistance becomes explicit once a near-final proposal exists.", 5);
  flowStep(slide, ctx, 948, 510, 380, "Outcome and debrief", "The game resolves the outcome and exports a structured negotiation trace.", 6);

  footerNote(slide, ctx, "The game is now playable end-to-end with cloud AI calls; the current focus is fluency, clarity, and educational quality.");
  return slide;
}
