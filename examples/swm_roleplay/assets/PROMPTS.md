# City X — Stakeholder Avatar Art Prompts

These prompts produce the **illustrated avatars** the game uses (pipeline "a").

## How it wires in

- Save each image as: `assets/<role_id>/<expression>.png`
- 6 characters × 4 expressions = **24 images**
- Expressions: `neutral`, `happy`, `concerned`, `angry`
- The 7 runtime reaction states map onto these automatically
  (`idle`/`speaking` → neutral, `approve`/`endorse` → happy,
  `wary`/`walkout` → concerned, `block` → angry).
- If a file is missing, the app falls back to the generated SVG avatar — so
  you can add art incrementally and the game keeps working.

Example final layout:

```
assets/
  national_government/   neutral.png  happy.png  concerned.png  angry.png
  municipal_government/   ...
  private_sector_company/ ...
  ngo_civil_society/      ...
  community_member/       ...
  informal_sector_worker/ ...
```

## Generation settings (for visual consistency)

- **Square 1:1**, render at **768×768** or larger, export final PNG.
- Head-and-shoulders **bust**, centred, facing viewer, consistent scale/crop
  across all 24 images.
- **Background:** solid warm cream `#f7f3e8` (the game crops to a circle).
- **Keep the same character** across that character's 4 expressions — reuse the
  same seed, or use a character-reference / img2img from the `neutral` image so
  only the facial expression changes.
- **No text, no logos, no watermarks.**

## Shared style preamble (prepend to every prompt)

> Flat editorial vector illustration, warm and grounded, environmental-civic
> theme. Muted olive, kraft-brown and recycled-paper palette. Soft even studio
> lighting, gentle shading, clean rounded shapes, dignified and respectful
> character design (not caricatured). Head-and-shoulders bust, centred,
> front-facing, solid cream `#f7f3e8` background, square composition, no text.

## Per-character subject (City X landfill-crisis negotiation cast)

| role_id | Subject (accent color) |
|---|---|
| `national_government` | A composed senior official from the Ministry of Urban Development, formal dark **deep-green** suit and tie, authoritative and measured. Accent `#245c4a`. |
| `municipal_government` | A practical mid-career municipal director of Environment & Infrastructure, smart-casual **teal-green** blazer, slightly overworked but steady. Accent `#2f6f5e`. |
| `private_sector_company` | A polished corporate Chief Development Officer of a waste-management firm, tailored **bronze/khaki** business attire, confident, persuasive. Accent `#7a5a1f`. |
| `ngo_civil_society` | An environmental-watchdog NGO director, earthy **leaf-green** field jacket, principled and intense, lanyard. Accent `#1f7a4c`. |
| `community_member` | A weathered, resilient host-community resident from Eastfield village, simple **forest-green** everyday clothing, dignified, lined face, quiet strength. Accent `#3d6f59`. |
| `informal_sector_worker` | A dignified informal waste-picker with 15 years' experience, sturdy **green** work clothes and a faded scarf, calloused hands, proud bearing — never pitiable. Accent `#157347`. |

## Per-expression modifier (append to the subject)

- **neutral** — calm, attentive, neutral mouth, listening at the negotiation
  table. (This is the base/reference image.)
- **happy** — warm satisfied smile, relaxed brows, hopeful — a point has been
  agreed in their favour.
- **concerned** — slight frown, raised inner brows, pensive — conditionally
  accepting, reservations remain.
- **angry** — firm displeasure, lowered brows, set jaw (controlled, not
  shouting) — rejecting a proposal that crosses a red line.

## Full prompt template

```
<shared style preamble> <per-character subject>, <per-expression modifier>.
Consistent character, same person across expressions, square 1:1, cream
#f7f3e8 background, no text.
```

### Example — `assets/community_member/concerned.png`

> Flat editorial vector illustration, warm and grounded, environmental-civic
> theme. Muted olive, kraft-brown and recycled-paper palette. Soft even studio
> lighting, gentle shading, clean rounded shapes, dignified and respectful
> character design (not caricatured). Head-and-shoulders bust, centred,
> front-facing, solid cream #f7f3e8 background, square composition, no text. A
> weathered, resilient host-community resident from Eastfield village, simple
> forest-green everyday clothing, dignified, lined face, quiet strength, slight
> frown with raised inner brows, pensive and reserved. Consistent character,
> same person across expressions, square 1:1, cream #f7f3e8 background, no text.
