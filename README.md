# book-writing

[![test](https://github.com/swiftugandan/book-writing-skill/actions/workflows/test.yml/badge.svg)](https://github.com/swiftugandan/book-writing-skill/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A [Claude Code](https://claude.com/claude-code) skill that turns a folder of source
material into a produced book: a structural blueprint, hand-paginated chapters, and a
merged, verified PDF.

It carries **structure**, meaning how a book is architected, and **design**, meaning how
the interior is built and rendered. It carries **no subject matter and no prose voice**.
Those come from your drafts and your instructions, which is what keeps it usable for a
book about anything.

## Install

As a plugin:

```
/plugin marketplace add swiftugandan/book-writing-skill
/plugin install book-writing
/plugin install svg-diagrams
```

Or copy the skill directly:

```bash
git clone https://github.com/swiftugandan/book-writing-skill.git
cp -R book-writing-skill/skills/book-writing ~/.claude/skills/
```

The skill directory is self-contained. The Python package, its tests, the stylesheet,
the templates, and the reference documents all live inside it.

## Setup

```bash
cd ~/.claude/skills/book-writing/scripts
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/playwright install chromium
```

Python 3.11 or newer. Playwright brings its own Chromium, so no system browser is
needed.

## Use

Put your source material in a `drafts/` folder at your project root. Transcripts, notes,
articles, outlines, half-written prose, anything. Then ask Claude to write the book.

The skill runs six phases, reading only the reference it needs for the phase it is in:

| Phase | What happens |
|---|---|
| ① Intake | Read `drafts/`. Extract the driving problem, the claims, the openers, the candidate running examples. Every claim gets labelled by evidential standing. |
| ② Blueprint | Write `STRUCTURE.md`: promise, audience, reading paths, running examples, and per chapter a driving question, beat list, field guide, and example. Written to the editorial constraints, because most of it is printed. |
| ③ Interior | Set the design tokens and prove them by taking one chapter all the way to PDF. |
| ④ Chapter | Draft and typeset chapters one at a time against a 13-beat pattern, **writing to the editorial constraints rather than repairing afterwards**. |
| ⑤ Editorial gate | Audit each chapter: `avoid-ai-writing` in detect mode, then the rigor checks a pattern detector cannot see. |
| ⑥ Production | Paginate, render, merge, verify. |

Two ideas do most of the work.

**Every chapter declares one driving question**, and every beat in that chapter must
serve the answer. It is the test that stops a chapter turning into a topic dump: a beat
that fails it gets cut or moved to the chapter whose question it actually serves.

**`STRUCTURE.md` is the contract between writing sessions.** A book is written over
weeks. Without a written architecture, chapter 9 drifts from chapter 2: the running
example mutates, the audience widens, the same idea arrives twice under different names.

## Prose quality is constrained twice

The editorial standards are loaded **before** anything is written, not after. They are
generation constraints first: vary sentence and paragraph length deliberately, keep em
dashes under one per thousand words, skip the transitional throat-clearing, repeat the
right word instead of cycling synonyms.

That covers the blueprint as well as the chapters. Most of `STRUCTURE.md` is printed: the
promise reaches the preface and the back cover, chapter titles repeat in every running
head, driving questions become chapter decks. A weak chapter title is on the page hundreds
of times, and it is far cheaper to fix a promise in the blueprint than after it has been
set in three places. The shipped templates model the rules too, since a template that uses
em dashes teaches every book built from it to use them.

Then the chapter is audited, because nobody holds forty rules in mind across nine pages.
The audit runs [`avoid-ai-writing`](https://github.com/conorbronsdon/avoid-ai-writing) in
**detect mode first** and fixes only what it flags.

Order matters more than it looks. Rewriting to remove AI patterns is more expensive than
not emitting them, and a heavy rewrite pass sands away the irregularity that makes prose
read as human. That failure mode is real enough that the `avoid-ai-writing` skill warns
about it directly. A chapter written to the constraints needs a light audit; a chapter
written blind needs surgery, and the surgery costs it its voice.

It is the same shape as the production pipeline. The templates are built to the right
geometry **and** `verify` checks the geometry. Constrain, then verify.

## Book directory

```
book/
  interior.css          the core stylesheet, linked by every page file
  book.order            assembly order, one filename per line
  front-matter.html
  chapter-01.html
  book.manifest.json    written by bookkit.paginate
  pdf/                  written by bookkit.render
  book.pdf              written by bookkit.merge
```

Everything a page needs sits beside it, so any page file opens correctly in a browser
with no build step.

## Production

```bash
SKILL=~/.claude/skills/book-writing
BOOK=/path/to/your/book

cd "$SKILL/scripts"
.venv/bin/python -m bookkit.paginate "$BOOK"
.venv/bin/python -m bookkit.render   "$BOOK"
.venv/bin/python -m bookkit.merge    "$BOOK"
.venv/bin/python -m bookkit.verify   "$BOOK"
```

Re-run all four after any content edit. Editing one chapter changes its page count, which
changes every downstream folio.

## Why verification is not optional

Hand-paginated books fail silently. That is the whole reason this repository contains
code and not just Markdown.

`.page { overflow: hidden }` is what keeps the trim clean, and it also means content that
does not fit is cropped away with no error. Text simply vanishes off the bottom of a page
and the PDF looks fine. Folio offsets have the same shape of problem: assign them by hand,
let one chapter run a page long, and every page number after it is wrong.

So `bookkit.verify` exits non-zero on all of these:

| Hard failure | What it catches |
|---|---|
| Content clipping | Text overflowing its page and disappearing |
| Geometry mismatch | A page rendering at the wrong trim |
| CSS layering violation | A chapter-local selector unprefixed, or shadowing the core stylesheet |
| Folio discontinuity | Page numbers that do not run continuously |
| Stale manifest | A chapter edited without re-running `paginate` |

`bookkit.merge` adds one more at assembly time: it refuses to write a book whose rendered
page count disagrees with the manifest.

Page counts drifting from the budget in `STRUCTURE.md` is a warning rather than an error.
A chapter running long is usually a chapter answering two questions, which is a problem to
fix in the blueprint.

## Diagrams

The companion `svg-diagrams` skill covers diagrams. They are inline SVG driven by the same
tokens as the interior, so they retarget with the book, and `bookkit.verify` checks them
alongside everything else.

The check that earns its keep is greyscale. `interior-design.md` always said diagrams must
never carry meaning in colour alone, and nothing enforced it. Measuring the palette shows
why that mattered: `--accent` and `--support` sit at 1.14:1 in greyscale, `--caution` and
`--muted` at 1.02:1, and even `--paper` against `--pale` at 1.13:1. Obviously different on a
monitor, the same grey on paper.

So the palette offers three tonal levels, not seven colours, and a diagram can encode at
most three categories by fill. A fourth needs a dash pattern, a stroke weight, a shape
change, or a label. A low-contrast pair passes the checker when it carries one of those,
which is the same move `interior.css` already makes for callouts.

The checker also rejects text below a 6pt print floor, measured at rendered scale rather
than in user units, since a viewBox that scales its contents will happily print a 10-unit
label at 5pt.

```bash
.venv/bin/python -m bookkit.diagrams /path/to/book-or-file
```

## Retargeting the design

The interior ships as a technical-publisher trim: 7 × 10 inches, serif body, one restrained
spot colour. Nine tokens at the top of `interior.css` control all of it.

```css
--page-w  --page-h  --margin
--ink  --paper  --accent
--serif  --sans  --mono
```

Changing the trim also means passing the new geometry to the tools, since the CSS `@page`
rule cannot read custom properties:

```bash
.venv/bin/python -m bookkit.render "$BOOK" --page-w 6in --page-h 9in
.venv/bin/python -m bookkit.verify "$BOOK" --width-pt 432 --height-pt 648
```

## Tests

```bash
cd skills/book-writing/scripts && .venv/bin/pytest
```

245 tests. CI additionally builds a real book from the shipped templates and runs the four
documented commands, then confirms `verify` rejects a deliberately clipped page. That
end-to-end check exists because it caught a bug the unit suite could not: the fixtures
construct valid layouts by hand, so a template linking the wrong stylesheet path passed
every unit test and still produced an unstyled book.

## Attribution

The structural and production design is distilled from
[swiftugandan/specification-driven-delivery-book](https://github.com/swiftugandan/specification-driven-delivery-book):
the blueprint format, the chapter beat pattern, the editorial standards, and the
hand-paginated HTML interior. The pagination and verification tooling is new. That book
assigned folio offsets by hand, which this replaces with measured values.

The editorial gate delegates to
[conorbronsdon/avoid-ai-writing](https://github.com/conorbronsdon/avoid-ai-writing)
rather than reimplementing AI-writing detection.

No content from either source is redistributed here, and a test asserts as much.

## License

[MIT](LICENSE)
