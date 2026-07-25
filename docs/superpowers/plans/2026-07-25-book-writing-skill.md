# book-writing Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a self-contained `book-writing` Claude skill that turns a `drafts/` folder into a structural blueprint, hand-paginated HTML chapters, and a merged, verified PDF.

**Architecture:** A router `SKILL.md` with progressive disclosure into `references/` (authoring and production knowledge), `assets/` (core stylesheet and templates), and `scripts/` (a `bookkit` Python package). All layout measurement and PDF printing go through a single Playwright Chromium instance so measured extents and printed output cannot disagree. The skill directory is self-contained and portable.

**Tech Stack:** Python 3.11+, Playwright (bundled Chromium, for both measurement and PDF printing), pypdf (merge), pytest (tests), uv (dependency management).

## Global Constraints

- Skill lives at `skills/book-writing/`. No plugin or marketplace wrapper.
- The skill directory must be **self-contained** — copying it elsewhere must not break it. Python package, tests, assets, and references all live inside it.
- Page geometry default: **7in × 10in = 504 × 720 pt = 672 × 960 CSS px** at 96 dpi. Conversion: `pt = px * 0.75`.
- Folio mechanism: `body { counter-reset: page N }` + `.page { counter-increment: page }` + `.page-number::after { content: counter(page) }`. The **first page of a file displays folio `N + 1`**. So for a file whose first page is folio `F`, write `counter-reset: page (F - 1)`.
- Chapter-local CSS selectors must be prefixed `ch-` and must never redefine a core selector.
- `verify.py` **hard-fails** (exit 1) on: geometry mismatch, page content overflow (clipping), CSS layering violation, folio discontinuity. It **warns** (exit 0) on page-budget drift.
- The skill carries no subject matter and no prose voice. Never bundle content from the source book.
- Python module invocation is always `uv run --project skills/book-writing/scripts python -m bookkit.<mod>`.
- Every chapter must pass the `avoid-ai-writing` skill before being marked done.

---

## File Structure

```
skills/book-writing/
  SKILL.md                              router: six phases, when to read what
  references/
    blueprint-format.md                 the STRUCTURE.md contract
    chapter-pattern.md                  canonical chapter beat sequence
    editorial-standards.md              voice + rigor; delegates to avoid-ai-writing
    interior-design.md                  tokens, core components, layout discipline
    production.md                       paginate, render, merge, verify
  assets/
    interior.css                        shared core stylesheet
    STRUCTURE.template.md
    chapter.template.html
    front-matter.template.html
    cover.template.html
  scripts/
    pyproject.toml
    bookkit/
      __init__.py
      measure.py                        Playwright: .page extents + geometry
      cssguard.py                       core vs chapter-local selector rules
      manifest.py                       manifest model + folio assignment
      paginate.py                       CLI: measure, write offsets, write manifest
      render.py                         CLI: html -> pdf (same Chromium)
      merge.py                          CLI: pdfs -> book.pdf
      verify.py                         CLI: all checks
    tests/
      conftest.py
      fixtures/
      test_measure.py
      test_cssguard.py
      test_manifest.py
      test_paginate.py
      test_render_merge.py
      test_verify.py
      test_skill_structure.py
      test_end_to_end.py
```

**Responsibilities.** `measure.py` is the only module that opens a browser for layout. `render.py` is the only module that prints PDFs, reusing the same Playwright Chromium. `cssguard.py` and `manifest.py` are pure — no I/O beyond reading text — so they are cheap to test. `paginate.py` and `verify.py` compose the others behind CLIs. Nothing in `bookkit` imports from `references/` or `assets/` except by path at runtime.

---

### Task 1: Scaffold the package and measure page extents

**Files:**
- Create: `skills/book-writing/scripts/pyproject.toml`
- Create: `skills/book-writing/scripts/bookkit/__init__.py`
- Create: `skills/book-writing/scripts/bookkit/measure.py`
- Create: `skills/book-writing/scripts/tests/conftest.py`
- Test: `skills/book-writing/scripts/tests/test_measure.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `PageExtent` frozen dataclass with fields `file: str`, `index: int`, `box_px: float`, `content_px: float`, `width_px: float`, `overflow_px: float`.
  - `measure_file(path: Path) -> list[PageExtent]`
  - `measure_files(paths: Sequence[Path]) -> list[PageExtent]`
  - `PX_PER_PT = 4 / 3` and `px_to_pt(px: float) -> float`
  - Context manager `browser_page()` yielding a Playwright `Page`, reused by `render.py` in Task 4.

- [ ] **Step 1: Create the package manifest**

Create `skills/book-writing/scripts/pyproject.toml`:

```toml
[project]
name = "bookkit"
version = "0.1.0"
description = "Layout measurement, pagination, and production for the book-writing skill"
requires-python = ">=3.11"
dependencies = [
    "playwright>=1.49",
    "pypdf>=5.1",
]

