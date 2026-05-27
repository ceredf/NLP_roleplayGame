const COLORS = {
  bg: "#F6F7FB",
  ink: "#101828",
  muted: "#475467",
  border: "#D0D5DD",
  blue: "#2563EB",
  blueSoft: "#DBEAFE",
  teal: "#0F766E",
  tealSoft: "#CCFBF1",
  amber: "#B45309",
  amberSoft: "#FEF3C7",
  white: "#FFFFFF",
  slate: "#344054",
};

function box(slide, ctx, left, top, width, height, fill, line = "#00000000") {
  return ctx.addShape(slide, {
    left,
    top,
    width,
    height,
    fill,
    line: ctx.line({ color: line, width: 1 }),
    geometry: "rect",
  });
}

function text(slide, ctx, left, top, width, height, value, opts = {}) {
  return ctx.addText(slide, {
    text: value,
    left,
    top,
    width,
    height,
    fontSize: opts.fontSize ?? 18,
    color: opts.color ?? COLORS.ink,
    bold: opts.bold ?? false,
    typeface: opts.typeface ?? "Aptos",
    align: opts.align ?? "left",
    valign: opts.valign ?? "top",
    fill: opts.fill ?? "#00000000",
    line: opts.line ?? ctx.line(),
    insets: opts.insets ?? { left: 0, right: 0, top: 0, bottom: 0 },
  });
}

function pillar(slide, ctx, left, top, width, height, accent, accentSoft, title, body, bullets) {
  box(slide, ctx, left, top, width, height, COLORS.white, COLORS.border);
  box(slide, ctx, left, top, width, 8, accent);
  box(slide, ctx, left + 20, top + 24, 110, 28, accentSoft);
  text(slide, ctx, left + 32, top + 29, 90, 18, title.toUpperCase(), {
    fontSize: 12,
    bold: true,
    color: accent,
    align: "center",
  });
  text(slide, ctx, left + 20, top + 68, width - 40, 62, body, {
    fontSize: 22,
    bold: true,
    color: COLORS.slate,
  });
  text(slide, ctx, left + 20, top + 150, width - 40, height - 170, bullets.map((b) => `• ${b}`).join("\n"), {
    fontSize: 18,
    color: COLORS.muted,
  });
}

export async function slide01(presentation, ctx) {
  const slide = presentation.slides.add();

  box(slide, ctx, 0, 0, ctx.W, ctx.H, COLORS.bg);
  box(slide, ctx, 72, 52, 250, 32, COLORS.blueSoft);
  text(slide, ctx, 92, 59, 210, 18, "City X Negotiation Game", {
    fontSize: 13,
    bold: true,
    color: COLORS.blue,
    align: "center",
  });

  text(slide, ctx, 72, 104, 820, 58, "Next Steps To Make The Game Fluent And Presentation-Ready", {
    fontSize: 30,
    bold: true,
    color: COLORS.ink,
  });
  text(slide, ctx, 72, 168, 980, 42, "The core loop is playable. The next phase is about making negotiation clearer, faster to follow, and more credible round by round.", {
    fontSize: 18,
    color: COLORS.muted,
  });

  pillar(
    slide,
    ctx,
    72,
    242,
    350,
    376,
    COLORS.blue,
    COLORS.blueSoft,
    "Now",
    "Stabilize the live play experience",
    [
      "Replay the full game several times with Vertex AI and capture any edge-case failures.",
      "Tighten round transitions so every click has a clear visible result.",
      "Add a visible cloud-status badge so users know AI responses are coming from Vertex AI.",
      "Polish the setup and final screens so nothing feels broken or unfinished.",
    ],
  );

  pillar(
    slide,
    ctx,
    465,
    242,
    350,
    376,
    COLORS.teal,
    COLORS.tealSoft,
    "Next",
    "Improve negotiation quality and clarity",
    [
      "Simplify the opening round into a cleaner first move instead of fragmented prompts.",
      "Make agreement and disagreement explicit after each proposal change.",
      "Improve the proposal draft so it reflects what the table actually converged on.",
      "Refine satisfaction, vote readiness, and round summaries to feel more intuitive.",
    ],
  );

  pillar(
    slide,
    ctx,
    858,
    242,
    350,
    376,
    COLORS.amber,
    COLORS.amberSoft,
    "Later",
    "Prepare the project for demos and handoff",
    [
      "Document limitations, scenario logic, and the expected model/backend configuration.",
      "Add analytics or exported traces so negotiations can be reviewed afterwards.",
      "Finalize deployment defaults for cloud-hosted play when the local experience is stable.",
      "Package the game as a polished teaching/demo artifact for class or stakeholder use.",
    ],
  );

  text(slide, ctx, 72, 650, 760, 26, "Recommended working default: vertexai:gemini-2.5-flash-lite for fast iteration and repeated playthroughs.", {
    fontSize: 15,
    color: COLORS.slate,
    bold: true,
  });

  return slide;
}
