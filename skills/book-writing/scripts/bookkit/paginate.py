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


def paginate(book_dir: Path, order: Sequence[str], first_folio: int = 1) -> Manifest:
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
