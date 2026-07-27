---
name: book-writing
description: Write and produce a book from source material in a drafts/ folder: a structural blueprint, hand-paginated chapters, and a verified PDF. Use when asked to write a book, turn drafts or a transcript into a book, outline or structure a book, draft or typeset a chapter, or produce a book PDF.
---

# Writing a book

Turns a `drafts/` folder into a produced book through six phases. This skill carries
**structure** (how a book is architected) and **design** (how the interior is built and
rendered). It carries **no subject matter and no voice**. Those come from the drafts and from the
author's instructions.

Work one phase at a time. Read the reference for the active phase; do not preload the rest.

## ① Intake: read `drafts/`

Inventory everything in `drafts/`: transcripts, notes, articles, outlines, existing prose.
Extract into a working note:

- The driving problem the book exists to address.
- Every distinct claim, each labelled **reported practice**, **interpretation**,
  **established practice**, **evidence**, or **speculation**. This classification is carried
  all the way into the prose.
- Stories usable as chapter openers.
- Candidate running examples.

Voice and subject matter are read out of the drafts here. If `drafts/` is empty or missing,
stop and say so. **Do not invent source material.**

## ② Blueprint: write `STRUCTURE.md`

Read `references/blueprint-format.md` **and Part One of
`references/editorial-standards.md`**. Copy `assets/STRUCTURE.template.md` and fill it in.

Most of the blueprint is printed: the promise reaches the preface and back cover, chapter
titles repeat in every running head, driving questions become chapter decks. It is shipping
prose, so it is written to the same constraints and audited the same way. Run
`avoid-ai-writing` in detect mode over `STRUCTURE.md` before moving on.

Every chapter declares one **driving question**, and every beat in that chapter must serve
the answer. This is the constraint that keeps a chapter from becoming a topic dump.

`STRUCTURE.md` is the contract between writing sessions. Write it before any prose.

## ③ Interior: establish the design system

Read `references/interior-design.md`. Copy `assets/interior.css` **into the book directory,
beside the page files**, and set the tokens (`--page-w`, `--page-h`, `--margin`, `--ink`,
`--paper`, `--accent`, `--serif`, `--sans`, `--mono`).

The book directory holds everything the browser needs to resolve a page:

```
book/
  interior.css          the core layer, linked by every page file
  book.order            assembly order, one filename per line
  front-matter.html
  chapter-01.html
```

Then lay out **one** chapter and take it all the way through phase ⑥. Prove the design on a
single chapter before laying out the rest.

## ④ Chapter: draft and typeset

Read **both** `references/chapter-pattern.md` and `references/editorial-standards.md`
**before writing a word**. Part One of the editorial standards is a set of generation
constraints, not a checklist for afterwards. Writing to them costs nothing; repairing prose
that ignored them costs a rewrite, and a heavy rewrite flattens the voice the drafts gave
the book.

Then one chapter at a time, from `STRUCTURE.md` into a copy of
`assets/chapter.template.html`.

Pages are laid out by hand as `.page` divs. A chapter may add its own diagram CSS in an
inline `<style>`, prefixed `ch-`, never shadowing a core selector.

When a chapter needs a diagram, invoke the **`svg-diagrams`** skill. Diagrams are inline SVG
driven by the same tokens as the interior, so they need no `ch-` class at all, and
`bookkit.verify` already checks them.

## ⑤ Editorial gate

Part Two of `references/editorial-standards.md`. Three steps, per chapter:

1. Invoke the **`avoid-ai-writing`** skill in **detect mode** first. A chapter drafted to
   Part One should come back nearly clean. Fix only what it flags; rewriting unflagged
   prose strips the irregularity that makes it read as human.
2. Check the things a pattern detector cannot see: terms defined on first use, claims still
   carrying their evidential standing, every beat still serving the driving question.
3. Count em dashes against the one-per-thousand-words target.

A chapter is not done until it has passed all three.

## ⑥ Production

Read `references/production.md`.

Set `SKILL` to this skill's own directory (the one holding this file) and `BOOK` to the
book directory, then:

```bash
cd "$SKILL/scripts"
.venv/bin/python -m bookkit.paginate "$BOOK"
.venv/bin/python -m bookkit.render   "$BOOK"
.venv/bin/python -m bookkit.merge    "$BOOK"
.venv/bin/python -m bookkit.verify   "$BOOK" --css "$SKILL/assets/interior.css"
```

First run only: `python3 -m venv .venv && .venv/bin/pip install -e '.[dev]' &&
.venv/bin/playwright install chromium`.

`verify` fails on clipped pages, wrong geometry, CSS layering violations, a stale manifest,
and folio discontinuity. Every one of those failures is otherwise silent. Never hand-edit a
`counter-reset` offset; `paginate` writes it from measured page counts.

Re-run all four after any content edit: editing one chapter changes its page count, which
changes every downstream folio.
