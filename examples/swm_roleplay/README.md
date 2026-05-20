# SWM Role-Play Scenario Pack

This folder contains a first-pass scenario-pack format for the SWM negotiation game.

The goal of the format is to keep the game engine fixed while allowing scenario content to be swapped in as JSON. A scenario pack should be plain data: no code, no prompt templates that depend on implementation details, and no hidden logic outside the file.

## Design Principles

- Keep the pack serializable so it can be stored directly in `Dialog.scenario`.
- Separate engine rules from scenario content.
- Distinguish public information from stakeholder-private information.
- Make proposal evaluation machine-readable.
- Keep room for both single-player and multiplayer use.

## Top-Level Structure

- `schema_version`: version for the scenario-pack format.
- `scenario_id`: stable identifier for the pack.
- `title`: human-readable scenario name.
- `summary`: short description for game lobbies or menus.
- `setting`: time, location, and domain metadata.
- `narrative`: public crisis framing shown to all players.
- `engine`: scenario-specific round timing and mechanics overrides.
- `proposal_dimensions`: the required dimensions every final plan must address.
- `stakeholders`: the role definitions used to create player cards and AI personas.
- `events`: surprise events that can be injected during negotiation.
- `critical_failure`: rules that immediately collapse the negotiation.
- `debrief`: prompts for post-game reflection and analysis.
- `sources`: traceability for the real-world evidence behind the fictionalized scenario.

Hidden win / scoring rules should live in a separate game-rules JSON file so stakeholder agents do not see them as part of the public scenario content.

## Stakeholder Structure

Each stakeholder should contain:

- `id`: stable machine-readable key.
- `display_name`: role label shown in the interface.
- `iswm_category`: governance category.
- `playable`: whether a human can directly play the role.
- `ai_default`: whether AI should auto-fill the role in solo play.
- `public_profile`: role-card information visible to the player.
- `private_info`: hidden information only that role starts with.
- `negotiation`: structured constraints for voting and bargaining.
- `behavior`: hints for persona construction and orchestrator rules.

## Proposal Evaluation Structure

Each stakeholder has:

- `minimum_requirements`: what must be addressed before they can endorse.
- `preferred_gains`: what they want but can trade away.
- `red_lines`: what they will not accept.
- `batna`: what happens if the negotiation fails.

This is intended to support both:

- hard game logic, such as blocking endorsement when red lines are violated
- softer LLM-judge evaluation, such as "fully satisfied", "partially satisfied", or "unsatisfied"

## Implementation Notes

- The engine can load this JSON and pass it through as the `scenario=` metadata in `sdialog`.
- The `behavior` block is designed to map cleanly to `Persona` fields plus `SimpleReflexOrchestrator` rules.
- `events[*].effects` is descriptive data for now; later we can compile it into moderator instructions and stakeholder-specific steering.

## First Example

See [city_x_scenario.json](/Users/gigi/Desktop/sdialog-main/examples/swm_roleplay/city_x_scenario.json).
