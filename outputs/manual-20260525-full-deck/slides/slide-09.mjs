import { THEME, contentTitle, roundedCard, text, footerNote } from "./common.mjs";

function lane(slide, ctx, left, top, width, accent, label, title, bullets) {
  roundedCard(slide, ctx, left, top, width, 356, "#FFFDFC", THEME.line);
  roundedCard(slide, ctx, left + 20, top + 20, 94, 26, accent, accent);
  text(slide, ctx, left + 32, top + 25, 70, 14, label, { fontSize: 12, color: "#FFFFFF", bold: true, align: "center", typeface: "Aptos" });
  text(slide, ctx, left + 20, top + 64, width - 40, 56, title, { fontSize: 24, color: THEME.inkDark, bold: true, typeface: "Aptos" });
  text(slide, ctx, left + 20, top + 126, width - 40, 206, bullets.map((b) => `• ${b}`).join("\n"), { fontSize: 17, color: THEME.muted, typeface: "Aptos" });
}

export async function slide09(presentation, ctx) {
  const slide = presentation.slides.add();
  contentTitle(slide, ctx, "Next Steps");
  lane(slide, ctx, 92, 270, 360, THEME.green, "NOW", "Stabilize the live experience", [
    "Continue full-play testing with cloud AI",
    "Remove remaining UX friction in transitions and feedback",
    "Make backend and cloud status explicit inside the interface",
  ]);
  lane(slide, ctx, 500, 270, 360, THEME.teal, "NEXT", "Improve negotiation clarity", [
    "Improve agreement and disagreement visibility",
    "Make proposals reflect actual negotiated outcomes",
    "Simplify the opening interaction design",
    "Refine vote-readiness and satisfaction signals",
  ]);
  lane(slide, ctx, 908, 270, 360, THEME.orange, "LATER", "Prepare for scale and handoff", [
    "Add stronger documentation and limitations",
    "Prepare robust cloud deployment defaults",
    "Improve traceability, replay, and post-game analytics",
    "Package the game as a reusable educational artifact",
  ]);
  footerNote(slide, ctx, "The core loop works; the next phase is about turning a functioning prototype into a fluent learning experience.");
  return slide;
}
