import { THEME, contentTitle, roundedCard, text, footerNote } from "./common.mjs";

function evalCard(slide, ctx, left, top, width, title, bullets, accent) {
  roundedCard(slide, ctx, left, top, width, 328, "#FFFDFC", THEME.line);
  roundedCard(slide, ctx, left, top, width, 12, accent, accent);
  text(slide, ctx, left + 22, top + 24, width - 44, 26, title, {
    fontSize: 24,
    color: THEME.inkDark,
    bold: true,
    typeface: "Aptos",
  });
  text(slide, ctx, left + 22, top + 72, width - 44, 226, bullets.map((b) => `• ${b}`).join("\n"), {
    fontSize: 17,
    color: THEME.muted,
    typeface: "Aptos",
  });
}

export async function slide08(presentation, ctx) {
  const slide = presentation.slides.add();
  contentTitle(slide, ctx, "Evaluation");
  evalCard(slide, ctx, 92, 286, 380, "Technical reliability", [
    "End-to-end playthrough stability",
    "Robust handling of malformed model outputs",
    "Repeatable multi-run smoke tests with cloud AI",
  ], THEME.teal);
  evalCard(slide, ctx, 530, 286, 380, "Negotiation quality", [
    "Coherence of stakeholder behavior",
    "Proposal relevance to stakeholder positions",
    "Visible agreement and disagreement dynamics",
    "Credibility of voting and outcomes",
  ], THEME.orange);
  evalCard(slide, ctx, 968, 286, 320, "Educational value", [
    "Makes tradeoffs legible",
    "Encourages perspective-taking",
    "Shows how governance, private incentives, and community concerns interact",
  ], THEME.red);
  footerNote(slide, ctx, "Evaluation should measure not only model output quality, but whether the game teaches negotiation under real-world constraints.");
  return slide;
}
