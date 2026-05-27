import { THEME, contentTitle, roundedCard, text, statCard, brandBlock } from "./common.mjs";

async function icon(slide, ctx, name, left, top) {
  await ctx.addLucideIcon(slide, { icon: name, left, top, width: 88, height: 88, color: THEME.ink });
}

export async function slide02(presentation, ctx) {
  const slide = presentation.slides.add();
  contentTitle(slide, ctx, "AI project for SWM");
  brandBlock(slide, ctx, "horizontal");

  await icon(slide, ctx, "Recycle", 274, 258);
  await icon(slide, ctx, "UsersRound", 670, 258);
  await icon(slide, ctx, "BrainCircuit", 1070, 258);

  text(slide, ctx, 230, 414, 220, 30, "THE PROBLEM", { fontSize: 24, color: THEME.ink, bold: true, align: "center", typeface: "Aptos" });
  text(slide, ctx, 603, 414, 310, 30, "STAKEHOLDERS", { fontSize: 24, color: THEME.ink, bold: true, align: "center", typeface: "Aptos" });
  text(slide, ctx, 975, 414, 320, 30, "AI LEARNING GAP", { fontSize: 24, color: THEME.ink, bold: true, align: "center", typeface: "Aptos" });

  statCard(slide, ctx, 170, 500, 330, 224, THEME.green, "", "2 billion people lack reliable waste collection.\n\nMany cities in low- and middle-income contexts face landfill overflow, polluted water, public health risks, and fragmented service systems.", null);
  statCard(slide, ctx, 555, 500, 330, 224, THEME.green, "", "SWM decisions involve public authorities, private operators, informal workers, civil society, and affected communities. These actors have unequal power, conflicting incentives, and asymmetric information.", null);
  statCard(slide, ctx, 940, 500, 330, 224, THEME.green, "", "Role-play is a strong format for learning negotiation and systems thinking, but there are very few AI-supported educational tools for SWM.\n\nThis project addresses that gap.", null);
  return slide;
}
