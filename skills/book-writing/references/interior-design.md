# The interior design system

`assets/interior.css` is the book's interior. Copy it into the **book directory**,
beside the page files, set the tokens, and link it from every page file as
`<link rel="stylesheet" href="interior.css">`.

Keeping the stylesheet beside the page files is what makes a page file
self-resolving: open one in a browser, or hand it to `bookkit.render`, and it
finds its stylesheet with no build step and no path assumptions. A page file
that cannot resolve its stylesheet still renders, silently, without the fixed
`.page` height, so Chromium prints a different number of physical pages than
there are `.page` elements. `bookkit.merge` refuses to assemble a book when that
count disagrees with the manifest.

## Tokens

Retargeting the book is a token edit, not a stylesheet rewrite.

| Token | Default | Effect |
|---|---|---|
| `--page-w` | `7in` | Trim width. Drives `.page` geometry. |
| `--page-h` | `10in` | Trim height. |
| `--margin` | `0.65in` | Text block inset on all four sides. |
| `--ink` | `#242424` | Body text. Near-black rather than black; pure black on white is harsh at body size. |
| `--paper` | `#ffffff` | Page background. |
| `--accent` | `#d54b20` | The single spot colour: eyebrows, dropcaps, rules, principle bars. |
| `--serif` | Charter stack | Body text. |
| `--sans` | Avenir Next stack | Headings, labels, running heads, folios. |
| `--mono` | Courier stack | Specifications, code, artifact excerpts. |

Two supporting hues (`--support`, `--caution`) exist for callout variants. Keep
the palette this small. A technical interior earns its authority from restraint;
every additional colour costs more than it returns.

**Changing `--page-w` or `--page-h` also requires passing the new geometry to
`bookkit.render` and `bookkit.verify`.** The `@page` rule cannot read custom
properties, so it is not the source of truth. The CLI flags are.

## The two CSS layers

The **core layer** lives in `assets/interior.css` and is linked by every page
file. It holds the page frame, the typographic scale, and the component
vocabulary.

The **chapter-local layer** is an inline `<style>` block in a single page file,
for a diagram that only that chapter needs: a map, a board, a calendar, a timeline.

Two rules, both enforced by `bookkit.verify`:

1. Every chapter-local class is prefixed `ch-`.
2. No chapter-local class shadows a core selector.

The second rule is the one that matters. A chapter that redefines `.callout`
restyles every callout in the book, and the damage shows up in a chapter nobody
was editing. Prefixing makes the boundary visible; the shadow check makes it
real.

The distinction is not theoretical. In the source this system was distilled from,
roughly 25 selectors appeared in nearly every file while 128 appeared in only one
or two: a genuine core surrounded by per-chapter invention, with no boundary
between them and the whole stylesheet duplicated into all 33 files.

## Component vocabulary

- **Page frame** — `page`, `with-head`, `running-head`, `page-number`,
  `folio-title`
- **Typographic scale** — `lead`, `small`, `micro`, `caption`, plus `h1`–`h4`
- **Chapter opener** — `eyebrow`, `deck`, `dropcap`, `opener-number`
- **Rules and emphasis** — `rule`, `accent-rule`, `principle`, `quote`,
  `signature`
- **Layout** — `columns-2`, `columns-3`, `sidebar-grid`
- **Components** — `callout` (+ `support`, `caution`), `label`, `spec`,
  `artifact`, `steps`, `checklist`, `comparison-row`, `matrix`, `flow-box`

## Layout discipline

- Diagrams are functional, not decorative, and must read in **grayscale**.
- **Never carry meaning in colour alone.** Callout variants differ by border
  treatment and label glyph as well as hue, so they survive a monochrome print
  and a colour-blind reader.
- No slide-deck pages, full-page dark panels, card walls, gradients, or shadows.
- Continuous editorial rhythm: generous margins, quiet running heads, folios,
  captions. The interior should recede.

## Hand-pagination

Pages are laid out by hand as `.page` divs. You decide what falls on each page,
not the browser. This is what makes the interior controllable.

It has one sharp edge: `overflow: hidden` keeps the trim clean, so content that
does not fit is clipped without any error. Text simply vanishes off the bottom of
a page. `bookkit.verify` measures every page's content extent against its box for
exactly this reason. Run it.
