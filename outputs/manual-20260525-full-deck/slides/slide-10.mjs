import { THEME, titleSlideBase, box, text } from "./common.mjs";

function canopy(slide, ctx, left, top, width, height, fill) {
  box(slide, ctx, left, top, width, height, fill, "#00000000", "ellipse");
}

export async function slide10(presentation, ctx) {
  const slide = presentation.slides.add();
  titleSlideBase(slide, ctx, "Thank you\nvery\nmuch!", "", "", {
    titleTop: 174,
    titleSize: 82,
  });

  box(slide, ctx, 864, 82, 430, 578, "#294A32", "#294A32", "roundRect");
  box(slide, ctx, 878, 96, 402, 550, "#1B3525", "#1B3525", "roundRect");
  canopy(slide, ctx, 908, 116, 130, 104, "#7D8E63");
  canopy(slide, ctx, 1016, 128, 156, 118, "#5E6E52");
  canopy(slide, ctx, 1132, 160, 108, 88, "#D6C39A");
  canopy(slide, ctx, 960, 254, 164, 126, "#566B52");
  canopy(slide, ctx, 1118, 264, 130, 102, "#A9A16B");
  canopy(slide, ctx, 1020, 384, 178, 136, "#4B5B46");
  canopy(slide, ctx, 1146, 420, 88, 72, "#B97F42");
  canopy(slide, ctx, 902, 492, 144, 110, "#465C4B");
  canopy(slide, ctx, 1048, 516, 170, 120, "#7E855B");
  text(slide, ctx, 882, 664, 360, 18, "Questions and discussion", { fontSize: 18, color: "#E6E1D6", typeface: "Aptos" });
  return slide;
}
