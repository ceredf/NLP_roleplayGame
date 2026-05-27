import { THEME, box, brandBlock, text, roundedCard, footerNote } from "../../manual-20260525-full-deck/slides/common.mjs";

function stakeholderCard(slide, ctx, left, top, width, height, accent, title, role, lines) {
  roundedCard(slide, ctx, left, top, width, height, "#FFFDFC", THEME.line);
  roundedCard(slide, ctx, left, top, 12, height, accent, accent);
  text(slide, ctx, left + 24, top + 16, width - 36, 24, title, {
    fontSize: 21,
    color: THEME.inkDark,
    bold: true,
    typeface: "Aptos",
  });
  text(slide, ctx, left + 24, top + 42, width - 36, 18, role, {
    fontSize: 13,
    color: THEME.muted,
    typeface: "Aptos",
  });
  text(slide, ctx, left + 24, top + 68, width - 36, height - 82, lines.map((l) => `• ${l}`).join("\n"), {
    fontSize: 13,
    color: THEME.inkDark,
    typeface: "Aptos",
  });
}

export async function slide01(presentation, ctx) {
  const slide = presentation.slides.add();
  box(slide, ctx, 0, 0, ctx.W, ctx.H, THEME.bg);
  brandBlock(slide, ctx, "vertical");

  text(slide, ctx, 82, 76, 620, 62, "6 Stakeholders", {
    fontSize: 58,
    color: THEME.ink,
    display: true,
  });
  text(slide, ctx, 132, 142, 520, 28, "ROLE SCRIPTS OVERVIEW", {
    fontSize: 24,
    color: THEME.ink,
    typeface: "Aptos",
    bold: true,
  });
  text(slide, ctx, 82, 184, 1060, 22, "Each card captures what the stakeholder wants, the pressure they bring into the room, and the line they will defend if challenged.", {
    fontSize: 16,
    color: THEME.muted,
    typeface: "Aptos",
  });

  const cards = [
    ["#3A9A93", "National Government", "Urgency + political control", [
      "Restore waste operations quickly.",
      "Keep the deal politically defensible.",
      "Reject open-ended national liability.",
    ]],
    ["#3A9A93", "Municipal Government", "Operational realism", [
      "Demand implementable timelines.",
      "Push for named funding sources.",
      "Reject unfunded municipal obligations.",
    ]],
    ["#E0A340", "Private Sector Company", "Commercial viability", [
      "Push for a stable long-term framework.",
      "Defend predictability for investment.",
      "Reject liability for historic contamination.",
    ]],
    ["#E0A340", "NGO / Civil Society", "Monitoring + enforcement", [
      "Demand independent oversight.",
      "Insist on public reporting and escalation.",
      "Reject vague or symbolic commitments.",
    ]],
    ["#D65B54", "Community Leader", "Health + closure path", [
      "Demand protection and acknowledgement of harm.",
      "Insist on a real closure pathway.",
      "Reject compensation without safeguards.",
    ]],
    ["#D65B54", "Informal Sector Worker", "Livelihood protection", [
      "Defend worker recognition and inclusion.",
      "Demand concrete transition support.",
      "Reject modernization through exclusion.",
    ]],
  ];

  let i = 0;
  for (let row = 0; row < 3; row += 1) {
    for (let col = 0; col < 2; col += 1) {
      const left = 82 + col * 564;
      const top = 232 + row * 154;
      const [accent, title, role, lines] = cards[i];
      stakeholderCard(slide, ctx, left, top, 500, 126, accent, title, role, lines);
      i += 1;
    }
  }

  footerNote(slide, ctx, "Use this slide as a live facilitation aid: each stakeholder should repeat their core demand, defend their red line, and react to the proposal from their role perspective.");
  return slide;
}
