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
