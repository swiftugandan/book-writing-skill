# Contributing

## Setup

```bash
cd skills/book-writing/scripts
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/playwright install chromium
.venv/bin/pytest
```

## Where things live

```
skills/book-writing/
  SKILL.md          the router: six phases, which reference to read when
  references/       the knowledge, loaded one phase at a time
  assets/           interior.css and the page templates
  scripts/bookkit/  measurement, pagination, rendering, merging, verification
  scripts/tests/
```

`SKILL.md` is a router, not a manual. It is kept under 900 words by a test, because it
loads on every invocation. Detail belongs in `references/`.

## The rules the tests enforce

Four constraints will fail CI if you change them. Each one prevents a failure that is
otherwise silent:

- **`measure.py` owns the only browser.** `render.py` reuses its `browser_page()`. If
  measurement and printing ran on different Chromium builds they could disagree on
  layout, and verification would certify a page as fitting that the PDF then clips.
- **Core versus chapter-local CSS.** `assets/interior.css` is the core layer. A chapter
  may add diagram CSS inline, prefixed `ch-`, and may never shadow a core selector. One
  chapter redefining `.callout` restyles the whole book, and the damage shows up in a
  chapter nobody was editing.
- **Folio offsets are computed, never written by hand.** `bookkit.paginate` derives them
  from measured page counts.
- **No content from the source book.** A test asserts that no subject matter from
  `specification-driven-delivery-book` appears in the references.

## Testing changes

Unit tests are necessary and not sufficient here. The fixtures build valid book layouts
by hand, so they cannot catch a template that links the wrong path or an asset that fails
to resolve. Anything touching `assets/`, the templates, or the CLIs also needs the
end-to-end path:

```bash
BOOK=$(mktemp -d)/book && mkdir -p "$BOOK"
cp skills/book-writing/assets/interior.css               "$BOOK/interior.css"
cp skills/book-writing/assets/chapter.template.html      "$BOOK/chapter-01.html"
printf 'chapter-01.html\n' > "$BOOK/book.order"

cd skills/book-writing/scripts
.venv/bin/python -m bookkit.paginate "$BOOK"
.venv/bin/python -m bookkit.render   "$BOOK"
.venv/bin/python -m bookkit.merge    "$BOOK"
.venv/bin/python -m bookkit.verify   "$BOOK"
```

CI runs this on every push. A change that passes `pytest` and fails here is exactly the
class of bug the job was added for.

## Prose changes

`SKILL.md` and everything in `references/` is prose that ships. Run it through the
[`avoid-ai-writing`](https://github.com/conorbronsdon/avoid-ai-writing) skill before
opening a pull request. `references/editorial-standards.md` sets a target of at most one
em dash per thousand words, and it applies to the skill's own documentation.

## Pull requests

Keep the change and its test in the same commit. Explain in the body what failure the
change prevents, not only what it does.
