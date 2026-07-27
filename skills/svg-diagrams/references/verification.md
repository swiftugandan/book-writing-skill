# Verification

Every check here catches something invisible on a backlit screen and obvious on
paper. That is why none of them is a warning.

## Running it

```bash
cd skills/book-writing/scripts
.venv/bin/python -m bookkit.diagrams /path/to/target
```

The target can be a book directory, a single HTML file, or a standalone `.svg`.

Inside a book you rarely need it: `bookkit.verify` runs the same checks over
every page file, so the production pipeline already covers diagrams.

The checker lives in `bookkit` alongside the rest of the verification tooling,
which means the same Chromium measures diagrams, measures pages, and prints the
PDF. Using this skill outside a book therefore needs `bookkit` installed. That is
the cost of not maintaining two copies of the same checks.

## What it enforces

| Check | Threshold | Why the failure is silent |
|---|---|---|
| Greyscale distinguishability | 1.5:1 between fills | Two hues that differ on screen collapse to one grey in print. The diagram looks right everywhere except the book. |
| Text legibility | 6pt floor, at rendered scale | Small type is perfectly readable on a screen you can zoom. On paper it is a smudge, and you find out after the print run. |
| Text contrast | 4.5:1 | Pale labels survive a bright monitor and vanish under office lighting. |
| Overflow | viewBox bounds | Content outside the viewBox is cropped with no error. The shape is simply gone. |
| Hardcoded colour | any literal | The diagram stays orange when the book is retargeted to blue, and nothing reports it. |
| External or raster reference | any | The PDF renders a missing graphic. The build succeeds. |
| Gradients, filters, shadows | any | Banned by the layout discipline. They also print as mud. |
| Dimensions | present, not `px` | Without a physical unit the print size depends on rendering context rather than on intent. |

## The escape for a low-contrast pair

Two fills closer than 1.5:1 in greyscale pass when the shapes carrying them
differ by a **dash pattern** or a **stroke weight**:

```svg
<rect fill="var(--accent, #d54b20)" stroke="var(--ink, #242424)" stroke-width="1"/>
<rect fill="var(--support, #177c83)" stroke="var(--ink, #242424)"
      stroke-width="1" stroke-dasharray="4 2"/>
```

Those two fills are 1.14:1 apart, which is the same grey on paper. The dash
pattern is what makes them separable, and colour becomes a bonus for readers of
the screen edition rather than the only signal.

This is the same move `interior.css` already makes for callouts, where
`.callout.caution` carries a double border and the `.label` variants use distinct
glyphs. The rule is that **colour alone is not enough**, not that particular
colours are forbidden.

## Reading a failure

```
ERROR   flow.svg: diagram 1: fills rgb(213, 75, 32) and rgb(23, 124, 131) are
        1.14:1 apart in greyscale, below 1.5:1, and are not separated by a dash
        pattern or stroke weight; colour alone is not enough
```

The message names the two resolved colours, the measured ratio, and the fix.
Colours are reported as resolved values rather than token names, because the same
token resolves differently once a book is retargeted and the resolved value is
what actually prints.