[project.optional-dependencies]
dev = ["pytest>=8.3"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["bookkit"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

Create an empty `skills/book-writing/scripts/bookkit/__init__.py`.

- [ ] **Step 2: Install and verify the toolchain**

```bash
cd skills/book-writing/scripts
uv sync --extra dev
uv run playwright install chromium
uv run python -c "import playwright, pypdf; print('ok')"
```

Expected: prints `ok`. If `uv` is unavailable, use `python -m venv .venv && .venv/bin/pip install -e '.[dev]'`.

- [ ] **Step 3: Write the shared test fixture helper**

Create `skills/book-writing/scripts/tests/conftest.py`:

```python
from pathlib import Path

import pytest

PAGE_CSS = """
@page { size: 7in 10in; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body { counter-reset: page 0; }
.page {
  position: relative;
  width: 7in;
  height: 10in;
  padding: .65in;
  overflow: hidden;
  break-after: page;
  counter-increment: page;
}
.page-number::after { content: counter(page); }
"""


def write_book(dir_: Path, name: str, pages: list[str], extra_css: str = "") -> Path:
    """Write a minimal book page-file with one .page div per entry in `pages`."""
    body = "\n".join(f'<div class="page">{p}</div>' for p in pages)
    html = (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        f"<style>{PAGE_CSS}{extra_css}</style></head><body>{body}</body></html>"
    )
    path = dir_ / name
    path.write_text(html, encoding="utf-8")
    return path


@pytest.fixture
def book_dir(tmp_path: Path) -> Path:
    d = tmp_path / "book"
    d.mkdir()
    return d
```

- [ ] **Step 4: Write the failing test**

Create `skills/book-writing/scripts/tests/test_measure.py`:

```python
from pathlib import Path

from bookkit.measure import PageExtent, measure_file, measure_files, px_to_pt
from tests.conftest import write_book


def test_px_to_pt_converts_at_96dpi():
    assert px_to_pt(672) == 504.0
    assert px_to_pt(960) == 720.0


def test_measures_one_extent_per_page_div(book_dir: Path):
    path = write_book(book_dir, "chapter-01.html", ["<p>one</p>", "<p>two</p>"])

    extents = measure_file(path)

    assert [e.index for e in extents] == [0, 1]
    assert all(isinstance(e, PageExtent) for e in extents)
    assert all(e.file == "chapter-01.html" for e in extents)


def test_page_box_matches_declared_geometry(book_dir: Path):
    path = write_book(book_dir, "chapter-01.html", ["<p>short</p>"])

    extent = measure_file(path)[0]

    assert px_to_pt(extent.width_px) == 504.0
    assert px_to_pt(extent.box_px) == 720.0


def test_short_page_reports_no_overflow(book_dir: Path):
    path = write_book(book_dir, "chapter-01.html", ["<p>short</p>"])

    assert measure_file(path)[0].overflow_px <= 0


def test_overlong_page_reports_positive_overflow(book_dir: Path):
    tall = "<p>line</p>" * 400
    path = write_book(book_dir, "chapter-01.html", [tall])

    extent = measure_file(path)[0]

    assert extent.overflow_px > 0
    assert extent.content_px > extent.box_px


def test_measure_files_concatenates_in_argument_order(book_dir: Path):
    a = write_book(book_dir, "a.html", ["<p>a</p>"])
    b = write_book(book_dir, "b.html", ["<p>b</p>", "<p>b2</p>"])

    extents = measure_files([a, b])

    assert [(e.file, e.index) for e in extents] == [
        ("a.html", 0),
        ("b.html", 0),
        ("b.html", 1),
    ]
```

- [ ] **Step 5: Run the test to verify it fails**

```bash
cd skills/book-writing/scripts && uv run pytest tests/test_measure.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'bookkit.measure'`.

- [ ] **Step 6: Write the implementation**

Create `skills/book-writing/scripts/bookkit/measure.py`:

```python
"""Layout measurement for hand-paginated book pages.

This module owns the only browser used for layout. `render.py` reuses
`browser_page()` so that measured extents and printed PDFs come from the same
Chromium build — if they diverged, verification could certify a page as fitting
that the PDF then clips.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Sequence

from playwright.sync_api import Page, sync_playwright

PX_PER_PT = 4 / 3

_EXTENT_JS = """
() => Array.from(document.querySelectorAll('.page')).map((el, index) => {
  const style = getComputedStyle(el);
  const padTop = parseFloat(style.paddingTop);
  const padBottom = parseFloat(style.paddingBottom);
  let contentBottom = 0;
  for (const child of el.children) {
    if (getComputedStyle(child).position === 'absolute') continue;
    const bottom = child.offsetTop + child.offsetHeight;
    if (bottom > contentBottom) contentBottom = bottom;
  }
  return {
    index,
    box_px: el.getBoundingClientRect().height,
    width_px: el.getBoundingClientRect().width,
    content_px: contentBottom + padTop + padBottom,
  };
});
"""


def px_to_pt(px: float) -> float:
    """Convert CSS pixels (96 dpi) to PostScript points (72 dpi)."""
    return px / PX_PER_PT


@dataclass(frozen=True)
class PageExtent:
    """One `.page` element's measured box and content extent, in CSS pixels."""

    file: str
    index: int
    box_px: float
    content_px: float
    width_px: float

    @property
    def overflow_px(self) -> float:
        """Positive means content is clipped by `overflow: hidden`."""
        return self.content_px - self.box_px


@contextmanager
def browser_page() -> Iterator[Page]:
    """Yield a Chromium page. Shared by measurement and PDF printing."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page()
            yield page
        finally:
            browser.close()


def _extents_for(page: Page, path: Path) -> list[PageExtent]:
    page.goto(path.resolve().as_uri(), wait_until="load")
    page.emulate_media(media="print")
    raw = page.evaluate(_EXTENT_JS)
    return [
        PageExtent(
            file=path.name,
            index=item["index"],
            box_px=item["box_px"],
            content_px=item["content_px"],
            width_px=item["width_px"],
        )
        for item in raw
    ]


def measure_file(path: Path) -> list[PageExtent]:
    """Measure every `.page` in one HTML file."""
    with browser_page() as page:
        return _extents_for(page, path)


def measure_files(paths: Sequence[Path]) -> list[PageExtent]:
    """Measure several files in argument order, reusing one browser."""
    results: list[PageExtent] = []
    with browser_page() as page:
        for path in paths:
            results.extend(_extents_for(page, path))
    return results
```

- [ ] **Step 7: Run the test to verify it passes**

```bash
cd skills/book-writing/scripts && uv run pytest tests/test_measure.py -v
```

Expected: 6 passed.

- [ ] **Step 8: Commit**

```bash
git add skills/book-writing/scripts
git commit -m "feat(bookkit): measure hand-paginated page extents via Playwright"
```

---

### Task 2: Guard the two-layer CSS boundary

**Files:**
- Create: `skills/book-writing/scripts/bookkit/cssguard.py`
- Test: `skills/book-writing/scripts/tests/test_cssguard.py`

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces:
  - `CssViolation` frozen dataclass with fields `file: str`, `selector: str`, `reason: str` where `reason` is `"unprefixed"` or `"shadows-core"`.
  - `core_selectors(css_path: Path) -> frozenset[str]`
  - `local_selectors(html_path: Path) -> frozenset[str]`
  - `check_css_layering(html_path: Path, css_path: Path) -> list[CssViolation]`
  - `LOCAL_PREFIX = "ch-"`

- [ ] **Step 1: Write the failing test**

Create `skills/book-writing/scripts/tests/test_cssguard.py`:

```python
from pathlib import Path

from bookkit.cssguard import (
    CssViolation,
    check_css_layering,
    core_selectors,
    local_selectors,
)

CORE = """
:root { --ink: #242424; }
.page { width: 7in; }
.page-number::after { content: counter(page); }
.callout { padding: 13px; }
.callout.teal { border-top-color: teal; }
h1, h2, .sans { font-family: sans-serif; }
"""


def _write(tmp_path: Path, css: str, inline: str) -> tuple[Path, Path]:
    css_path = tmp_path / "interior.css"
    css_path.write_text(css, encoding="utf-8")
    html_path = tmp_path / "chapter-01.html"
    html_path.write_text(
        f"<!doctype html><html><head><style>{inline}</style></head>"
        "<body><div class='page'></div></body></html>",
        encoding="utf-8",
    )
    return html_path, css_path


def test_core_selectors_extracts_class_names(tmp_path: Path):
    css_path = tmp_path / "interior.css"
    css_path.write_text(CORE, encoding="utf-8")

    assert core_selectors(css_path) == {"page", "page-number", "callout", "teal", "sans"}


def test_local_selectors_reads_inline_style_block(tmp_path: Path):
    html_path, _ = _write(tmp_path, CORE, ".ch-kanban { display: grid; }")

    assert local_selectors(html_path) == {"ch-kanban"}


def test_local_selectors_empty_when_no_style_block(tmp_path: Path):
    html_path = tmp_path / "chapter-01.html"
    html_path.write_text("<!doctype html><html><body></body></html>", encoding="utf-8")

    assert local_selectors(html_path) == frozenset()


def test_prefixed_novel_selector_is_allowed(tmp_path: Path):
    html_path, css_path = _write(tmp_path, CORE, ".ch-usecase-map { display: grid; }")

    assert check_css_layering(html_path, css_path) == []


def test_unprefixed_local_selector_is_a_violation(tmp_path: Path):
    html_path, css_path = _write(tmp_path, CORE, ".kanban { display: grid; }")

    assert check_css_layering(html_path, css_path) == [
        CssViolation(file="chapter-01.html", selector="kanban", reason="unprefixed")
    ]


def test_local_redefinition_of_core_selector_is_a_violation(tmp_path: Path):
    html_path, css_path = _write(tmp_path, CORE, ".callout { padding: 40px; }")

    assert check_css_layering(html_path, css_path) == [
        CssViolation(file="chapter-01.html", selector="callout", reason="shadows-core")
    ]


def test_prefixed_name_colliding_with_core_is_still_shadowing(tmp_path: Path):
    core = CORE + "\n.ch-legacy { color: red; }\n"
    html_path, css_path = _write(tmp_path, core, ".ch-legacy { color: blue; }")

    assert check_css_layering(html_path, css_path) == [
        CssViolation(file="chapter-01.html", selector="ch-legacy", reason="shadows-core")
    ]


def test_violations_are_sorted_by_selector(tmp_path: Path):
    html_path, css_path = _write(tmp_path, CORE, ".zebra{color:red}.alpha{color:blue}")

    assert [v.selector for v in check_css_layering(html_path, css_path)] == [
        "alpha",
        "zebra",
    ]
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd skills/book-writing/scripts && uv run pytest tests/test_cssguard.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'bookkit.cssguard'`.

- [ ] **Step 3: Write the implementation**

Create `skills/book-writing/scripts/bookkit/cssguard.py`:

```python
"""Enforce the two-layer CSS boundary.

The core layer (`assets/interior.css`) is shared by every page file. A chapter
may add its own diagram components in an inline `<style>` block, but those must
be prefixed `ch-` and must never redefine a core selector — otherwise one
chapter silently changes the look of the whole book.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

LOCAL_PREFIX = "ch-"

_STYLE_BLOCK = re.compile(r"<style[^>]*>(.*?)</style>", re.DOTALL | re.IGNORECASE)
_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_DECLARATIONS = re.compile(r"\{[^{}]*\}", re.DOTALL)
_CLASS_NAME = re.compile(r"\.(-?[_a-zA-Z][_a-zA-Z0-9-]*)")


@dataclass(frozen=True)
class CssViolation:
    """A chapter-local selector that breaks the layering rule."""

    file: str
    selector: str
    reason: str  # "unprefixed" | "shadows-core"


def _class_names(css: str) -> frozenset[str]:
    """Every class name appearing in a selector position."""
    without_comments = _COMMENT.sub(" ", css)
    selectors_only = _DECLARATIONS.sub(" ", without_comments)
    return frozenset(_CLASS_NAME.findall(selectors_only))


def core_selectors(css_path: Path) -> frozenset[str]:
    """Class names defined by the shared core stylesheet."""
    return _class_names(css_path.read_text(encoding="utf-8"))


def local_selectors(html_path: Path) -> frozenset[str]:
    """Class names defined in a page file's inline `<style>` blocks."""
    html = html_path.read_text(encoding="utf-8")
    blocks = _STYLE_BLOCK.findall(html)
    names: set[str] = set()
    for block in blocks:
        names |= _class_names(block)
    return frozenset(names)


def check_css_layering(html_path: Path, css_path: Path) -> list[CssViolation]:
    """Report every chapter-local selector that is unprefixed or shadows core."""
    core = core_selectors(css_path)
    violations = []
    for name in local_selectors(html_path):
        if name in core:
            reason = "shadows-core"
        elif not name.startswith(LOCAL_PREFIX):
            reason = "unprefixed"
        else:
            continue
        violations.append(
            CssViolation(file=html_path.name, selector=name, reason=reason)
        )
    return sorted(violations, key=lambda v: v.selector)
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd skills/book-writing/scripts && uv run pytest tests/test_cssguard.py -v
```

Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/book-writing/scripts/bookkit/cssguard.py skills/book-writing/scripts/tests/test_cssguard.py
git commit -m "feat(bookkit): enforce core vs chapter-local CSS layering"
```

---

### Task 3: Model the manifest and assign folios

**Files:**
- Create: `skills/book-writing/scripts/bookkit/manifest.py`
- Test: `skills/book-writing/scripts/tests/test_manifest.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `ManifestEntry` frozen dataclass: `file: str`, `pages: int`, `start_folio: int`.
  - `Manifest` frozen dataclass: `entries: tuple[ManifestEntry, ...]`, with `total_pages() -> int`, `to_json() -> str`, `Manifest.from_json(text: str) -> Manifest`, `entry_for(file: str) -> ManifestEntry`.
  - `assign_folios(counts: Sequence[tuple[str, int]], first_folio: int = 1) -> Manifest`
  - `folio_discontinuities(manifest: Manifest, first_folio: int = 1) -> list[str]`

- [ ] **Step 1: Write the failing test**

Create `skills/book-writing/scripts/tests/test_manifest.py`:

```python
import pytest

from bookkit.manifest import (
    Manifest,
    ManifestEntry,
    assign_folios,
    folio_discontinuities,
)


def test_assign_folios_starts_at_one_by_default():
    manifest = assign_folios([("front-matter.html", 4), ("chapter-01.html", 12)])

    assert manifest.entries == (
        ManifestEntry(file="front-matter.html", pages=4, start_folio=1),
        ManifestEntry(file="chapter-01.html", pages=12, start_folio=5),
    )


def test_assign_folios_honours_a_custom_first_folio():
    manifest = assign_folios([("chapter-01.html", 3)], first_folio=9)

    assert manifest.entries[0].start_folio == 9


def test_assign_folios_accumulates_across_many_files():
    manifest = assign_folios([("a.html", 2), ("b.html", 5), ("c.html", 1)])

    assert [e.start_folio for e in manifest.entries] == [1, 3, 8]


def test_total_pages_sums_entries():
    assert assign_folios([("a.html", 2), ("b.html", 5)]).total_pages() == 7


def test_entry_for_returns_the_named_entry():
    manifest = assign_folios([("a.html", 2), ("b.html", 5)])

    assert manifest.entry_for("b.html").start_folio == 3


def test_entry_for_raises_on_unknown_file():
    manifest = assign_folios([("a.html", 2)])

    with pytest.raises(KeyError, match="missing.html"):
        manifest.entry_for("missing.html")


def test_json_round_trips():
    manifest = assign_folios([("a.html", 2), ("b.html", 5)])

    assert Manifest.from_json(manifest.to_json()) == manifest


def test_json_is_human_readable_and_stable():
    text = assign_folios([("a.html", 2)]).to_json()

    assert '"file": "a.html"' in text
    assert text.endswith("\n")


def test_no_discontinuities_in_a_well_formed_manifest():
    assert folio_discontinuities(assign_folios([("a.html", 2), ("b.html", 5)])) == []


def test_detects_a_gap_between_entries():
    manifest = Manifest(
        entries=(
            ManifestEntry(file="a.html", pages=2, start_folio=1),
            ManifestEntry(file="b.html", pages=5, start_folio=9),
        )
    )

    problems = folio_discontinuities(manifest)

    assert len(problems) == 1
    assert "b.html" in problems[0]
    assert "expected 3" in problems[0]


def test_detects_a_wrong_first_folio():
    manifest = Manifest(entries=(ManifestEntry(file="a.html", pages=2, start_folio=4),))

    assert "expected 1" in folio_discontinuities(manifest)[0]
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd skills/book-writing/scripts && uv run pytest tests/test_manifest.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'bookkit.manifest'`.

- [ ] **Step 3: Write the implementation**

Create `skills/book-writing/scripts/bookkit/manifest.py`:

```python
"""The book manifest: file order, measured page counts, and folio assignment.

Hand-assigned folio offsets are the source book's sharpest failure mode — a
chapter that runs one page long makes every downstream folio wrong, silently.
The manifest replaces the guess with measured values.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class ManifestEntry:
    """One page file's position in the assembled book."""

    file: str
    pages: int
    start_folio: int


@dataclass(frozen=True)
class Manifest:
    """Ordered page files with their measured extents and folio starts."""

    entries: tuple[ManifestEntry, ...]

    def total_pages(self) -> int:
        return sum(entry.pages for entry in self.entries)

    def entry_for(self, file: str) -> ManifestEntry:
        for entry in self.entries:
            if entry.file == file:
                return entry
        raise KeyError(file)

    def to_json(self) -> str:
        payload = {
            "entries": [
                {
                    "file": entry.file,
                    "pages": entry.pages,
                    "start_folio": entry.start_folio,
                }
                for entry in self.entries
            ],
            "total_pages": self.total_pages(),
        }
        return json.dumps(payload, indent=2) + "\n"

    @classmethod
    def from_json(cls, text: str) -> "Manifest":
        payload = json.loads(text)
        return cls(
            entries=tuple(
                ManifestEntry(
                    file=item["file"],
                    pages=item["pages"],
                    start_folio=item["start_folio"],
                )
                for item in payload["entries"]
            )
        )


def assign_folios(
    counts: Sequence[tuple[str, int]], first_folio: int = 1
) -> Manifest:
    """Build a manifest from `(file, page_count)` pairs in assembly order."""
    entries = []
    folio = first_folio
    for file, pages in counts:
        entries.append(ManifestEntry(file=file, pages=pages, start_folio=folio))
        folio += pages
    return Manifest(entries=tuple(entries))


def folio_discontinuities(manifest: Manifest, first_folio: int = 1) -> list[str]:
    """Report any entry whose start folio does not follow from its predecessor."""
    problems = []
    expected = first_folio
    for entry in manifest.entries:
        if entry.start_folio != expected:
            problems.append(
                f"{entry.file}: starts at folio {entry.start_folio}, "
                f"expected {expected}"
            )
        expected = entry.start_folio + entry.pages
    return problems
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd skills/book-writing/scripts && uv run pytest tests/test_manifest.py -v
```

Expected: 11 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/book-writing/scripts/bookkit/manifest.py skills/book-writing/scripts/tests/test_manifest.py
git commit -m "feat(bookkit): model the manifest and assign folios from measured counts"
```

---

### Task 4: Rewrite counter offsets from measured extents

**Files:**
- Create: `skills/book-writing/scripts/bookkit/paginate.py`
- Test: `skills/book-writing/scripts/tests/test_paginate.py`

**Interfaces:**
- Consumes: `measure_files`, `PageExtent` (Task 1); `Manifest`, `assign_folios` (Task 3).
- Produces:
  - `set_counter_offset(html: str, start_folio: int) -> str` — rewrites the `counter-reset: page N` declaration to `N = start_folio - 1`; raises `ValueError` if no declaration is present.
  - `page_counts(extents: Sequence[PageExtent]) -> list[tuple[str, int]]`
  - `paginate(book_dir: Path, order: Sequence[str], first_folio: int = 1) -> Manifest` — measures, rewrites each file in place, writes `book.manifest.json`, returns the manifest.
  - `MANIFEST_NAME = "book.manifest.json"`
  - CLI: `python -m bookkit.paginate <book_dir> [--first-folio N]`, reading file order from `book.order` (one filename per line) if present, else sorted glob of `*.html`.

- [ ] **Step 1: Write the failing test**

Create `skills/book-writing/scripts/tests/test_paginate.py`:

```python
from pathlib import Path

import pytest

from bookkit.manifest import Manifest
from bookkit.measure import PageExtent
from bookkit.paginate import (
    MANIFEST_NAME,
    page_counts,
    paginate,
    set_counter_offset,
)
from tests.conftest import write_book


def test_set_counter_offset_is_one_less_than_the_first_folio():
    css = "body { counter-reset: page 0; }"

    assert set_counter_offset(css, start_folio=51) == "body { counter-reset: page 50; }"


def test_set_counter_offset_of_folio_one_writes_zero():
    assert set_counter_offset("counter-reset: page 99;", 1) == "counter-reset: page 0;"


def test_set_counter_offset_tolerates_whitespace_variants():
    assert set_counter_offset("counter-reset:page   7 ;", 4) == "counter-reset: page 3;"


def test_set_counter_offset_raises_when_declaration_is_absent():
    with pytest.raises(ValueError, match="counter-reset"):
        set_counter_offset("body { margin: 0; }", 1)


def test_page_counts_groups_extents_by_file_in_order():
    extents = [
        PageExtent(file="a.html", index=0, box_px=960, content_px=10, width_px=672),
        PageExtent(file="b.html", index=0, box_px=960, content_px=10, width_px=672),
        PageExtent(file="b.html", index=1, box_px=960, content_px=10, width_px=672),
    ]

    assert page_counts(extents) == [("a.html", 1), ("b.html", 2)]


def test_paginate_writes_a_manifest_with_measured_counts(book_dir: Path):
    write_book(book_dir, "front-matter.html", ["<p>a</p>", "<p>b</p>"])
    write_book(book_dir, "chapter-01.html", ["<p>c</p>", "<p>d</p>", "<p>e</p>"])

    manifest = paginate(book_dir, ["front-matter.html", "chapter-01.html"])

    assert [(e.file, e.pages, e.start_folio) for e in manifest.entries] == [
        ("front-matter.html", 2, 1),
        ("chapter-01.html", 3, 3),
    ]


def test_paginate_persists_the_manifest_to_disk(book_dir: Path):
    write_book(book_dir, "a.html", ["<p>a</p>"])

    manifest = paginate(book_dir, ["a.html"])

    written = Manifest.from_json((book_dir / MANIFEST_NAME).read_text(encoding="utf-8"))
    assert written == manifest


def test_paginate_rewrites_each_files_counter_offset(book_dir: Path):
    write_book(book_dir, "a.html", ["<p>a</p>", "<p>b</p>"])
    write_book(book_dir, "b.html", ["<p>c</p>"])

    paginate(book_dir, ["a.html", "b.html"])

    assert "counter-reset: page 0;" in (book_dir / "a.html").read_text(encoding="utf-8")
    assert "counter-reset: page 2;" in (book_dir / "b.html").read_text(encoding="utf-8")


def test_paginate_is_idempotent(book_dir: Path):
    write_book(book_dir, "a.html", ["<p>a</p>", "<p>b</p>"])
    write_book(book_dir, "b.html", ["<p>c</p>"])

    first = paginate(book_dir, ["a.html", "b.html"])
    snapshot = (book_dir / "b.html").read_text(encoding="utf-8")
    second = paginate(book_dir, ["a.html", "b.html"])

    assert first == second
    assert (book_dir / "b.html").read_text(encoding="utf-8") == snapshot


def test_paginate_honours_a_custom_first_folio(book_dir: Path):
    write_book(book_dir, "a.html", ["<p>a</p>"])

    paginate(book_dir, ["a.html"], first_folio=13)

    assert "counter-reset: page 12;" in (book_dir / "a.html").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd skills/book-writing/scripts && uv run pytest tests/test_paginate.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'bookkit.paginate'`.

- [ ] **Step 3: Write the implementation**

Create `skills/book-writing/scripts/bookkit/paginate.py`:

```python
"""Assign folios from measured page counts and write them into the sources.

Because `.page { counter-increment: page }` fires on the first page, a file
whose first page should display folio F needs `counter-reset: page (F - 1)`.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Sequence

from bookkit.manifest import Manifest, assign_folios
from bookkit.measure import PageExtent, measure_files

MANIFEST_NAME = "book.manifest.json"
ORDER_NAME = "book.order"

_COUNTER_RESET = re.compile(r"counter-reset\s*:\s*page\s+(-?\d+)\s*;")


def set_counter_offset(html: str, start_folio: int) -> str:
    """Rewrite the `counter-reset: page N` declaration for a given first folio."""
    replacement = f"counter-reset: page {start_folio - 1};"
    rewritten, count = _COUNTER_RESET.subn(replacement, html)
    if count == 0:
        raise ValueError("no `counter-reset: page N` declaration found")
    return rewritten


def page_counts(extents: Sequence[PageExtent]) -> list[tuple[str, int]]:
    """Collapse per-page extents into `(file, page_count)` pairs, order preserved."""
    counts: list[tuple[str, int]] = []
    for extent in extents:
        if counts and counts[-1][0] == extent.file:
            counts[-1] = (extent.file, counts[-1][1] + 1)
        else:
            counts.append((extent.file, 1))
    return counts


def read_order(book_dir: Path) -> list[str]:
    """Assembly order from `book.order`, else every HTML file sorted by name."""
    order_file = book_dir / ORDER_NAME
    if order_file.exists():
        lines = order_file.read_text(encoding="utf-8").splitlines()
        return [line.strip() for line in lines if line.strip()]
    return sorted(path.name for path in book_dir.glob("*.html"))


def paginate(
    book_dir: Path, order: Sequence[str], first_folio: int = 1
) -> Manifest:
    """Measure, assign folios, rewrite counter offsets, and write the manifest."""
    extents = measure_files([book_dir / name for name in order])
    manifest = assign_folios(page_counts(extents), first_folio=first_folio)
    for entry in manifest.entries:
        path = book_dir / entry.file
        path.write_text(
            set_counter_offset(path.read_text(encoding="utf-8"), entry.start_folio),
            encoding="utf-8",
        )
    (book_dir / MANIFEST_NAME).write_text(manifest.to_json(), encoding="utf-8")
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Paginate a book directory.")
    parser.add_argument("book_dir", type=Path)
    parser.add_argument("--first-folio", type=int, default=1)
    args = parser.parse_args(argv)

    manifest = paginate(
        args.book_dir, read_order(args.book_dir), first_folio=args.first_folio
    )
    for entry in manifest.entries:
        print(f"{entry.file:<28} {entry.pages:>3} pages  folio {entry.start_folio}")
    print(f"{'TOTAL':<28} {manifest.total_pages():>3} pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd skills/book-writing/scripts && uv run pytest tests/test_paginate.py -v
```

Expected: 10 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/book-writing/scripts/bookkit/paginate.py skills/book-writing/scripts/tests/test_paginate.py
git commit -m "feat(bookkit): derive folio offsets from measured page counts"
```

---

### Task 5: Render and merge PDFs

**Files:**
- Create: `skills/book-writing/scripts/bookkit/render.py`
- Create: `skills/book-writing/scripts/bookkit/merge.py`
- Test: `skills/book-writing/scripts/tests/test_render_merge.py`

**Interfaces:**
- Consumes: `browser_page` (Task 1); `Manifest`, `MANIFEST_NAME` (Tasks 3–4).
- Produces:
  - `render.py`: `render_all(book_dir: Path, manifest: Manifest, out_dir: Path, page_w: str = "7in", page_h: str = "10in") -> list[Path]`; CLI `python -m bookkit.render <book_dir> [--out DIR] [--page-w W] [--page-h H]`.
  - `merge.py`: `merge(pdfs: Sequence[Path], out: Path) -> int` returning the merged page count; `pdf_geometry_pt(pdf: Path) -> list[tuple[float, float]]`; CLI `python -m bookkit.merge <book_dir> [--out FILE]`.

- [ ] **Step 1: Write the failing test**

Create `skills/book-writing/scripts/tests/test_render_merge.py`:

```python
from pathlib import Path

from bookkit.manifest import assign_folios
from bookkit.merge import merge, pdf_geometry_pt
from bookkit.render import render_all
from tests.conftest import write_book


def test_render_all_writes_one_pdf_per_source(book_dir: Path):
    write_book(book_dir, "a.html", ["<p>a</p>"])
    write_book(book_dir, "b.html", ["<p>b</p>", "<p>c</p>"])
    manifest = assign_folios([("a.html", 1), ("b.html", 2)])

    pdfs = render_all(book_dir, manifest, book_dir / "out")

    assert [p.name for p in pdfs] == ["a.pdf", "b.pdf"]
    assert all(p.exists() and p.stat().st_size > 0 for p in pdfs)


def test_rendered_pages_use_the_declared_geometry(book_dir: Path):
    write_book(book_dir, "a.html", ["<p>a</p>", "<p>b</p>"])
    manifest = assign_folios([("a.html", 2)])

    pdfs = render_all(book_dir, manifest, book_dir / "out")

    for width, height in pdf_geometry_pt(pdfs[0]):
        assert round(width) == 504
        assert round(height) == 720


def test_rendered_page_count_matches_the_manifest(book_dir: Path):
    write_book(book_dir, "a.html", ["<p>a</p>", "<p>b</p>", "<p>c</p>"])
    manifest = assign_folios([("a.html", 3)])

    pdfs = render_all(book_dir, manifest, book_dir / "out")

    assert len(pdf_geometry_pt(pdfs[0])) == 3


def test_merge_concatenates_in_argument_order(book_dir: Path):
    write_book(book_dir, "a.html", ["<p>a</p>"])
    write_book(book_dir, "b.html", ["<p>b</p>", "<p>c</p>"])
    manifest = assign_folios([("a.html", 1), ("b.html", 2)])
    pdfs = render_all(book_dir, manifest, book_dir / "out")

    total = merge(pdfs, book_dir / "book.pdf")

    assert total == 3
    assert len(pdf_geometry_pt(book_dir / "book.pdf")) == 3


def test_merge_creates_missing_parent_directories(book_dir: Path):
    write_book(book_dir, "a.html", ["<p>a</p>"])
    manifest = assign_folios([("a.html", 1)])
    pdfs = render_all(book_dir, manifest, book_dir / "out")

    merge(pdfs, book_dir / "dist" / "book.pdf")

    assert (book_dir / "dist" / "book.pdf").exists()
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd skills/book-writing/scripts && uv run pytest tests/test_render_merge.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'bookkit.merge'`.

- [ ] **Step 3: Write the renderer**

Create `skills/book-writing/scripts/bookkit/render.py`:

```python
"""Print one PDF per page file, using the same Chromium that measured them."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from bookkit.manifest import Manifest
from bookkit.measure import browser_page
from bookkit.paginate import MANIFEST_NAME


def render_all(
    book_dir: Path,
    manifest: Manifest,
    out_dir: Path,
    page_w: str = "7in",
    page_h: str = "10in",
) -> list[Path]:
    """Render every file in the manifest to `out_dir`, returning the PDF paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with browser_page() as page:
        for entry in manifest.entries:
            source = book_dir / entry.file
            target = out_dir / f"{Path(entry.file).stem}.pdf"
            page.goto(source.resolve().as_uri(), wait_until="load")
            page.emulate_media(media="print")
            page.pdf(
                path=str(target),
                width=page_w,
                height=page_h,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                print_background=True,
                prefer_css_page_size=True,
            )
            written.append(target)
    return written


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a book directory to PDFs.")
    parser.add_argument("book_dir", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--page-w", default="7in")
    parser.add_argument("--page-h", default="10in")
    args = parser.parse_args(argv)

    manifest = Manifest.from_json(
        (args.book_dir / MANIFEST_NAME).read_text(encoding="utf-8")
    )
    out_dir = args.out or args.book_dir / "pdf"
    for path in render_all(
        args.book_dir, manifest, out_dir, args.page_w, args.page_h
    ):
        print(f"rendered {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Write the merger**

Create `skills/book-writing/scripts/bookkit/merge.py`:

```python
"""Assemble per-file PDFs into the finished book, in manifest order."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from pypdf import PdfReader, PdfWriter

from bookkit.manifest import Manifest
from bookkit.paginate import MANIFEST_NAME


def pdf_geometry_pt(pdf: Path) -> list[tuple[float, float]]:
    """Each page's (width, height) in PostScript points."""
    reader = PdfReader(str(pdf))
    return [
        (float(page.mediabox.width), float(page.mediabox.height))
        for page in reader.pages
    ]


def merge(pdfs: Sequence[Path], out: Path) -> int:
    """Concatenate `pdfs` in order into `out`, returning the total page count."""
    out.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    for pdf in pdfs:
        for page in PdfReader(str(pdf)).pages:
            writer.add_page(page)
    with out.open("wb") as handle:
        writer.write(handle)
    return len(writer.pages)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Merge rendered PDFs into one book.")
    parser.add_argument("book_dir", type=Path)
    parser.add_argument("--pdf-dir", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    manifest = Manifest.from_json(
        (args.book_dir / MANIFEST_NAME).read_text(encoding="utf-8")
    )
    pdf_dir = args.pdf_dir or args.book_dir / "pdf"
    pdfs = [pdf_dir / f"{Path(e.file).stem}.pdf" for e in manifest.entries]
    out = args.out or args.book_dir / "book.pdf"

    total = merge(pdfs, out)
    print(f"merged {len(pdfs)} files into {out} ({total} pages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run the test to verify it passes**

```bash
cd skills/book-writing/scripts && uv run pytest tests/test_render_merge.py -v
```

Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add skills/book-writing/scripts/bookkit/render.py skills/book-writing/scripts/bookkit/merge.py skills/book-writing/scripts/tests/test_render_merge.py
git commit -m "feat(bookkit): render page files and merge them into the book PDF"
```

---

### Task 6: Compose the verification gate

**Files:**
- Create: `skills/book-writing/scripts/bookkit/verify.py`
- Test: `skills/book-writing/scripts/tests/test_verify.py`

**Interfaces:**
- Consumes: `measure_files`, `px_to_pt` (Task 1); `check_css_layering` (Task 2); `Manifest`, `folio_discontinuities` (Task 3); `MANIFEST_NAME`, `page_counts` (Task 4).
- Produces:
  - `Finding` frozen dataclass: `level: str` (`"error"` or `"warning"`), `file: str`, `message: str`.
  - `verify(book_dir: Path, manifest: Manifest, css_path: Path, expected_pt: tuple[float, float] = (504.0, 720.0), budget: dict[str, int] | None = None) -> list[Finding]`
  - `has_errors(findings: Sequence[Finding]) -> bool`
  - CLI: `python -m bookkit.verify <book_dir> [--css PATH] [--width-pt W] [--height-pt H]`, exit 1 when any error is present.
  - `GEOMETRY_TOLERANCE_PT = 0.5`, `OVERFLOW_TOLERANCE_PX = 1.0`

- [ ] **Step 1: Write the failing test**

Create `skills/book-writing/scripts/tests/test_verify.py`:

```python
from pathlib import Path

from bookkit.manifest import Manifest, ManifestEntry, assign_folios
from bookkit.verify import Finding, has_errors, verify
from tests.conftest import write_book

CORE_CSS = ".page { width: 7in; }\n.callout { padding: 13px; }\n"


def _css(tmp_path: Path) -> Path:
    path = tmp_path / "interior.css"
    path.write_text(CORE_CSS, encoding="utf-8")
    return path


def test_clean_book_produces_no_findings(book_dir: Path, tmp_path: Path):
    write_book(book_dir, "a.html", ["<p>a</p>", "<p>b</p>"])
    manifest = assign_folios([("a.html", 2)])

    assert verify(book_dir, manifest, _css(tmp_path)) == []


def test_overflowing_page_is_an_error(book_dir: Path, tmp_path: Path):
    write_book(book_dir, "a.html", ["<p>x</p>" * 400])
    manifest = assign_folios([("a.html", 1)])

    findings = verify(book_dir, manifest, _css(tmp_path))

    assert has_errors(findings)
    assert any("clipped" in f.message for f in findings if f.level == "error")


def test_wrong_geometry_is_an_error(book_dir: Path, tmp_path: Path):
    write_book(book_dir, "a.html", ["<p>a</p>"])
    manifest = assign_folios([("a.html", 1)])

    findings = verify(book_dir, manifest, _css(tmp_path), expected_pt=(432.0, 648.0))

    assert has_errors(findings)
    assert any("geometry" in f.message for f in findings)


def test_unprefixed_local_selector_is_an_error(book_dir: Path, tmp_path: Path):
    write_book(book_dir, "a.html", ["<p>a</p>"], extra_css=".kanban { color: red; }")
    manifest = assign_folios([("a.html", 1)])

    findings = verify(book_dir, manifest, _css(tmp_path))

    assert has_errors(findings)
    assert any("kanban" in f.message for f in findings)


def test_local_redefinition_of_core_is_an_error(book_dir: Path, tmp_path: Path):
    write_book(book_dir, "a.html", ["<p>a</p>"], extra_css=".callout { padding: 0; }")
    manifest = assign_folios([("a.html", 1)])

    findings = verify(book_dir, manifest, _css(tmp_path))

    assert any("shadows-core" in f.message for f in findings if f.level == "error")


def test_folio_discontinuity_is_an_error(book_dir: Path, tmp_path: Path):
    write_book(book_dir, "a.html", ["<p>a</p>"])
    write_book(book_dir, "b.html", ["<p>b</p>"])
    broken = Manifest(
        entries=(
            ManifestEntry(file="a.html", pages=1, start_folio=1),
            ManifestEntry(file="b.html", pages=1, start_folio=7),
        )
    )

    findings = verify(book_dir, broken, _css(tmp_path))

    assert any("folio" in f.message for f in findings if f.level == "error")


def test_stale_manifest_page_count_is_an_error(book_dir: Path, tmp_path: Path):
    write_book(book_dir, "a.html", ["<p>a</p>", "<p>b</p>", "<p>c</p>"])
    stale = assign_folios([("a.html", 2)])

    findings = verify(book_dir, stale, _css(tmp_path))

    assert any("stale" in f.message for f in findings if f.level == "error")


def test_budget_drift_is_a_warning_not_an_error(book_dir: Path, tmp_path: Path):
    write_book(book_dir, "a.html", ["<p>a</p>", "<p>b</p>", "<p>c</p>"])
    manifest = assign_folios([("a.html", 3)])

    findings = verify(book_dir, manifest, _css(tmp_path), budget={"a.html": 12})

    assert not has_errors(findings)
    assert [f.level for f in findings] == ["warning"]
    assert "budget" in findings[0].message


def test_budget_match_produces_no_warning(book_dir: Path, tmp_path: Path):
    write_book(book_dir, "a.html", ["<p>a</p>", "<p>b</p>"])
    manifest = assign_folios([("a.html", 2)])

    assert verify(book_dir, manifest, _css(tmp_path), budget={"a.html": 2}) == []


def test_has_errors_ignores_warnings():
    warning = Finding(level="warning", file="a.html", message="budget drift")

    assert not has_errors([warning])
    assert has_errors([warning, Finding(level="error", file="a.html", message="x")])
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd skills/book-writing/scripts && uv run pytest tests/test_verify.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'bookkit.verify'`.

- [ ] **Step 3: Write the implementation**

Create `skills/book-writing/scripts/bookkit/verify.py`:

```python
"""The production gate.

Every check here catches a failure that is otherwise silent: clipped text
vanishes without an error, a stale folio offset renumbers half the book, and a
chapter-local selector can restyle every chapter at once. An advisory check
that a tired author skips is equivalent to no check, so these exit non-zero.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from bookkit.cssguard import check_css_layering
from bookkit.manifest import Manifest, folio_discontinuities
from bookkit.measure import measure_files, px_to_pt
from bookkit.paginate import MANIFEST_NAME, page_counts

GEOMETRY_TOLERANCE_PT = 0.5
OVERFLOW_TOLERANCE_PX = 1.0


@dataclass(frozen=True)
class Finding:
    """One verification result. `level` is "error" or "warning"."""

    level: str
    file: str
    message: str


def has_errors(findings: Sequence[Finding]) -> bool:
    return any(finding.level == "error" for finding in findings)


def verify(
    book_dir: Path,
    manifest: Manifest,
    css_path: Path,
    expected_pt: tuple[float, float] = (504.0, 720.0),
    budget: dict[str, int] | None = None,
) -> list[Finding]:
    """Run every check over a book directory and return the findings."""
    findings: list[Finding] = []
    paths = [book_dir / entry.file for entry in manifest.entries]
    extents = measure_files(paths)
    expected_w, expected_h = expected_pt

    for extent in extents:
        width_pt = px_to_pt(extent.width_px)
        height_pt = px_to_pt(extent.box_px)
        if (
            abs(width_pt - expected_w) > GEOMETRY_TOLERANCE_PT
            or abs(height_pt - expected_h) > GEOMETRY_TOLERANCE_PT
        ):
            findings.append(
                Finding(
                    level="error",
                    file=extent.file,
                    message=(
                        f"page {extent.index + 1}: geometry is "
                        f"{width_pt:.1f}×{height_pt:.1f}pt, "
                        f"expected {expected_w:.1f}×{expected_h:.1f}pt"
                    ),
                )
            )
        if extent.overflow_px > OVERFLOW_TOLERANCE_PX:
            findings.append(
                Finding(
                    level="error",
                    file=extent.file,
                    message=(
                        f"page {extent.index + 1}: content is clipped by "
                        f"{px_to_pt(extent.overflow_px):.1f}pt"
                    ),
                )
            )

    measured = dict(page_counts(extents))
    for entry in manifest.entries:
        actual = measured.get(entry.file, 0)
        if actual != entry.pages:
            findings.append(
                Finding(
                    level="error",
                    file=entry.file,
                    message=(
                        f"stale manifest: measured {actual} pages, "
                        f"manifest says {entry.pages}; re-run bookkit.paginate"
                    ),
                )
            )

    for problem in folio_discontinuities(manifest):
        findings.append(
            Finding(level="error", file=problem.split(":")[0], message=f"folio {problem}")
        )

    for path in paths:
        for violation in check_css_layering(path, css_path):
            findings.append(
                Finding(
                    level="error",
                    file=violation.file,
                    message=(
                        f"chapter-local selector .{violation.selector} "
                        f"is {violation.reason}"
                    ),
                )
            )

    for file, budgeted in (budget or {}).items():
        actual = measured.get(file)
        if actual is not None and actual != budgeted:
            findings.append(
                Finding(
                    level="warning",
                    file=file,
                    message=(
                        f"page budget drift: {actual} pages against a "
                        f"budget of {budgeted}"
                    ),
                )
            )

    return findings


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify a book directory.")
    parser.add_argument("book_dir", type=Path)
    parser.add_argument("--css", type=Path, default=None)
    parser.add_argument("--width-pt", type=float, default=504.0)
    parser.add_argument("--height-pt", type=float, default=720.0)
    args = parser.parse_args(argv)

    manifest = Manifest.from_json(
        (args.book_dir / MANIFEST_NAME).read_text(encoding="utf-8")
    )
    css_path = args.css or args.book_dir / "assets" / "interior.css"

    findings = verify(
        args.book_dir, manifest, css_path, (args.width_pt, args.height_pt)
    )
    for finding in findings:
        print(f"{finding.level.upper():<7} {finding.file}: {finding.message}")
    if has_errors(findings):
        print(f"\nFAILED: {sum(f.level == 'error' for f in findings)} error(s)")
        return 1
    print(f"OK: {manifest.total_pages()} pages verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd skills/book-writing/scripts && uv run pytest tests/test_verify.py -v
```

Expected: 10 passed.

- [ ] **Step 5: Run the whole suite**

```bash
cd skills/book-writing/scripts && uv run pytest -v
```

Expected: 50 passed.

- [ ] **Step 6: Commit**

```bash
git add skills/book-writing/scripts/bookkit/verify.py skills/book-writing/scripts/tests/test_verify.py
git commit -m "feat(bookkit): add the production verification gate"
```

---

### Task 7: Write the core interior stylesheet

**Files:**
- Create: `skills/book-writing/assets/interior.css`
- Test: `skills/book-writing/scripts/tests/test_interior_css.py`

**Interfaces:**
- Consumes: `core_selectors` (Task 2), `measure_file` (Task 1).
- Produces: `assets/interior.css` defining the six tokens and the core component vocabulary. Later tasks' templates link this file.

**Required tokens** (declared on `:root`): `--page-w`, `--page-h`, `--margin`, `--ink`, `--paper`, `--accent`, `--serif`, `--sans`, `--mono`.

**Required core classes:** `page`, `with-head`, `running-head`, `page-number`, `folio-title`, `eyebrow`, `deck`, `lead`, `small`, `micro`, `dropcap`, `opener-number`, `principle`, `quote`, `callout`, `label`, `spec`, `artifact`, `steps`, `checklist`, `comparison-row`, `matrix`, `flow-box`, `columns-2`, `columns-3`, `sidebar-grid`, `rule`, `accent-rule`, `signature`, `caption`.

- [ ] **Step 1: Write the failing test**

Create `skills/book-writing/scripts/tests/test_interior_css.py`:

```python
from pathlib import Path

from bookkit.cssguard import core_selectors
from bookkit.measure import measure_file, px_to_pt

CSS_PATH = Path(__file__).resolve().parents[2] / "assets" / "interior.css"

REQUIRED_TOKENS = [
    "--page-w",
    "--page-h",
    "--margin",
    "--ink",
    "--paper",
    "--accent",
    "--serif",
    "--sans",
    "--mono",
]

REQUIRED_CLASSES = {
    "page", "with-head", "running-head", "page-number", "folio-title",
    "eyebrow", "deck", "lead", "small", "micro", "dropcap", "opener-number",
    "principle", "quote", "callout", "label", "spec", "artifact", "steps",
    "checklist", "comparison-row", "matrix", "flow-box", "columns-2",
    "columns-3", "sidebar-grid", "rule", "accent-rule", "signature", "caption",
}


def test_stylesheet_exists():
    assert CSS_PATH.exists()


def test_declares_every_design_token():
    css = CSS_PATH.read_text(encoding="utf-8")

    missing = [token for token in REQUIRED_TOKENS if f"{token}:" not in css]
    assert missing == []


def test_defines_the_core_component_vocabulary():
    assert REQUIRED_CLASSES <= core_selectors(CSS_PATH)


def test_no_core_class_uses_the_chapter_local_prefix():
    assert not any(name.startswith("ch-") for name in core_selectors(CSS_PATH))


def test_forbidden_decorative_properties_are_absent():
    css = CSS_PATH.read_text(encoding="utf-8")

    for banned in ("box-shadow", "linear-gradient", "radial-gradient", "text-shadow"):
        assert banned not in css, f"{banned} violates the layout discipline"


def test_page_renders_at_the_declared_geometry(tmp_path: Path):
    html = tmp_path / "probe.html"
    html.write_text(
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<link rel='stylesheet' href='{CSS_PATH.as_uri()}'></head>"
        "<body><div class='page'><p>probe</p></div></body></html>",
        encoding="utf-8",
    )

    extent = measure_file(html)[0]

    assert round(px_to_pt(extent.width_px)) == 504
    assert round(px_to_pt(extent.box_px)) == 720


def test_retargeting_the_page_tokens_changes_the_geometry(tmp_path: Path):
    html = tmp_path / "probe.html"
    html.write_text(
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<link rel='stylesheet' href='{CSS_PATH.as_uri()}'>"
        "<style>:root { --page-w: 6in; --page-h: 9in; }</style></head>"
        "<body><div class='page'><p>probe</p></div></body></html>",
        encoding="utf-8",
    )

    extent = measure_file(html)[0]

    assert round(px_to_pt(extent.width_px)) == 432
    assert round(px_to_pt(extent.box_px)) == 648
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd skills/book-writing/scripts && uv run pytest tests/test_interior_css.py -v
```

Expected: FAIL — `test_stylesheet_exists` fails, `assets/interior.css` does not exist.

- [ ] **Step 3: Write the stylesheet**

Create `skills/book-writing/assets/interior.css`. Start from this skeleton and fill in the remaining components; every class in `REQUIRED_CLASSES` must be present, and the banned decorative properties must not appear.

```css
/* Core interior stylesheet for the book-writing skill.
   Retarget the whole book by overriding the tokens below. Chapter-local
   components belong in a page file's inline <style>, prefixed `ch-`. */

:root {
  --page-w: 7in;
  --page-h: 10in;
  --margin: 0.65in;

  --ink: #242424;
  --paper: #ffffff;
  --accent: #d54b20;
  --muted: #686868;
  --rule-color: #c9c9c9;
  --pale: #f1f1f1;

  --serif: Charter, "Bitstream Charter", Georgia, "Times New Roman", serif;
  --sans: "Avenir Next", Avenir, Arial, Helvetica, sans-serif;
  --mono: "Courier New", Courier, monospace;
}

@page { size: 7in 10in; margin: 0; }

* { box-sizing: border-box; }

html, body {
  margin: 0;
  padding: 0;
  background: #d8d8d8;
  color: var(--ink);
  font-family: var(--serif);
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

body { counter-reset: page 0; }

/* --- page frame --- */

.page {
  position: relative;
  width: var(--page-w);
  height: var(--page-h);
  margin: 0 auto 18px;
  padding: var(--margin);
  overflow: hidden;
  break-after: page;
  page-break-after: always;
  background: var(--paper);
  counter-increment: page;
}
.page:last-child { break-after: auto; page-break-after: auto; }
.with-head { padding-top: calc(var(--margin) + 0.08in); }

.running-head {
  position: absolute;
  left: var(--margin);
  right: var(--margin);
  top: 0.28in;
  display: flex;
  justify-content: space-between;
  padding-bottom: 6px;
  border-bottom: 1px solid #bdbdbd;
  font: 600 7pt/1 var(--sans);
  color: #555;
}
.page-number {
  position: absolute;
  right: var(--margin);
  bottom: 0.26in;
  font: 600 7.5pt/1 var(--sans);
  color: #555;
}
.page-number::after { content: counter(page); }
.folio-title {
  position: absolute;
  left: var(--margin);
  bottom: 0.26in;
  font: 600 7.5pt/1 var(--sans);
  letter-spacing: 0.025em;
  color: var(--muted);
}

/* --- typographic scale --- */

h1, h2, h3, h4, p, ul, ol, blockquote { margin-top: 0; }
h1, h2, h3, h4, .sans { font-family: var(--sans); }
h1 { margin-bottom: 18px; font-size: 31pt; line-height: 1.01; letter-spacing: -0.035em; }
h2 { margin-bottom: 14px; font-size: 18.5pt; line-height: 1.12; letter-spacing: -0.018em; }
h3 { margin-bottom: 7px; font-size: 11pt; line-height: 1.2; }
h4 {
  margin-bottom: 5px;
  font-size: 8.2pt;
  line-height: 1.2;
  letter-spacing: 0.075em;
  text-transform: uppercase;
}
p, li { font-size: 9.85pt; line-height: 1.48; }
p { margin-bottom: 10px; }
ul, ol { margin-bottom: 11px; padding-left: 19px; }
li { margin-bottom: 4px; }
code { font-family: var(--mono); }

.small, .small p, .small li { font-size: 8.25pt; line-height: 1.4; }
.micro { font: 7.2pt/1.35 var(--sans); color: var(--muted); }
.lead { font-size: 12pt; line-height: 1.48; }
.caption { font: 7.4pt/1.35 var(--sans); color: var(--muted); margin-top: 5px; }

/* --- chapter opener --- */

.eyebrow {
  margin-bottom: 11px;
  font: 700 7.4pt/1 var(--sans);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--accent);
}
.deck { margin-bottom: 20px; font-size: 14pt; line-height: 1.36; color: #444; }
.dropcap::first-letter {
  float: left;
  margin: 3px 7px 0 0;
  font: 750 39pt/0.73 var(--sans);
  color: var(--accent);
}
.opener-number {
  margin-bottom: 22px;
  font: 750 72pt/0.8 var(--sans);
  letter-spacing: -0.08em;
  color: #f2ddd5;
}

/* --- rules and emphasis --- */

.rule { border: 0; border-top: 1px solid var(--rule-color); margin: 18px 0; }
.accent-rule { width: 0.7in; border: 0; border-top: 3px solid var(--accent); margin: 0 0 18px; }
.principle {
  margin: 16px 0;
  padding: 12px 0 12px 18px;
  border-left: 4px solid var(--accent);
  font: 700 13.5pt/1.35 var(--sans);
}
.quote {
  margin: 17px 0;
  padding-left: 16px;
  border-left: 3px solid var(--accent);
  font-size: 13pt;
  line-height: 1.4;
  color: #3a3a3a;
}
.signature { margin-top: 12px; font: 8pt/1.4 var(--sans); color: var(--muted); }

/* --- layout --- */

.columns-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 22px; }
.columns-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.sidebar-grid { display: grid; grid-template-columns: 1.65fr 0.85fr; gap: 21px; }

/* --- components ---
   Remaining required classes follow the same pattern. Each must be defined:
   .callout (+ .callout.teal, .callout.amber), .label, .spec, .artifact,
   .steps, .checklist, .comparison-row, .matrix, .flow-box.
   Carry variants by border colour and background tint only — never encode
   meaning in colour alone, and keep every component legible in greyscale. */
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd skills/book-writing/scripts && uv run pytest tests/test_interior_css.py -v
```

Expected: 7 passed. If `test_defines_the_core_component_vocabulary` fails, the assertion error names the missing classes — add them.

- [ ] **Step 5: Commit**

```bash
git add skills/book-writing/assets/interior.css skills/book-writing/scripts/tests/test_interior_css.py
git commit -m "feat(assets): add the tokenised core interior stylesheet"
```

---

### Task 8: Write the page and blueprint templates

**Files:**
- Create: `skills/book-writing/assets/chapter.template.html`
- Create: `skills/book-writing/assets/front-matter.template.html`
- Create: `skills/book-writing/assets/cover.template.html`
- Create: `skills/book-writing/assets/STRUCTURE.template.md`
- Test: `skills/book-writing/scripts/tests/test_templates.py`

**Interfaces:**
- Consumes: `check_css_layering` (Task 2), `measure_file` and `px_to_pt` (Task 1), `interior.css` (Task 7).
- Produces: four templates. HTML templates link `../assets/interior.css`, carry a `counter-reset: page 0` declaration for `paginate.py` to rewrite, and use `{{PLACEHOLDER}}` tokens.

- [ ] **Step 1: Write the failing test**

Create `skills/book-writing/scripts/tests/test_templates.py`:

```python
import re
from pathlib import Path

import pytest

from bookkit.cssguard import check_css_layering
from bookkit.measure import measure_file, px_to_pt
from bookkit.paginate import set_counter_offset

ASSETS = Path(__file__).resolve().parents[2] / "assets"
CSS_PATH = ASSETS / "interior.css"
HTML_TEMPLATES = [
    "chapter.template.html",
    "front-matter.template.html",
    "cover.template.html",
]


@pytest.mark.parametrize("name", HTML_TEMPLATES)
def test_template_exists(name: str):
    assert (ASSETS / name).exists()


@pytest.mark.parametrize("name", HTML_TEMPLATES)
def test_template_links_the_core_stylesheet(name: str):
    html = (ASSETS / name).read_text(encoding="utf-8")

    assert 'href="../assets/interior.css"' in html


@pytest.mark.parametrize("name", HTML_TEMPLATES)
def test_template_carries_a_rewritable_counter_reset(name: str):
    html = (ASSETS / name).read_text(encoding="utf-8")

    assert set_counter_offset(html, 5) != html


@pytest.mark.parametrize("name", HTML_TEMPLATES)
def test_template_declares_at_least_one_page(name: str):
    html = (ASSETS / name).read_text(encoding="utf-8")

    assert 'class="page' in html


@pytest.mark.parametrize("name", HTML_TEMPLATES)
def test_template_respects_css_layering(name: str, tmp_path: Path):
    source = (ASSETS / name).read_text(encoding="utf-8")
    probe = tmp_path / name
    probe.write_text(source.replace("../assets/interior.css", CSS_PATH.as_uri()), "utf-8")

    assert check_css_layering(probe, CSS_PATH) == []


def test_chapter_template_renders_at_the_declared_geometry(tmp_path: Path):
    source = (ASSETS / "chapter.template.html").read_text(encoding="utf-8")
    probe = tmp_path / "probe.html"
    probe.write_text(source.replace("../assets/interior.css", CSS_PATH.as_uri()), "utf-8")

    for extent in measure_file(probe):
        assert round(px_to_pt(extent.width_px)) == 504
        assert round(px_to_pt(extent.box_px)) == 720


def test_chapter_template_pages_do_not_overflow(tmp_path: Path):
    source = (ASSETS / "chapter.template.html").read_text(encoding="utf-8")
    probe = tmp_path / "probe.html"
    probe.write_text(source.replace("../assets/interior.css", CSS_PATH.as_uri()), "utf-8")

    assert all(extent.overflow_px <= 1.0 for extent in measure_file(probe))


def test_chapter_template_marks_every_required_beat():
    html = (ASSETS / "chapter.template.html").read_text(encoding="utf-8")

    for beat in [
        "OPENING SITUATION",
        "CHAPTER PROMISE",
        "PROBLEM AND CONSEQUENCES",
        "CORE CONCEPT",
        "STEP-BY-STEP METHOD",
        "WORKED EXAMPLE",
        "FAILURE MODES",
        "FIELD GUIDE",
        "WHAT TO REMEMBER",
        "ONE ACTION",
        "TRANSITION",
    ]:
        assert beat in html, f"chapter template is missing the {beat} beat"


def test_structure_template_declares_every_required_field():
    md = (ASSETS / "STRUCTURE.template.md").read_text(encoding="utf-8")

    for field in [
        "## Promise",
        "## Audience",
        "## Reading paths",
        "## Running examples",
        "## Standard chapter pattern",
        "## Page budget",
    ]:
        assert field in md


def test_structure_template_requires_a_driving_question_per_chapter():
    md = (ASSETS / "STRUCTURE.template.md").read_text(encoding="utf-8")

    assert re.search(r"\*\*Question:\*\*", md)
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd skills/book-writing/scripts && uv run pytest tests/test_templates.py -v
```

Expected: FAIL — the template files do not exist.

- [ ] **Step 3: Write the chapter template**

Create `skills/book-writing/assets/chapter.template.html`:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{{BOOK_TITLE}} — Chapter {{N}}</title>
  <link rel="stylesheet" href="../assets/interior.css">
  <style>
    /* Chapter-local components only. Prefix every class `ch-`.
       Never redefine a core selector — bookkit.verify rejects both. */
    body { counter-reset: page 0; }
  </style>
</head>
<body>

<!-- OPENING SITUATION + CHAPTER PROMISE -->
<div class="page">
  <div class="opener-number">{{N}}</div>
  <div class="eyebrow">{{PART_NAME}}</div>
  <h1>{{CHAPTER_TITLE}}</h1>
  <hr class="accent-rule">
  <p class="deck">{{DRIVING_QUESTION}}</p>
  <p class="dropcap">{{OPENING_SITUATION}}</p>
  <div class="callout">
    <span class="label">CHAPTER PROMISE</span>
    <p>{{PROMISE}}</p>
    <p class="micro">Reading time: {{MINUTES}} minutes</p>
  </div>
  <div class="folio-title">{{CHAPTER_TITLE}}</div>
  <div class="page-number"></div>
</div>

<!-- PROBLEM AND CONSEQUENCES -->
<div class="page with-head">
  <div class="running-head"><span>{{BOOK_TITLE}}</span><span>{{CHAPTER_TITLE}}</span></div>
  <h2>{{PROBLEM_HEADING}}</h2>
  <p>{{PROBLEM_BODY}}</p>
  <div class="folio-title">{{CHAPTER_TITLE}}</div>
  <div class="page-number"></div>
</div>

<!-- CORE CONCEPT -->
<div class="page with-head">
  <div class="running-head"><span>{{BOOK_TITLE}}</span><span>{{CHAPTER_TITLE}}</span></div>
  <h2>{{CONCEPT_HEADING}}</h2>
  <p>{{CONCEPT_BODY}}</p>
  <div class="principle">{{PRINCIPLE}}</div>
  <div class="folio-title">{{CHAPTER_TITLE}}</div>
  <div class="page-number"></div>
</div>

<!-- STEP-BY-STEP METHOD -->
<div class="page with-head">
  <div class="running-head"><span>{{BOOK_TITLE}}</span><span>{{CHAPTER_TITLE}}</span></div>
  <h2>{{METHOD_HEADING}}</h2>
  <ol class="steps">
    <li>{{STEP_1}}</li>
    <li>{{STEP_2}}</li>
    <li>{{STEP_3}}</li>
  </ol>
  <div class="folio-title">{{CHAPTER_TITLE}}</div>
  <div class="page-number"></div>
</div>

<!-- WORKED EXAMPLE -->
<div class="page with-head">
  <div class="running-head"><span>{{BOOK_TITLE}}</span><span>{{CHAPTER_TITLE}}</span></div>
  <h2>{{EXAMPLE_HEADING}}</h2>
  <p>{{EXAMPLE_BODY}}</p>
  <div class="spec">
    <h3>{{ARTIFACT_NAME}}</h3>
    <p>{{ARTIFACT_BODY}}</p>
  </div>
  <div class="folio-title">{{CHAPTER_TITLE}}</div>
  <div class="page-number"></div>
</div>

<!-- FAILURE MODES -->
<div class="page with-head">
  <div class="running-head"><span>{{BOOK_TITLE}}</span><span>{{CHAPTER_TITLE}}</span></div>
  <h2>{{FAILURE_HEADING}}</h2>
  <div class="callout amber">
    <span class="label amber">WARNING</span>
    <p>{{FAILURE_BODY}}</p>
  </div>
  <div class="folio-title">{{CHAPTER_TITLE}}</div>
  <div class="page-number"></div>
</div>

<!-- FIELD GUIDE -->
<div class="page with-head">
  <div class="running-head"><span>{{BOOK_TITLE}}</span><span>{{CHAPTER_TITLE}}</span></div>
  <h2>Field guide: {{FIELD_GUIDE_NAME}}</h2>
  <ul class="checklist">
    <li>{{CHECK_1}}</li>
    <li>{{CHECK_2}}</li>
  </ul>
  <div class="folio-title">{{CHAPTER_TITLE}}</div>
  <div class="page-number"></div>
</div>

<!-- WHAT TO REMEMBER + ONE ACTION + TRANSITION -->
<div class="page with-head">
  <div class="running-head"><span>{{BOOK_TITLE}}</span><span>{{CHAPTER_TITLE}}</span></div>
  <h2>What to remember</h2>
  <ul><li>{{REMEMBER_1}}</li><li>{{REMEMBER_2}}</li></ul>
  <h4>ONE ACTION TO TAKE NEXT</h4>
  <p>{{ACTION}}</p>
  <hr class="rule">
  <p class="small">TRANSITION — {{TRANSITION}}</p>
  <div class="folio-title">{{CHAPTER_TITLE}}</div>
  <div class="page-number"></div>
</div>

</body>
</html>
```

- [ ] **Step 4: Write the front-matter and cover templates**

Create `skills/book-writing/assets/front-matter.template.html` — same `<head>` as the chapter template (title `{{BOOK_TITLE}} — Front matter`), with `.page` divs for: half title, title page, copyright, table of contents, and preface opener. Use `{{...}}` placeholders throughout, and no `.page-number` on the half title or title page.

Create `skills/book-writing/assets/cover.template.html` — same `<head>` (title `{{BOOK_TITLE}} — Covers`), with two `.page` divs: front cover (`{{BOOK_TITLE}}`, `{{SUBTITLE}}`, `{{AUTHOR}}`) and back cover (`{{BACK_COVER_BLURB}}`, `{{OUTCOMES}}`). Neither carries a running head or folio.

- [ ] **Step 5: Write the blueprint template**

Create `skills/book-writing/assets/STRUCTURE.template.md`:

```markdown
# {{BOOK_TITLE}}

## Working subtitle

{{SUBTITLE}}

## Promise

{{One paragraph: what the reader can do after finishing that they could not do before.}}

## Audience

- {{Role}}
- {{Role}}

**Not the audience:** {{Who should be pointed elsewhere, and where.}}

## Reading paths

**{{Path name}}:** Chapters {{list}}
{{What this path gives the reader.}}

**{{Path name}}:** {{Route}}
{{What this path gives the reader.}}

## Running examples

### Primary: {{Name}}

{{The example that recurs in every chapter. Start it as something small and
under-specified so it can grow across the book.}}

### Variant: {{Name}}

{{An example that stresses scale, regulation, modernization, or operational risk.}}

---

# Part {{N}} — {{Part title}}

## Chapter {{N}}: {{Chapter title}}

**Question:** {{The single question this chapter answers. Every beat below must
serve this answer. If a beat does not, cut it or move it to another chapter.}}

- {{Beat}}
- {{Beat}}
- {{Beat}}

**Field guide:** {{Reusable artifact the reader leaves with}}
**Primary example:** {{Slice of the running example}}

---

# Back matter

## Appendix A: {{Title}}
## Glossary
## Notes and references
## Index

---

# Standard chapter pattern

Each chapter uses this sequence where it fits:

1. Opening situation
2. Chapter promise and reading time
3. Problem and consequences
4. Core concept in plain language
5. Step-by-step method
6. Primary worked example
7. Variant example
8. Failure modes and limitations
9. Reusable field guide
10. What to remember
11. Questions for the reader's team
12. One action to take next
13. Transition to the next chapter

# Page budget

- Front matter: {{N}}–{{N}} pages
- Part I: {{N}}–{{N}} pages
- Back matter: {{N}}–{{N}} pages
- **Estimated total:** {{N}}–{{N}} pages
```

- [ ] **Step 6: Run the test to verify it passes**

```bash
cd skills/book-writing/scripts && uv run pytest tests/test_templates.py -v
```

Expected: all passed.

- [ ] **Step 7: Commit**

```bash
git add skills/book-writing/assets
git commit -m "feat(assets): add chapter, front-matter, cover, and blueprint templates"
```

---

### Task 9: Write the authoring references

**Files:**
- Create: `skills/book-writing/references/blueprint-format.md`
- Create: `skills/book-writing/references/chapter-pattern.md`
- Create: `skills/book-writing/references/editorial-standards.md`
- Test: `skills/book-writing/scripts/tests/test_references_authoring.py`

**Interfaces:**
- Consumes: `assets/STRUCTURE.template.md` (Task 8).
- Produces: three reference documents, each loaded by `SKILL.md` for a specific phase.

- [ ] **Step 1: Write the failing test**

Create `skills/book-writing/scripts/tests/test_references_authoring.py`:

```python
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[2]
REFS = SKILL / "references"


@pytest.mark.parametrize(
    "name", ["blueprint-format.md", "chapter-pattern.md", "editorial-standards.md"]
)
def test_reference_exists_and_is_substantial(name: str):
    path = REFS / name
    assert path.exists()
    assert len(path.read_text(encoding="utf-8").split()) > 250


def test_blueprint_format_lists_every_required_field():
    text = (REFS / "blueprint-format.md").read_text(encoding="utf-8")

    for field in [
        "Promise",
        "Audience",
        "Reading paths",
        "Running examples",
        "driving question",
        "Standard chapter pattern",
        "Page budget",
    ]:
        assert field in text


def test_blueprint_format_points_at_the_template():
    text = (REFS / "blueprint-format.md").read_text(encoding="utf-8")

    assert "assets/STRUCTURE.template.md" in text


def test_chapter_pattern_marks_beats_required_or_optional():
    text = (REFS / "chapter-pattern.md").read_text(encoding="utf-8")

    assert "required" in text
    assert "where it fits" in text


def test_chapter_pattern_covers_all_thirteen_beats():
    text = (REFS / "chapter-pattern.md").read_text(encoding="utf-8").lower()

    for beat in [
        "opening situation",
        "chapter promise",
        "problem and consequences",
        "core concept",
        "step-by-step method",
        "worked example",
        "variant example",
        "failure modes",
        "field guide",
        "what to remember",
        "questions for the reader",
        "one action",
        "transition",
    ]:
        assert beat in text, f"missing beat: {beat}"


def test_editorial_standards_delegates_to_avoid_ai_writing():
    text = (REFS / "editorial-standards.md").read_text(encoding="utf-8")

    assert "avoid-ai-writing" in text
    assert "github.com/conorbronsdon/avoid-ai-writing" in text


def test_editorial_standards_keeps_the_evidence_classification():
    text = (REFS / "editorial-standards.md").read_text(encoding="utf-8").lower()

    for term in ["reported practice", "interpretation", "evidence", "speculation"]:
        assert term in text


def test_editorial_standards_does_not_prescribe_subject_matter():
    text = (REFS / "editorial-standards.md").read_text(encoding="utf-8").lower()

    for leaked in ["volunteer operations", "simon martinelli", "self-contained system"]:
        assert leaked not in text, f"source-book content leaked: {leaked}"
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd skills/book-writing/scripts && uv run pytest tests/test_references_authoring.py -v
```

Expected: FAIL — reference files do not exist.

- [ ] **Step 3: Write `references/blueprint-format.md`**

Document the `STRUCTURE.md` contract. Required content:

- What the blueprint is for: the durable contract between writing sessions. Without it, chapter 9 drifts from chapter 2.
- The required-field table, in order: Promise, Audience, Reading paths, Running examples, Parts → chapters, Back matter, Standard chapter pattern, Page budget.
- **The driving question rule**, stated as the format's central constraint: every chapter declares one question; every beat in that chapter must serve the answer; a beat that does not is cut or moved. This is what stops a chapter becoming a topic dump.
- How to choose a primary running example: start it small and under-specified so it can grow across the book; add variants only where they expose scale, regulation, or risk that the primary cannot.
- How the page budget is used downstream: `bookkit.verify` warns on drift, so an over-running chapter surfaces as a structural problem rather than being absorbed silently.
- A pointer to `assets/STRUCTURE.template.md` as the starting file.
- One paragraph: a companion volume is this phase run again into a subfolder, sharing `assets/interior.css` and adding its own `STRUCTURE.md`.

- [ ] **Step 4: Write `references/chapter-pattern.md`**

Document the beat sequence. Required content:

- The thirteen beats in order, each marked **required** or **where it fits**, matching the spec: opening situation (required), chapter promise and reading time (required), problem and consequences (required), core concept in plain language (required), step-by-step method (required), primary worked example (required), variant example (where it fits), failure modes and limitations (required), reusable field guide (required), what to remember (required), questions for the reader's team (where it fits), one action to take next (required), transition to the next chapter (required).
- For each beat: what it is for, and the failure mode of omitting it.
- Pagination guidance: never orphan a heading at a page foot, never split a worked example across a spread break, and prefer moving a whole beat to the next page over tightening leading.
- A pointer to `assets/chapter.template.html`, whose comment markers correspond to these beats.

- [ ] **Step 5: Write `references/editorial-standards.md`**

Document the rigor rules. Required content:

- Voice: active voice, direct second person, natural contractions, calm conversational tone.
- Structure: concrete problem or example before the abstraction; short sentences; short paragraphs; precise verbs; descriptive headings.
- Terms: define on first use; no unexplained acronyms.
- Prohibitions: hype, consulting jargon, slogans, inflated claims, repetitive summary language.
- **The evidence classification**, carried forward from intake: every claim is labelled reported practice, interpretation, established practice, evidence, or speculation, and that distinction must survive into the prose.
- Callouts, used sparingly: Tip, Note, Warning, Rule of thumb.
- The delegation: the mechanical AI-slop pass is the `avoid-ai-writing` skill (installed at `~/.claude/skills/avoid-ai-writing`; upstream `https://github.com/conorbronsdon/avoid-ai-writing`), invoked on every chapter before it is marked done. State explicitly that this skill does not reimplement those patterns.
- A closing note that this file constrains rigor, not personality — the book's voice comes from the drafts and the user's instructions.

**Do not** include any example drawn from the source book. The test asserts that no such content leaks.

- [ ] **Step 6: Run the test to verify it passes**

```bash
cd skills/book-writing/scripts && uv run pytest tests/test_references_authoring.py -v
```

Expected: all passed.

- [ ] **Step 7: Commit**

```bash
git add skills/book-writing/references skills/book-writing/scripts/tests/test_references_authoring.py
git commit -m "docs(references): add blueprint, chapter-pattern, and editorial references"
```

---

### Task 10: Write the production references

**Files:**
- Create: `skills/book-writing/references/interior-design.md`
- Create: `skills/book-writing/references/production.md`
- Test: `skills/book-writing/scripts/tests/test_references_production.py`

**Interfaces:**
- Consumes: `assets/interior.css` (Task 7); the `bookkit` CLIs (Tasks 4–6).
- Produces: two reference documents.

- [ ] **Step 1: Write the failing test**

Create `skills/book-writing/scripts/tests/test_references_production.py`:

```python
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[2]
REFS = SKILL / "references"


@pytest.mark.parametrize("name", ["interior-design.md", "production.md"])
def test_reference_exists_and_is_substantial(name: str):
    path = REFS / name
    assert path.exists()
    assert len(path.read_text(encoding="utf-8").split()) > 250


def test_interior_design_documents_every_token():
    text = (REFS / "interior-design.md").read_text(encoding="utf-8")

    for token in ["--page-w", "--page-h", "--margin", "--ink", "--paper",
                  "--accent", "--serif", "--sans", "--mono"]:
        assert token in text


def test_interior_design_explains_the_two_css_layers():
    text = (REFS / "interior-design.md").read_text(encoding="utf-8")

    assert "ch-" in text
    assert "interior.css" in text
    assert "shadow" in text.lower()


def test_interior_design_states_the_layout_discipline():
    text = (REFS / "interior-design.md").read_text(encoding="utf-8").lower()

    for rule in ["grayscale", "colour alone", "gradient"]:
        assert rule in text or rule.replace("colour", "color") in text


def test_production_documents_the_folio_offset_rule():
    text = (REFS / "production.md").read_text(encoding="utf-8")

    assert "counter-reset" in text
    assert "F - 1" in text or "start_folio - 1" in text


def test_production_names_every_cli():
    text = (REFS / "production.md").read_text(encoding="utf-8")

    for module in ["bookkit.paginate", "bookkit.render", "bookkit.merge", "bookkit.verify"]:
        assert module in text


def test_production_lists_the_hard_failures_and_the_warning():
    text = (REFS / "production.md").read_text(encoding="utf-8").lower()

    for failure in ["geometry", "clip", "layering", "folio"]:
        assert failure in text
    assert "budget" in text


def test_production_explains_the_single_engine_requirement():
    text = (REFS / "production.md").read_text(encoding="utf-8").lower()

    assert "same" in text and "chromium" in text
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd skills/book-writing/scripts && uv run pytest tests/test_references_production.py -v
```

Expected: FAIL — reference files do not exist.

- [ ] **Step 3: Write `references/interior-design.md`**

Required content:

- The nine tokens, each with its default and what changing it does. Retargeting the book to a different trim or palette is a token edit, not a stylesheet rewrite.
- The two CSS layers: the core layer in `assets/interior.css`, linked by every page file; the chapter-local layer in a page file's inline `<style>`, for a diagram only that chapter needs. Local classes are prefixed `ch-` and must never shadow a core selector — `bookkit.verify` rejects both, because one chapter silently restyling the whole book is the failure this boundary exists to prevent.
- The core component vocabulary, grouped: page frame, typographic scale, chapter opener, rules and emphasis, layout grids, components.
- Layout discipline: diagrams functional and legible in grayscale; never carry meaning in color alone; no slide-deck pages, full-page dark panels, card walls, gradients, or shadows; continuous editorial rhythm with generous margins, quiet running heads, folios, and captions.
- Hand-pagination: pages are laid out by hand as `.page` divs. `overflow: hidden` keeps the trim clean but means overset content disappears silently, which is why `bookkit.verify` measures every page.

- [ ] **Step 4: Write `references/production.md`**

Required content:

- The four commands in order, copy-pasteable:

  ```bash
  cd skills/book-writing/scripts
  uv run python -m bookkit.paginate ../../../book
  uv run python -m bookkit.render   ../../../book
  uv run python -m bookkit.merge    ../../../book
  uv run python -m bookkit.verify   ../../../book --css ../assets/interior.css
  ```

- First-time setup: `uv sync --extra dev` then `uv run playwright install chromium`.
- The folio offset rule: `.page { counter-increment: page }` fires on the first page, so a file whose first page shows folio `F` needs `counter-reset: page (F - 1)`. `bookkit.paginate` writes this from measured counts; never edit it by hand.
- `book.order`: one filename per line, assembly order. Absent, files are taken in sorted-name order.
- The single-engine requirement: measurement and printing both run through the same Playwright Chromium. If they used different builds, layout could disagree and verification would certify a page as fitting that the PDF then clips.
- The verification gate: hard failures are geometry mismatch, page content clipping, CSS layering violation, and folio discontinuity or a stale manifest; page-budget drift is a warning. Each hard failure is silent without the check, which is why they exit non-zero.
- Re-running order after any content edit: `paginate` → `render` → `merge` → `verify`. Editing a chapter changes its page count, which changes every downstream folio.

- [ ] **Step 5: Run the test to verify it passes**

```bash
cd skills/book-writing/scripts && uv run pytest tests/test_references_production.py -v
```

Expected: all passed.

- [ ] **Step 6: Commit**

```bash
git add skills/book-writing/references skills/book-writing/scripts/tests/test_references_production.py
git commit -m "docs(references): add interior-design and production references"
```

---

### Task 11: Write the SKILL.md router

**Files:**
- Create: `skills/book-writing/SKILL.md`
- Test: `skills/book-writing/scripts/tests/test_skill_structure.py`

**Interfaces:**
- Consumes: every reference and asset from Tasks 7–10.
- Produces: the skill entry point. YAML frontmatter with `name: book-writing` and a `description` carrying explicit trigger phrases.

- [ ] **Step 1: Write the failing test**

Create `skills/book-writing/scripts/tests/test_skill_structure.py`:

```python
import re
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2]
SKILL_MD = SKILL / "SKILL.md"


def _frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert match, "SKILL.md must open with YAML frontmatter"
    fields = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def test_skill_md_exists():
    assert SKILL_MD.exists()


def test_frontmatter_names_the_skill():
    assert _frontmatter(SKILL_MD.read_text(encoding="utf-8"))["name"] == "book-writing"


def test_description_carries_trigger_phrases():
    description = _frontmatter(SKILL_MD.read_text(encoding="utf-8"))["description"]

    assert len(description) > 80
    assert "book" in description.lower()
    assert "drafts" in description.lower()


def test_router_stays_short_enough_to_load_cheaply():
    words = len(SKILL_MD.read_text(encoding="utf-8").split())

    assert words < 900, f"SKILL.md is {words} words; move detail into references/"


def test_router_names_all_six_phases():
    text = SKILL_MD.read_text(encoding="utf-8").lower()

    for phase in ["intake", "blueprint", "interior", "chapter", "editorial", "production"]:
        assert phase in text


def test_router_points_at_every_reference():
    text = SKILL_MD.read_text(encoding="utf-8")

    for ref in [
        "references/blueprint-format.md",
        "references/chapter-pattern.md",
        "references/editorial-standards.md",
        "references/interior-design.md",
        "references/production.md",
    ]:
        assert ref in text


def test_every_referenced_path_exists():
    text = SKILL_MD.read_text(encoding="utf-8")

    for rel in re.findall(r"(?:references|assets|scripts)/[A-Za-z0-9_.\-/]+", text):
        candidate = SKILL / rel
        if candidate.suffix:
            assert candidate.exists(), f"SKILL.md points at missing {rel}"


def test_router_names_the_drafts_input():
    assert "drafts/" in SKILL_MD.read_text(encoding="utf-8")


def test_router_requires_the_editorial_gate():
    text = SKILL_MD.read_text(encoding="utf-8")

    assert "avoid-ai-writing" in text


def test_router_refuses_to_invent_source_material():
    text = SKILL_MD.read_text(encoding="utf-8").lower()

    assert "do not invent" in text or "never invent" in text
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd skills/book-writing/scripts && uv run pytest tests/test_skill_structure.py -v
```

Expected: FAIL — `SKILL.md` does not exist.

- [ ] **Step 3: Write the router**

Create `skills/book-writing/SKILL.md`:

```markdown
---
name: book-writing
description: Write and produce a book from source material in a drafts/ folder — structural blueprint, hand-paginated chapters, and a verified PDF. Use when asked to write a book, turn drafts or a transcript into a book, outline or structure a book, draft or typeset a chapter, or produce a book PDF.
---

# Writing a book

Turns a `drafts/` folder into a produced book through six phases. This skill carries
**structure** (how a book is architected) and **design** (how the interior is built and
rendered). It carries **no subject matter and no voice** — those come from the drafts and
from the user's instructions.

Work one phase at a time. Read the reference for the active phase; do not preload the rest.

## ① Intake — read `drafts/`

Inventory everything in `drafts/`: transcripts, notes, articles, outlines, existing prose.
Extract into a working note:

- The driving problem the book exists to address.
- Every distinct claim, each labelled **reported practice**, **interpretation**,
  **established practice**, **evidence**, or **speculation**. This classification is carried
  through to the prose.
- Stories usable as chapter openers.
- Candidate running examples.

Voice and subject matter are read out of the drafts here. If `drafts/` is empty or missing,
stop and say so — **do not invent source material**.

## ② Blueprint — write `STRUCTURE.md`

Read `references/blueprint-format.md`. Copy `assets/STRUCTURE.template.md` and fill it in.

Every chapter declares one **driving question**, and every beat in that chapter must serve
the answer. This is the constraint that keeps a chapter from becoming a topic dump.

`STRUCTURE.md` is the durable contract between writing sessions. Write it before any prose.

## ③ Interior — establish the design system

Read `references/interior-design.md`. Copy `assets/interior.css` into the project and set
the nine tokens (`--page-w`, `--page-h`, `--margin`, `--ink`, `--paper`, `--accent`,
`--serif`, `--sans`, `--mono`).

Then lay out **one** chapter and take it all the way through phase ⑥. Prove the design on a
single chapter before laying out the rest.

## ④ Chapter — draft and typeset

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
uv run python -m bookkit.paginate ../../../book
uv run python -m bookkit.render   ../../../book
uv run python -m bookkit.merge    ../../../book
uv run python -m bookkit.verify   ../../../book --css ../assets/interior.css
```

`verify` fails on clipped pages, wrong geometry, CSS layering violations, and folio
discontinuity — every one of which is otherwise silent. Never hand-edit a `counter-reset`
offset; `paginate` writes it from measured page counts.

Re-run all four after any content edit: editing one chapter changes its page count, which
changes every downstream folio.
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd skills/book-writing/scripts && uv run pytest tests/test_skill_structure.py -v
```

Expected: 10 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/book-writing/SKILL.md skills/book-writing/scripts/tests/test_skill_structure.py
git commit -m "feat(skill): add the book-writing router"
```

---

### Task 12: Prove the pipeline end to end

**Files:**
- Create: `skills/book-writing/scripts/tests/test_end_to_end.py`
- Create: `README.md`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: every module and asset from Tasks 1–11.
- Produces: an end-to-end regression test and repository documentation.

- [ ] **Step 1: Write the failing test**

Create `skills/book-writing/scripts/tests/test_end_to_end.py`:

```python
import shutil
from pathlib import Path

from bookkit.manifest import Manifest
from bookkit.merge import merge, pdf_geometry_pt
from bookkit.paginate import MANIFEST_NAME, paginate, read_order
from bookkit.render import render_all
from bookkit.verify import has_errors, verify

SKILL = Path(__file__).resolve().parents[2]
ASSETS = SKILL / "assets"

PAGE = """<div class="page with-head">
  <div class="running-head"><span>Probe</span><span>Chapter {n}</span></div>
  <h2>Section {i}</h2><p>Body copy for section {i}.</p>
  <div class="folio-title">Chapter {n}</div><div class="page-number"></div>
</div>"""


def _chapter(book_dir: Path, n: int, pages: int) -> None:
    body = "\n".join(PAGE.format(n=n, i=i) for i in range(pages))
    (book_dir / f"chapter-{n:02d}.html").write_text(
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        f"<title>Probe — Chapter {n}</title>"
        '<link rel="stylesheet" href="../assets/interior.css">'
        "<style>body { counter-reset: page 0; }</style></head>"
        f"<body>{body}</body></html>",
        encoding="utf-8",
    )


def _project(tmp_path: Path) -> Path:
    shutil.copytree(ASSETS, tmp_path / "assets")
    book_dir = tmp_path / "book"
    book_dir.mkdir()
    _chapter(book_dir, 1, 3)
    _chapter(book_dir, 2, 2)
    (book_dir / "book.order").write_text(
        "chapter-01.html\nchapter-02.html\n", encoding="utf-8"
    )
    return book_dir


def test_full_pipeline_produces_a_verified_pdf(tmp_path: Path):
    book_dir = _project(tmp_path)
    css = tmp_path / "assets" / "interior.css"

    manifest = paginate(book_dir, read_order(book_dir))
    pdfs = render_all(book_dir, manifest, book_dir / "pdf")
    total = merge(pdfs, book_dir / "book.pdf")
    findings = verify(book_dir, manifest, css)

    assert manifest.total_pages() == 5
    assert total == 5
    assert not has_errors(findings)
    assert all(
        (round(w), round(h)) == (504, 720) for w, h in pdf_geometry_pt(book_dir / "book.pdf")
    )


def test_folios_are_continuous_across_chapters(tmp_path: Path):
    book_dir = _project(tmp_path)

    paginate(book_dir, read_order(book_dir))

    assert "counter-reset: page 0;" in (book_dir / "chapter-01.html").read_text("utf-8")
    assert "counter-reset: page 3;" in (book_dir / "chapter-02.html").read_text("utf-8")


def test_manifest_is_written_and_reloadable(tmp_path: Path):
    book_dir = _project(tmp_path)

    manifest = paginate(book_dir, read_order(book_dir))

    reloaded = Manifest.from_json((book_dir / MANIFEST_NAME).read_text("utf-8"))
    assert reloaded == manifest


def test_growing_a_chapter_is_caught_as_a_stale_manifest(tmp_path: Path):
    book_dir = _project(tmp_path)
    css = tmp_path / "assets" / "interior.css"
    manifest = paginate(book_dir, read_order(book_dir))

    _chapter(book_dir, 1, 4)  # the author added a page and forgot to re-paginate

    findings = verify(book_dir, manifest, css)

    assert has_errors(findings)
    assert any("stale" in f.message for f in findings)


def test_overstuffed_page_is_caught_as_clipping(tmp_path: Path):
    book_dir = _project(tmp_path)
    css = tmp_path / "assets" / "interior.css"
    path = book_dir / "chapter-02.html"
    path.write_text(
        path.read_text("utf-8").replace("<p>Body copy for section 0.</p>", "<p>x</p>" * 400),
        encoding="utf-8",
    )
    manifest = paginate(book_dir, read_order(book_dir))

    findings = verify(book_dir, manifest, css)

    assert has_errors(findings)
    assert any("clipped" in f.message for f in findings)
```

- [ ] **Step 2: Run the test**

```bash
cd skills/book-writing/scripts && uv run pytest tests/test_end_to_end.py -v
```

Expected: PASS if Tasks 1–11 are complete and correct. If a test fails, the failure names the defective stage — fix it there, not in the test.

- [ ] **Step 3: Run the whole suite**

```bash
cd skills/book-writing/scripts && uv run pytest -v
```

Expected: all tests pass across all nine test modules.

- [ ] **Step 4: Ignore build output**

Create or append to `.gitignore` at the repository root:

```gitignore
__pycache__/
*.pyc
.venv/
.pytest_cache/
uv.lock
book/pdf/
book/*.pdf
```

- [ ] **Step 5: Write the repository README**

Create `README.md` at the repository root covering: what the skill does, install (copy `skills/book-writing/` into `~/.claude/skills/`), first-time setup (`uv sync --extra dev && uv run playwright install chromium`), the six phases in one line each, how to run the test suite, and attribution — the structural and production design is distilled from `swiftugandan/specification-driven-delivery-book`, and the editorial gate delegates to `conorbronsdon/avoid-ai-writing`. State that no content from either source is redistributed.

- [ ] **Step 6: Commit**

```bash
git add skills/book-writing/scripts/tests/test_end_to_end.py README.md .gitignore
git commit -m "test: prove the book pipeline end to end"
```

---

## Self-Review

**Spec coverage.**

| Spec section | Task |
|---|---|
| Packaging / file structure | 1 (scaffold), 11 (SKILL.md) |
| ① Intake | 11 (SKILL.md phase ①) |
| ② Blueprint, driving question, page budget | 8 (template), 9 (reference) |
| ③ Interior tokens, two-layer CSS, layout discipline | 2 (guard), 7 (stylesheet), 10 (reference) |
| ④ Chapter pattern, 13 beats | 8 (template), 9 (reference) |
| ⑤ Editorial gate, avoid-ai-writing delegation | 9 (reference), 11 (SKILL.md phase ⑤) |
| ⑥ paginate / render / merge / verify | 1, 3, 4, 5, 6 (code), 10 (reference) |
| Hard-fail checks (geometry, clipping, layering, folio) | 6 |
| Page-budget warning | 6 |
| Self-containment | 1, 12 |
| No source-book content bundled | 9 (asserted by test) |

Every spec requirement maps to a task.

**Type consistency.** `PageExtent` (`file`, `index`, `box_px`, `content_px`, `width_px`, `overflow_px`) is produced in Task 1 and consumed unchanged in Tasks 4 and 6. `Manifest` / `ManifestEntry` (`file`, `pages`, `start_folio`) are produced in Task 3 and consumed in Tasks 4, 5, 6, 12. `CssViolation` (`file`, `selector`, `reason`) is produced in Task 2 and consumed in Task 6. `Finding` (`level`, `file`, `message`) is confined to Task 6 and its tests. `MANIFEST_NAME` is defined once in Task 4 and imported by Tasks 5, 6, 12. No name drifts between tasks.

**Deviation from spec.** The spec named `render.sh` driving system headless Chrome. This plan uses `render.py` on Playwright's bundled Chromium instead, because `paginate.py` needs the same engine for DOM measurement — two different Chromium builds could disagree on layout, and verification would then certify a page as fitting that the PDF clips. Same engine, different invocation.
