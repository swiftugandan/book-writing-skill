# `svg-diagrams` skill — design

**Date:** 2026-07-27
**Status:** Approved for planning

## Purpose

A skill for authoring SVG diagrams that survive print: legible in grayscale, sized for the
page, and driven by the same design tokens as the book around them.

It works standalone and inside a book. `book-writing` phase ④ delegates to it, the same
way phase ⑤ delegates to `avoid-ai-writing` rather than reimplementing detection.

## Why this exists

`references/interior-design.md` already states the rule: diagrams must be functional,
must read in grayscale, and must never carry meaning in colour alone. Nothing enforced it.

That gap is not theoretical. The interior's own two supporting hues, `--accent` (`#d54b20`)
and `--support` (`#177c83`), have a **grayscale contrast ratio of 1.14:1**. They are
obviously different on screen and nearly the same grey in print. A diagram that encodes
"approved" and "rejected" as those two fills is unreadable in the printed book and looks
perfect on the monitor where it was made.

`interior.css` already solves this for callouts by adding a non-colour differentiator:
`.callout.caution` uses a double border, and `.label` variants use distinct glyphs
(`■`, `●`, `▲`). Diagrams need the same discipline, applied mechanically.

### The palette has three tonal levels, not seven colours

Computing the grayscale contrast of every token pair makes the constraint concrete:

| Pair | Grayscale contrast |
|---|---|
| `--ink` vs `--paper` | 15.52 |
| `--ink` vs any mid-tone | 2.79 – 3.59 |
| `--paper` vs any mid-tone | 4.32 – 5.57 |
| **`--accent` vs `--support`** | **1.14** |
| **`--accent` vs `--caution`** | **1.26** |
| **`--support` vs `--muted`** | **1.13** |
| **`--caution` vs `--muted`** | **1.02** |
| **`--paper` vs `--pale`** | **1.13** |

Every mid-tone pair collapses. In print the palette resolves to three usable levels: dark
(`--ink`), one mid grey (`--accent`, `--support`, `--caution`, `--muted` are all the same
grey), and light (`--paper`, `--pale`).

So a diagram can encode at most **three** categories by fill alone. A fourth needs a
different channel: a dash pattern, a stroke weight, a hatch, or a label. This belongs in
`grammar.md` as an authoring rule, not only in the checker as a rejection.

## Non-goals

- Diagram generators, a DSL, or auto-layout. Real book diagrams are one-offs; the source
  book had 128 single-use components for that reason.
- Matrices. `.matrix` in `interior.css` already handles them, and a table is not a drawing.
- Replacing `interior.css`. Diagrams are inline SVG and carry their own geometry.

## Packaging

New skill at `skills/svg-diagrams/`. The checker lives in `bookkit`, alongside the rest of
verification, so diagrams are measured by the same Chromium that prints them.

```
skills/svg-diagrams/
  SKILL.md                    router: when to draw, which archetype, how to verify
  references/
    grammar.md                primitives, tokens, sizing, the print floor
    archetypes.md             six worked examples with commentary
    verification.md           what the checker enforces and why each failure is silent
  assets/
    diagram.template.svg
    examples/
      flow.svg  layered-stack.svg  node-map.svg
      pipeline.svg  cycle.svg  annotated-anatomy.svg
```

Using the skill standalone therefore requires `bookkit` installed. Documented rather than
solved by duplicating the checker.

## The token contract

An SVG referenced with `<img src="diagram.svg">` cannot see the page's CSS custom
properties. Only inline SVG inherits them. So **diagrams are inline `<svg>` elements inside
the `.page` div**, and every colour is a token with a fallback:

```svg
<rect fill="var(--paper, #ffffff)" stroke="var(--ink, #242424)" stroke-width="1"/>
<text font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
      font-size="8pt" fill="var(--ink, #242424)">Reviewed</text>
```

Inline in a book page, the diagram picks up the book's palette and retargets with it. Saved
as a standalone `.svg`, the fallbacks apply. One authoring form serves both.

Inline SVG also needs no `ch-` class, which retires the ad-hoc diagram CSS that produced
those 128 single-use selectors.

## Sizing

- Maximum width is the text measure: `--page-w` minus twice `--margin`, which is **5.7in**
  at the default 7 × 10in trim.
- Dimensions in `in` or `pt`, never `px`. The page is a physical object.
- Every diagram declares `width`, `height`, and a matching `viewBox`.

Diagram height interacts with hand-pagination, but needs no new tooling: a diagram too tall
for the space left on its page overflows the `.page` box, and the existing clipping check
in `bookkit.verify` already catches that.

## Archetypes

Six, chosen from what recurred in the source book rather than invented. Each ships as a
checker-clean worked example under `assets/examples/`.

| Archetype | Source-book evidence | Use for |
|---|---|---|
| Flow | `.state-flow`, `.flow-arrow`, `.flow-box` | A sequence of steps with branches |
| Layered stack | `.layer`, `.boundary-grid`, `.harness-layer` | Architecture, responsibility bands |
| Node map | `.map-actor`, `.map-case`, `.map-system` | Actors against capabilities |
| Pipeline | `.pipeline-row`, `.stage` | Ordered stages with inputs and outputs |
| Cycle | `.part-loop`, `.part-cycle` | A loop that returns to its start |
| Annotated anatomy | `.anatomy` | Callouts pointing at parts of an artifact |

