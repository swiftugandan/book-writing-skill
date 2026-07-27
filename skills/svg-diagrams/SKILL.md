---
name: svg-diagrams
description: Author SVG diagrams that survive print. Token-driven, legible in greyscale, and checked mechanically. Use when a chapter, article, or document needs a flow, architecture stack, node map, pipeline, cycle, or annotated artifact.
---

# Drawing a diagram

Diagrams here are hand-authored inline SVG. They inherit the surrounding design tokens, so
they retarget when the document does, and they are checked before they ship.

Work in this order.

## ① Decide whether a diagram earns its place

A diagram is worth making when the relationship between things is the point. If the content
is a sequence of items, write a list. If it is values across two axes, use a table:
`.matrix` in `interior.css` already handles those, and a table is not a drawing.

## ② Pick the archetype

Read `references/archetypes.md`. Six archetypes cover most of what a technical book needs:
flow, pipeline, cycle, layered stack, node map, annotated anatomy. Each links a worked
example under `assets/examples/` that already passes the checker. Start from the closest one
rather than from an empty file.

## ③ Draw it

Read `references/grammar.md` before writing any SVG. Three rules do most of the work:

- **One user unit is one point.** `font-size="9"` then means 9pt on paper.
- **Maximum width is 410.4 units**, the text measure at the default 7 × 10in trim.
- **Every colour is `var(--token, fallback)`.** Never a literal hex.

The constraint that catches people: **the palette has three tonal levels, not seven
colours.** In greyscale `--accent` and `--support` sit at 1.14:1, `--caution` and `--muted`
at 1.02:1, and even `--paper` against `--pale` at 1.13:1. Those pairs are the same grey on
paper. So a diagram can encode at most three categories by fill alone. A fourth needs a dash
pattern, a stroke weight, a shape change, or a label.

Start from `assets/diagram.template.svg`.

## ④ Check it

Read `references/verification.md`.

```bash
cd skills/book-writing/scripts
.venv/bin/python -m bookkit.diagrams /path/to/target
```

The target can be a book directory, an HTML file, or a standalone `.svg`. Inside a book this
is already covered: `bookkit.verify` runs the same checks over every page file.

The checker rejects text below the 6pt print floor, text under 4.5:1 contrast, fills that
collapse in greyscale without another differentiating channel, content cropped by the
`viewBox`, hardcoded colours, external or raster references, gradients and filters, and
missing or `px` dimensions. Every one of those is invisible on a backlit screen and obvious
on paper, which is why none of them is a warning.
