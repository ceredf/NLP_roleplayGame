export const THEME = {
  bg: "#FBFAF7",
  paper: "#FFFDFC",
  ink: "#5D4037",
  inkDark: "#3F2B25",
  muted: "#7A6B66",
  green: "#3F7F3D",
  greenDark: "#2E6B32",
  greenSoft: "#E9F2E6",
  sage: "#EEF2EC",
  line: "#D8D0CB",
  sand: "#F2ECE7",
  orange: "#E0A340",
  red: "#D65B54",
  teal: "#3A9A93",
};

export function box(slide, ctx, left, top, width, height, fill, line = "#00000000", geometry = "rect") {
  return ctx.addShape(slide, {
    left,
    top,
    width,
    height,
    fill,
    line: ctx.line(line, line === "#00000000" ? 0 : 1),
    geometry,
  });
}

export function text(slide, ctx, left, top, width, height, value, opts = {}) {
  return ctx.addText(slide, {
    text: value,
    left,
    top,
    width,
    height,
    fontSize: opts.fontSize ?? 18,
    color: opts.color ?? THEME.ink,
    bold: opts.bold ?? false,
    typeface: opts.typeface ?? (opts.display ? ctx.fonts.title : ctx.fonts.body),
    align: opts.align ?? "left",
    valign: opts.valign ?? "top",
    fill: opts.fill ?? "#00000000",
    line: opts.line ?? ctx.line(),
    insets: opts.insets ?? { left: 0, right: 0, top: 0, bottom: 0 },
  });
}

export function brandBlock(slide, ctx, variant = "vertical") {
  if (variant === "horizontal") {
    box(slide, ctx, 1088, 50, 278, 84, THEME.green);
    text(slide, ctx, 1120, 62, 210, 28, "eawag", { fontSize: 44, color: "#FFFFFF", bold: true });
    text(slide, ctx, 1122, 104, 200, 16, "aquatic research", { fontSize: 14, color: "#FFFFFF" });
    return;
  }
  box(slide, ctx, 1260, 0, 140, 246, THEME.green, THEME.inkDark, "roundRect");
  box(slide, ctx, 1288, 24, 84, 84, "#FFFFFF", "#FFFFFF", "ellipse");
  text(slide, ctx, 1302, 46, 56, 36, "USI", { fontSize: 26, color: THEME.green, bold: true, align: "center" });
  text(slide, ctx, 1280, 174, 100, 28, "eawag", { fontSize: 34, color: "#FFFFFF", bold: true, align: "center" });
  text(slide, ctx, 1280, 204, 100, 16, "aquatic research", { fontSize: 11, color: "#FFFFFF", align: "center" });
}

export function titleSlideBase(slide, ctx, title, subtitle = "", footer = "", opts = {}) {
  box(slide, ctx, 0, 0, ctx.W, ctx.H, THEME.bg);
  brandBlock(slide, ctx, opts.brand ?? "vertical");
  if (opts.topline) {
    text(slide, ctx, 82, 84, 980, 22, opts.topline, {
      fontSize: 16,
      color: THEME.ink,
      bold: false,
      typeface: "Aptos",
      align: "left",
    });
  }
  text(slide, ctx, 82, opts.titleTop ?? 238, 1040, 170, title, {
    fontSize: opts.titleSize ?? 72,
    color: THEME.ink,
    display: true,
    bold: false,
  });
  if (subtitle) {
    text(slide, ctx, 130, opts.subtitleTop ?? 430, 720, 36, subtitle, {
      fontSize: 28,
      color: THEME.ink,
      bold: false,
      typeface: "Aptos",
      align: "left",
    });
  }
  if (footer) {
    text(slide, ctx, 82, 694, 980, 24, footer, { fontSize: 13, color: THEME.green, typeface: "Aptos" });
  }
}

export function sectionLabel(slide, ctx, left, top, label) {
  text(slide, ctx, left, top, 500, 26, label, {
    fontSize: 24,
    color: THEME.ink,
    typeface: "Aptos",
    bold: true,
  });
}

export function contentTitle(slide, ctx, title, subtitle = "") {
  box(slide, ctx, 0, 0, ctx.W, ctx.H, THEME.bg);
  brandBlock(slide, ctx, "vertical");
  text(slide, ctx, 82, 86, 900, 92, title, {
    fontSize: 66,
    color: THEME.ink,
    display: true,
  });
  if (subtitle) {
    text(slide, ctx, 132, 278, 520, 34, subtitle, {
      fontSize: 26,
      color: THEME.ink,
      typeface: "Aptos",
      bold: true,
    });
  }
}

export function bulletList(slide, ctx, left, top, width, bullets, opts = {}) {
  const body = bullets
    .map((item) => (Array.isArray(item)
      ? `• ${item[0]}\n   ${item.slice(1).map((s) => `◦ ${s}`).join("\n   ")}`
      : `• ${item}`))
    .join("\n");
  text(slide, ctx, left, top, width, opts.height ?? 280, body, {
    fontSize: opts.fontSize ?? 19,
    color: opts.color ?? THEME.inkDark,
    typeface: "Aptos",
  });
}

export function roundedCard(slide, ctx, left, top, width, height, fill = THEME.paper, line = THEME.line) {
  return box(slide, ctx, left, top, width, height, fill, line, "roundRect");
}

export function statCard(slide, ctx, left, top, width, height, accent, title, body, icon) {
  roundedCard(slide, ctx, left, top, width, height, THEME.green, THEME.greenDark);
  if (icon) {
    ctx.addLucideIcon(slide, { icon, left: left + width / 2 - 32, top: top - 124, width: 64, height: 64, color: THEME.ink });
  }
  text(slide, ctx, left + 20, top + 18, width - 40, 30, title, {
    fontSize: 26,
    color: "#FFFFFF",
    bold: true,
    typeface: "Aptos",
    align: "center",
  });
  text(slide, ctx, left + 26, top + 60, width - 52, height - 80, body, {
    fontSize: 17,
    color: "#FFFFFF",
    typeface: "Aptos",
  });
}

export function drawTreeCluster(slide, ctx, originX, originY, scale = 1) {
  const trunk = THEME.ink;
  box(slide, ctx, originX + 108 * scale, originY + 120 * scale, 24 * scale, 150 * scale, "#9A5B28");
  box(slide, ctx, originX + 0, originY + 0, 150 * scale, 110 * scale, "#4FAE5E", "#00000000", "hexagon");
  box(slide, ctx, originX + 120 * scale, originY + 100 * scale, 150 * scale, 110 * scale, "#248936", "#00000000", "hexagon");
  box(slide, ctx, originX + 80 * scale, originY + 205 * scale, 95 * scale, 70 * scale, "#3AA44A", "#00000000", "hexagon");
  box(slide, ctx, originX + 90 * scale, originY + 98 * scale, 18 * scale, 120 * scale, "#9A5B28");
  box(slide, ctx, originX + 134 * scale, originY + 168 * scale, 120 * scale, 18 * scale, "#C67E36");
}

export function footerNote(slide, ctx, note) {
  text(slide, ctx, 82, 682, 1100, 20, note, {
    fontSize: 13,
    color: THEME.muted,
    typeface: "Aptos",
  });
}
