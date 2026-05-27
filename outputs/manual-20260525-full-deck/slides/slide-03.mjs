import { THEME, contentTitle, bulletList, drawTreeCluster, footerNote } from "./common.mjs";

export async function slide03(presentation, ctx) {
  const slide = presentation.slides.add();
  contentTitle(slide, ctx, "Designing the game play", "GAME STRUCTURE");
  bulletList(slide, ctx, 132, 368, 700, [
    "Single-player negotiation role-play with AI-supported stakeholders",
    "Scenario based on anonymized realistic urban waste-management tensions",
    "6 stakeholders with distinct goals, leverage, hidden information, and constraints",
    "Player chooses one role and negotiates with the others",
    ["Three core phases", "Opening positions", "Proposal building and negotiation", "Final vote and educational debrief"],
  ], { height: 310, fontSize: 21 });
  drawTreeCluster(slide, ctx, 995, 112, 1.22);
  drawTreeCluster(slide, ctx, 1128, 300, 0.88);
  drawTreeCluster(slide, ctx, 1040, 470, 0.62);
  footerNote(slide, ctx, "The design goal is not only to simulate conversation, but to make tradeoffs, power asymmetries, and coalition-building visible.");
  return slide;
}
