import { titleSlideBase } from "./common.mjs";

export async function slide04(presentation, ctx) {
  const slide = presentation.slides.add();
  titleSlideBase(slide, ctx, "6 Stakeholders", "ROLE DESIGN", "", {
    titleTop: 176,
    titleSize: 74,
    subtitleTop: 276,
  });
  return slide;
}
