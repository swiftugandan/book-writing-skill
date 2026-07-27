# The diagram grammar

Diagrams are hand-authored inline SVG. Start from `assets/diagram.template.svg`.

## One user unit is one point

Every diagram sets its `viewBox` so that **1 user unit = 1 point**. Then
`font-size="9"` means 9pt on paper and nobody has to reason about scaling.

This matters because the alternative fails quietly. An SVG declared
`width="144pt"` over `viewBox="0 0 288 72"` scales every unit by half, so a label
written `font-size="10"` prints at 5pt. It looks correct in the source and it is
unreadable in the book. The checker computes the true rendered size from the
declared width over the viewBox width, so a deviation is caught rather than
shipped, but the convention means you never meet the problem.

## Sizing

- **Maximum width is 410.4 units**, which is 5.7in: `--page-w` minus twice
  `--margin` at the default 7 × 10in trim. A wider diagram runs into the margin.
- Declare `width`, `height`, and `viewBox` on every `<svg>`.
- Dimensions in `in` or `pt`. Never `px`, never unitless. A page is a physical
  object.
- Height is yours to choose, but remember the diagram has to fit the space left
  on its page. If it does not, `.page { overflow: hidden }` crops it and
  `bookkit.verify` reports the clipping.

## Colour is always a token

Every `fill` and `stroke` is `var(--token, fallback)`, or `none`, or
`currentColor`:

```svg
<rect fill="var(--paper, #ffffff)" stroke="var(--ink, #242424)" stroke-width="1"/>
```

Inline in a page the token resolves to the book's palette, so the diagram
retargets when the book does. Saved as a standalone file the fallback applies.
One authoring form serves both.

Available tokens: `--ink`, `--paper`, `--pale`, `--accent`, `--support`,
`--caution`, `--muted`, plus `--serif`, `--sans`, `--mono`.

## The palette has three tonal levels, not seven colours

This is the constraint that catches people. Greyscale contrast between the
tokens:

| Pair | Contrast |
|---|---|
| `--ink` vs `--paper` | 15.52 |
| `--ink` vs any mid-tone | 2.79 to 3.59 |
| `--paper` vs any mid-tone | 4.32 to 5.57 |
| `--accent` vs `--support` | **1.14** |
| `--accent` vs `--caution` | **1.26** |
| `--support` vs `--muted` | **1.13** |
| `--caution` vs `--muted` | **1.02** |
| `--paper` vs `--pale` | **1.13** |

Every mid-tone pair collapses. In print the palette resolves to three usable
levels: dark, one mid grey, and light. `--accent` and `--support` are obviously
different on a monitor and the same grey on paper.

So **a diagram can encode at most three categories by fill alone.** A fourth
needs a different channel:

- a dash pattern, `stroke-dasharray="4 3"`
- a stroke weight, `stroke-width="2"` against `stroke-width="1"`
- a shape change, a rounded box against a squared one
- a label

The checker enforces this. Two fills closer than 1.5:1 in greyscale pass only
when the shapes carrying them differ by dash pattern or stroke weight. The rule
is that colour alone is not enough, not that these colours are banned.

`interior.css` already works this way for callouts, where `.callout.caution`
carries a double border and the `.label` variants use distinct glyphs. Diagrams
follow the same discipline.

## Primitives

**Box.** Offset by 0.5 so a 1-unit stroke lands cleanly rather than straddling
two half-units.

```svg
<rect x="0.5" y="8.5" width="86" height="34" rx="2"
      fill="var(--paper, #ffffff)" stroke="var(--ink, #242424)" stroke-width="1"/>
```

**Arrow.** Define the marker once in `<defs>`. `auto-start-reverse` lets the same
marker serve both ends.

```svg
<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"
        markerWidth="7" markerHeight="7" orient="auto-start-reverse">
  <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--ink, #242424)"/>
</marker>
```

**Label.** Centre with `text-anchor="middle"` on the box centre.

```svg
<text x="43.5" y="30" text-anchor="middle" font-size="8.5"
      font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
      fill="var(--ink, #242424)">Draft</text>
```

**Rule.** A hairline separator at `stroke-width="0.5"`.

**Annotation.** A short leader line with a marker at the pointing end, then text
set 4 units clear of it.

## Type

- Box labels: 8 to 9 units.
- Secondary and caption text: 7.5 units.
- Nothing below 6. The checker fails under 6pt, and the interior's own smallest
  type is `.label` at 6.8pt for comparison.
- Headings inside a diagram use `--sans`; specification or code fragments use
  `--mono`.

Text needs 4.5:1 contrast against whatever sits behind it, which in practice
means `--ink` on `--paper` or on `--pale`.

## Accessibility

Every diagram carries `role="img"` and an `aria-label` that describes it for a
reader who cannot see it. Describe what the diagram shows, not that it is a
diagram.
