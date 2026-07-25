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

Read `references/blueprint-format.md`. Copy `assets/STRUCTURE.template.md` and fill it in.

Every chapter declares one **driving question**, and every beat in that chapter must serve
the answer. This is the constraint that keeps a chapter from becoming a topic dump.

`STRUCTURE.md` is the contract between writing sessions. Write it before any prose.

## ③ Interior: establish the design system

Read `references/interior-design.md`. Copy `assets/interior.css` into the project and set
the tokens (`--page-w`, `--page-h`, `--margin`, `--ink`, `--paper`, `--accent`, `--serif`,
`--sans`, `--mono`).

Then lay out **one** chapter and take it all the way through phase ⑥. Prove the design on a
single chapter before laying out the rest.

## ④ Chapter: draft and typeset

Read `references/chapter-pattern.md`. One chapter at a time, from `STRUCTURE.md` into a copy
of `assets/chapter.template.html`.

Pages are laid out by hand as `.page` divs. A chapter may add its own diagram CSS in an
inline `<style>`, prefixed `ch-`, never shadowing a core selector.

## ⑤ Editorial gate

Read `references/editorial-standards.md`, then invoke the **`avoid-ai-writing`** skill on the
chapter. A chapter is not done until it has passed this gate.

## ⑥ Production

Read `references/production.md`.

```bash
cd skills/book-writing/scripts
.venv/bin/python -m bookkit.paginate ../../../book
.venv/bin/python -m bookkit.render   ../../../book
.venv/bin/python -m bookkit.merge    ../../../book
.venv/bin/python -m bookkit.verify   ../../../book --css ../assets/interior.css
```

`verify` fails on clipped pages, wrong geometry, CSS layering violations, a stale manifest,
and folio discontinuity. Every one of those failures is otherwise silent. Never hand-edit a
`counter-reset` offset; `paginate` writes it from measured page counts.

Re-run all four after any content edit: editing one chapter changes its page count, which
changes every downstream folio.
