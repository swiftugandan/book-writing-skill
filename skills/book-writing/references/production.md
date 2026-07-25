# Production

Four commands, always in this order.

## First-time setup

```bash
cd skills/book-writing/scripts
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/playwright install chromium
```

## The pipeline

```bash
cd skills/book-writing/scripts
.venv/bin/python -m bookkit.paginate ../../../book
.venv/bin/python -m bookkit.render   ../../../book
.venv/bin/python -m bookkit.merge    ../../../book
.venv/bin/python -m bookkit.verify   ../../../book --css ../assets/interior.css
```

Adjust the relative path to wherever the book directory lives. For a retargeted
trim, pass the geometry to both ends:

```bash
.venv/bin/python -m bookkit.render ../../../book --page-w 6in --page-h 9in
.venv/bin/python -m bookkit.verify ../../../book --width-pt 432 --height-pt 648 \
    --css ../assets/interior.css
```

**Re-run all four after any content edit.** Editing one chapter changes its page
count, which changes every downstream folio.

## The folio offset rule

`.page { counter-increment: page }` fires on the first page, so a file whose
first page should display folio `F` needs `counter-reset: page (F - 1)`.

`bookkit.paginate` writes this from measured page counts. **Never edit a
counter offset by hand.** Hand-assigned offsets are the failure this tool
exists to prevent: they encode a guess about how long each chapter will be, and
a chapter that runs one page over silently renumbers everything after it.

## `book.order`

One filename per line, in assembly order:

```
cover.html
front-matter.html
chapter-01.html
chapter-02.html
appendix-a.html
```

Without it, files are taken in sorted-name order — fine for `chapter-NN.html`,
wrong as soon as front matter and appendices exist.

## One rendering engine

Measurement and printing both run through the **same** Playwright Chromium. This
is not incidental. If layout were measured by one engine and printed by another,
the two could disagree — and verification would certify a page as fitting that
the PDF then clips. `render.py` reuses `measure.py`'s `browser_page()` for this
reason.

For the same reason, `bookkit.render` passes its geometry explicitly rather than
deferring to the stylesheet's `@page` rule, which cannot read the `--page-w` and
`--page-h` tokens.

## The verification gate

`bookkit.verify` exits non-zero on any of these. Each one is silent without the
check, which is why none of them is advisory:

| Hard failure | What it catches |
|---|---|
| Geometry mismatch | A page rendering at the wrong trim |
| Content clipping | Text overflowing `overflow: hidden` and vanishing |
| CSS layering violation | A chapter-local selector unprefixed, or shadowing core |
| Folio discontinuity | Page numbers that do not run continuously |
| Stale manifest | A chapter edited without re-running `paginate` |

It warns, without failing, on **page budget** drift against `STRUCTURE.md` — a
chapter running long is usually a chapter answering two questions, which is a
structural problem to fix in the blueprint rather than a build error.
