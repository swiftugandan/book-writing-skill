# book-writing

A Claude skill that turns a folder of source material into a produced book: a
structural blueprint, hand-paginated chapters, and a merged, verified PDF.

The skill carries **structure** (how a book is architected) and **design** (how the
interior is built and rendered). It carries **no subject matter and no prose voice** —
those come from your drafts and your instructions.

## Install

Copy the skill directory into your Claude skills folder:

```bash
cp -R skills/book-writing ~/.claude/skills/
```

It is self-contained: the Python package, its tests, the stylesheet, the templates,
and the references all live inside `skills/book-writing/`.

## Setup

```bash
cd ~/.claude/skills/book-writing/scripts
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/playwright install chromium
```

Requires Python 3.11 or newer. Playwright brings its own Chromium, so no system
browser is needed.

## Use

Put your source material — transcripts, notes, articles, outlines, existing prose —
in a `drafts/` folder at your project root, then ask Claude to write the book.

The skill runs six phases:

1. **Intake** — read `drafts/`, extract the driving problem, the claims (each labelled
   by evidential standing), the openers, and the candidate running examples.
2. **Blueprint** — write `STRUCTURE.md`: promise, audience, reading paths, running
   examples, and per chapter a driving question, beat list, field guide, and example.
3. **Interior** — set the design tokens in `interior.css` and prove them on one chapter.
4. **Chapter** — draft and typeset chapters one at a time against the beat pattern.
5. **Editorial gate** — run each chapter through the `avoid-ai-writing` skill.
6. **Production** — paginate, render, merge, verify.

## Production pipeline

```bash
cd skills/book-writing/scripts
.venv/bin/python -m bookkit.paginate ../../../book
.venv/bin/python -m bookkit.render   ../../../book
.venv/bin/python -m bookkit.merge    ../../../book
.venv/bin/python -m bookkit.verify   ../../../book --css ../assets/interior.css
```

`verify` exits non-zero on clipped pages, wrong trim geometry, CSS layering
violations, a stale manifest, and folio discontinuity. Each of those failures is
silent in a hand-paginated book — text that overflows a page is simply cropped away,
and a chapter that runs one page long renumbers everything after it — so none of the
checks is advisory.

## Tests

```bash
cd skills/book-writing/scripts && .venv/bin/pytest
```

## Attribution

The structural and production design is distilled from
[swiftugandan/specification-driven-delivery-book](https://github.com/swiftugandan/specification-driven-delivery-book):
the blueprint format, the chapter beat pattern, the editorial standards, and the
hand-paginated HTML interior. The pagination and verification tooling is new — the
source book assigned folio offsets by hand, which this replaces with measured values.

The editorial gate delegates to
[conorbronsdon/avoid-ai-writing](https://github.com/conorbronsdon/avoid-ai-writing)
rather than reimplementing AI-writing detection.

No content from either source is redistributed here.
