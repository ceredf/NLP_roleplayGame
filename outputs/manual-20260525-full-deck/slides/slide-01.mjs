import { THEME, titleSlideBase } from "./common.mjs";

export async function slide01(presentation, ctx) {
  const slide = presentation.slides.add();
  titleSlideBase(
    slide,
    ctx,
    "AI Supported role\nplay for solid waste\nmanagement",
    "",
    "USI × Eawag / Sandec · May 2026 · Francesca Cereda, Luigi Marmolaro, & Sylvia Betteridge",
    {
      topline: "NLP FOR BUSINESS AND FINANCE PROJECT COURSE 2026",
      titleTop: 246,
      titleSize: 76,
      brand: "vertical",
    },
  );
  return slide;
}
