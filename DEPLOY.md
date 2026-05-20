# City X — Deployment package

A self-contained bundle to install and run the **City X gamified solid-waste
management negotiation game** built on the **SDialog** toolkit.

## What's in this folder

```
deploy/
├── DEPLOY.md                  ← you are here
├── README.md                  ← full SDialog project README
├── LICENSE                    ← MIT
├── pyproject.toml             ← package metadata (installable with pip)
├── requirements.txt           ← runtime Python dependencies
├── src/sdialog/               ← the SDialog framework + game engine
│   ├── agents.py · personas.py · base.py · …
│   ├── roleplay.py            ← scenario→persona→Agent builders
│   ├── roleplay_engine.py     ← runtime, rounds, voting, outcome
│   └── roleplay_cli.py        ← terminal version of the same game
└── examples/swm_roleplay/     ← the Streamlit web game
    ├── streamlit_app.py
    ├── city_x_scenario.json   ← public scenario data
    ├── city_x_game_rules.json ← hidden win thresholds
    ├── ui/                    ← theme · sprites · components
    └── assets/                ← logo + (optional) PNG avatar overrides
```

## Requirements
- Python **3.9+** (tested with 3.12).
- An LLM backend — either:
  - **Local (recommended for offline demo):** [Ollama](https://ollama.com)
    with a chat model pulled (default: `qwen2.5:latest`), or
  - **Hosted:** an API key for OpenAI / Anthropic / etc. exported in the
    shell before launch.

## Install (clean, isolated virtualenv)

```bash
cd deploy
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install . --no-deps --no-build-isolation
pip install streamlit
```

> **Why a venv?** Mixed Conda envs sometimes have a `numpy ≥ 2` while the
> bundled `scikit-learn` was built against `numpy < 1.x`, which throws a
> `numpy.dtype size changed` error at import. An isolated venv pins the
> right versions automatically.

## Run

```bash
# 1) Start the LLM backend (one of):
ollama serve &                # local, then in another shell:
ollama pull qwen2.5:latest

# or, hosted:
export OPENAI_API_KEY=sk-...

# 2) Launch the game (from the deploy/ folder, with the venv active):
.venv/bin/streamlit run examples/swm_roleplay/streamlit_app.py
```

Open the printed URL (default `http://localhost:8501`). At the setup screen
keep `ollama:qwen2.5:latest` or type another SDialog backend string
(e.g. `openai:gpt-4.1`).

## Architecture in one paragraph

The game runs on a **UI-agnostic engine** (`src/sdialog/roleplay.py` +
`roleplay_engine.py`) on top of the **SDialog** framework. Scenario content
is plain JSON (`city_x_scenario.json`) — public/private info structurally
separated. Hidden win rules live in a **separate** file
(`city_x_game_rules.json`) so stakeholder agents never see them. Five AI
stakeholders are built as SDialog `Agent`s (persona synthesized from the
scenario JSON) and the human plays one. The Streamlit layer
(`examples/swm_roleplay/streamlit_app.py` + the `ui/` package) is pure
presentation. At the end, a deterministic engine rule decides
pass/partial/fail by endorsement count, and a separate **LLM-as-judge**
grades each stakeholder's goal achievement against their hidden thresholds.

## Switching scenario or model

- **Scenario:** edit/replace `examples/swm_roleplay/city_x_scenario.json`
  (and `city_x_game_rules.json` for the win thresholds). The engine is
  unchanged.
- **Model:** the setup screen takes any SDialog backend string. Local
  Ollama is the default; for production demos a hosted model usually gives
  better stakeholder reasoning.

## Production notes / known caveats

- The Streamlit rerun model is handled in code with a **deferred-busy
  pattern** so AI generations don't double-render forms.
- Every agent call is **stateless** (persona kept, no growing dialog
  context) so longer games don't overflow the model context.
- If an agent returns nothing usable, a robust in-character fallback
  (built from that stakeholder's own requirements/red-lines) keeps the
  game playable.
- The game logs the full conversation as a standard SDialog `Dialog.json`,
  downloadable from the outcome screen — useful for evaluation and re-use.

## Optional: drop-in illustrated avatars

The 6 stakeholder avatars are generated SVGs by default. To swap in
illustrated art, drop PNGs into
`examples/swm_roleplay/assets/<role_id>/<expression>.png`
(expressions: `neutral`, `happy`, `concerned`, `angry`). See
`assets/PROMPTS.md` for the generation prompt sheet.
