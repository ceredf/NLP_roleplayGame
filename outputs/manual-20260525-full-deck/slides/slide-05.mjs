import { THEME, roundedCard, text, footerNote, box, brandBlock } from "./common.mjs";

function stakeholderCard(slide, ctx, left, top, width, height, accent, title, body) {
  roundedCard(slide, ctx, left, top, width, height, "#FFFDFC", THEME.line);
  roundedCard(slide, ctx, left, top, 14, height, accent, accent);
  text(slide, ctx, left + 28, top + 22, width - 40, 28, title, {
    fontSize: 23,
    color: THEME.inkDark,
    bold: true,
    typeface: "Aptos",
  });
  text(slide, ctx, left + 28, top + 66, width - 48, height - 84, body, {
    fontSize: 16,
    color: THEME.muted,
    typeface: "Aptos",
  });
}

export async function slide05(presentation, ctx) {
  const slide = presentation.slides.add();
  box(slide, ctx, 0, 0, ctx.W, ctx.H, THEME.bg);
  brandBlock(slide, ctx, "vertical");
  text(slide, ctx, 82, 82, 960, 72, "Stakeholder roles and\nnegotiation logic", {
    fontSize: 56,
    color: THEME.ink,
    display: true,
  });
  text(slide, ctx, 82, 166, 1100, 24, "Each role combines public position, private constraints, leverage, and red lines.", {
    fontSize: 18,
    color: THEME.muted,
    typeface: "Aptos",
  });

  const cards = [
    [THEME.teal, "National Government", "Long-term infrastructure logic, budget framing, and policy legitimacy."],
    [THEME.teal, "Municipal Government", "Local implementation pressure, service continuity, and political accountability."],
    [THEME.orange, "Private Sector", "Operational efficiency, contract incentives, and control over recyclables."],
    [THEME.orange, "NGO / Civil Society", "Environmental justice, transparency, and public-interest pressure."],
    [THEME.red, "Community Leader", "Resident wellbeing, local legitimacy, and trust-building across the table."],
    [THEME.red, "Informal Sector Worker", "Livelihood protection, access to materials, and exclusion risk."],
  ];

  let i = 0;
  for (let row = 0; row < 3; row += 1) {
    for (let col = 0; col < 2; col += 1) {
      const left = 82 + col * 690;
      const top = 222 + row * 154;
      const [accent, title, body] = cards[i];
      stakeholderCard(slide, ctx, left, top, 610, 126, accent, title, body);
      i += 1;
    }
  }

  footerNote(slide, ctx, "Each stakeholder is designed with a public role card plus hidden information that shapes negotiation behavior.");
  return slide;
}
