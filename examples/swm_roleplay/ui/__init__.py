"""Gamified presentation layer for the City X waste-management negotiation game.

This package is pure presentation: every function returns an HTML/SVG string or
small Streamlit render helper. It has no dependency on ``sdialog`` or the game
engine, so it can be unit-tested in isolation.

Modules:
- ``theme``: single source of truth for palette/stakeholder colors + global CSS.
- ``sprites``: parametric SVG avatar + City X skyline engine (swap point for
  illustrated art later — replace the body of ``sprites.avatar`` / ``sprites.city``).
- ``components``: composed game UI (pipeline spine, avatar roster, city banner,
  transcript bubbles, vote tally, outcome scorecard, badges).
"""
