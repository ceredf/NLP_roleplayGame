const COLORS = {
  bg: "#FCFCFD",
  ink: "#101828",
  muted: "#475467",
  border: "#D0D5DD",
  blue: "#2563EB",
  blueSoft: "#E0EAFF",
  teal: "#0F766E",
  tealSoft: "#D1FAE5",
  violet: "#7C3AED",
  violetSoft: "#EDE9FE",
  rose: "#BE185D",
  roseSoft: "#FCE7F3",
  amber: "#B45309",
  amberSoft: "#FEF3C7",
  slate: "#344054",
  white: "#FFFFFF",
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

function moduleCard(slide, ctx, left, top, width, height, accent, soft, title, subtitle, bullets) {
  box(slide, ctx, left, top, width, height, COLORS.white, COLORS.border);
  box(slide, ctx, left, top, 10, height, accent);
  box(slide, ctx, left + 26, top + 18, 112, 24, soft);
  text(slide, ctx, left + 34, top + 23, 96, 14, title.toUpperCase(), {
    fontSize: 11,
    bold: true,
    color: accent,
    align: "center",
  });
  text(slide, ctx, left + 26, top + 54, width - 52, 32, subtitle, {
    fontSize: 20,
    bold: true,
    color: COLORS.slate,
  });
  text(slide, ctx, left + 26, top + 96, width - 52, height - 110, bullets.map((b) => `• ${b}`).join("\n"), {
    fontSize: 15,
    color: COLORS.muted,
  });
}

function connector(slide, ctx, left, top, width, label) {
  box(slide, ctx, left, top, width, 4, "#CBD5E1");
  text(slide, ctx, left + width / 2 - 28, top - 18, 56, 16, label, {
    fontSize: 11,
    bold: true,
    color: "#667085",
    align: "center",
  });
}

export async function slide02(presentation, ctx) {
  const slide = presentation.slides.add();

  box(slide, ctx, 0, 0, ctx.W, ctx.H, COLORS.bg);
  text(slide, ctx, 72, 58, 700, 42, "How The `sdialog` Stack Works", {
    fontSize: 30,
    bold: true,
    color: COLORS.ink,
  });
  text(slide, ctx, 72, 108, 900, 34, "The negotiation game layers scenario data, persona-driven agents, and a deterministic game engine on top of a shared dialog transcript.", {
    fontSize: 17,
    color: COLORS.muted,
  });

  moduleCard(
    slide,
    ctx,
    72,
    188,
    250,
    202,
    COLORS.blue,
    COLORS.blueSoft,
    "Foundation",
    "Dialog / Turn / Event",
    [
      "Core pydantic data structures in `sdialog.__init__`.",
      "Hold transcript, metadata, and event history.",
      "Everything else reads from or writes to this shared conversation state.",
    ],
  );

  moduleCard(
    slide,
    ctx,
    360,
    188,
    250,
    202,
    COLORS.teal,
    COLORS.tealSoft,
    "Scenario",
    "roleplay.py",
    [
      "Loads scenario JSON, hidden rules, and stakeholder definitions.",
      "Builds role cards, private goals, and the session setup.",
      "Decides which roles are human and which roles are AI-controlled.",
    ],
  );

  moduleCard(
    slide,
    ctx,
    648,
    188,
    250,
    202,
    COLORS.violet,
    COLORS.violetSoft,
    "Agents",
    "agents.py + util.py",
    [
      "Wrap persona prompts around the selected model backend.",
      "Maintain conversation memory and call the LLM for each AI stakeholder.",
      "Can use Vertex AI, Gemini API, Ollama, or other configured backends.",
    ],
  );

  moduleCard(
    slide,
    ctx,
    936,
    188,
    272,
    202,
    COLORS.rose,
    COLORS.roseSoft,
    "Engine",
    "roleplay_engine.py",
    [
      "Runs rounds, turn order, proposal state, voting, and outcomes.",
      "Tracks stakeholder satisfaction, proposal versions, and negotiations.",
      "Provides the deterministic game contract the UI uses.",
    ],
  );

  connector(slide, ctx, 322, 286, 38, "feeds");
  connector(slide, ctx, 610, 286, 38, "spawns");
  connector(slide, ctx, 898, 286, 38, "drives");

  moduleCard(
    slide,
    ctx,
    72,
    448,
    536,
    178,
    COLORS.amber,
    COLORS.amberSoft,
    "UI Layer",
    "streamlit_app.py",
    [
      "Renders setup, round transitions, amendment inputs, flags, votes, and outcome screens.",
      "Translates button clicks into engine actions and agent calls.",
      "Shows the proposal, transcript, satisfaction, and downloadable JSON for the user.",
    ],
  );

  moduleCard(
    slide,
    ctx,
    648,
    448,
    560,
    178,
    "#1D4ED8",
    "#DBEAFE",
    "Extension Layers",
    "evaluation / audio / interpretability / orchestrators",
    [
      "Evaluation scores quality and consistency.",
      "Audio supports speech and room-style interaction paths.",
      "Interpretability inspects or steers model behavior.",
      "Orchestrators inject extra rules or dynamic instructions into the dialogue loop.",
    ],
  );

  text(slide, ctx, 72, 656, 980, 24, "In short: scenario data defines the world, agents generate stakeholder behavior, and the engine makes the negotiation progress in a controlled way.", {
    fontSize: 15,
    color: COLORS.slate,
    bold: true,
  });

  return slide;
}