Timelines are a pipeline variant and traceability chains are a flow variant. Neither earns
a separate entry.

## Verification

### Module layout

`Finding` and `has_errors` move from `bookkit/verify.py` into a new `bookkit/findings.py`,
imported by both `verify.py` and the new `diagrams.py`. Without this, `verify` importing
`diagrams` while `diagrams` imports `Finding` from `verify` is a circular import.

New `bookkit/diagrams.py`:

- `relative_luminance(rgb: tuple[int, int, int]) -> float` — WCAG relative luminance.
- `contrast_ratio(a, b) -> float` — `(L_lighter + 0.05) / (L_darker + 0.05)`.
- `find_diagrams(path: Path) -> list[Diagram]` — every inline `<svg>` in an HTML file, or
  the root element of an `.svg` file.
- `check_diagrams(paths: Sequence[Path]) -> list[Finding]`
- CLI `python -m bookkit.diagrams <path>` accepting a book directory, an HTML file, or an
  SVG file.

`bookkit.verify` calls `check_diagrams` over the manifest's page files, so the book pipeline
covers diagrams with no extra command.

Constants: `MIN_FILL_CONTRAST = 1.5`, `MIN_TEXT_CONTRAST = 4.5`, `MIN_TYPE_PT = 6.0`.

### Colour resolution

Colours are read from the browser's computed style, not parsed from the source, so
`var(--accent, …)` resolves to whatever the surrounding page actually sets. This reuses
`measure.browser_page()`, keeping one rendering engine for measurement, printing, and
diagram checking.

### The checks

Each hard-fails. Every one is silent without the check.

**1. Grayscale distinguishability.** A *semantic fill* is a distinct computed `fill` value
appearing on a shape element (`rect`, `circle`, `ellipse`, `polygon`, `path`), excluding
`none` and fully transparent values. Stroke colours are checked the same way, separately.

For every pair of distinct semantic fills, compute the grayscale contrast ratio. Below `MIN_FILL_CONTRAST`, the pair must be separated by a
non-colour attribute: a differing `stroke-dasharray`, a differing `stroke-width`, or a
`<pattern>` fill. If it is not, that is an error.

This is the nuance the `--accent`/`--support` case forces. A flat fail on low contrast
would reject legitimate designs that already differentiate by another channel, which is
exactly what `interior.css` does for callouts. The rule is "colour alone is not enough",
not "these colours are banned".

**2. Text legibility.** Any `<text>` with a computed `font-size` below `MIN_TYPE_PT` is an
error. The interior's smallest type is `.label` at 6.8pt, so a 6pt floor leaves room
without permitting the 4pt labels that look fine on a backlit screen and vanish in print.

**3. Text contrast.** Each `<text>` is compared against its background: the fill of the
smallest shape whose bounding box contains the text's bounding box, defaulting to
`--paper`. Below `MIN_TEXT_CONTRAST` (WCAG AA, 4.5:1) is an error.

**4. Overflow.** Any element whose bounding box extends beyond the `viewBox` is an error.
The content is cropped with no warning otherwise.

**5. Hardcoded colour.** A literal hex or named colour in a `fill` or `stroke` attribute,
where a `var(--token, fallback)` belongs. Without this the diagram stays orange when the
book is retargeted to blue.

**6. External and raster references.** `<image>`, `xlink:href`, or any remote URL. These
produce a missing graphic in the PDF.

**7. Gradients and shadows.** `<linearGradient>`, `<radialGradient>`, `<filter>`,
`feDropShadow`. Banned by the layout discipline in `interior-design.md`.

**8. Missing dimensions.** An `<svg>` without `width`, `height`, and `viewBox`, or with
dimensions in `px`.

## Delegation from book-writing

`SKILL.md` phase ④ gains one short paragraph: when a chapter needs a diagram, invoke
`svg-diagrams`. The router is currently 727 words against a 900-word test budget, so this
fits without restructuring.

`references/interior-design.md` gains a pointer from its layout-discipline section, so the
rule and its enforcement are named in the same place.

## Testing

- **Pure maths**, no browser: `relative_luminance` against known WCAG values,
  `contrast_ratio` symmetry, and the `--accent`/`--support` pair asserting 1.14:1 so the
  motivating case is pinned as a regression test.
- **One fixture per check**, each a minimal SVG that trips exactly one rule, plus a clean
  control that trips none.
- **The non-colour-differentiator escape**: a low-contrast pair separated by
  `stroke-dasharray` passes; the same pair without it fails.
- **Dogfooding**: every example in `assets/examples/` must pass the checker, in the same
  shape as the existing `test_interior_css` and template tests.
- **Pipeline integration**: a book page containing a bad diagram fails `bookkit.verify`.
- **Skill structure**: `SKILL.md` frontmatter, references exist, book-writing phase ④
  names the delegation.

## Open items

None. Scope is fixed as above.
