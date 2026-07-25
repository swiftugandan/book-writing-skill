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


def merge(pdfs: Sequence[Path], out: Path, expected_pages: int | None = None) -> int:
    """Concatenate `pdfs` in order into `out`, returning the total page count.

    When `expected_pages` is given, a disagreement raises rather than writing a
    book that does not match the one the manifest describes. The usual cause is
    a page file whose stylesheet failed to load, so Chromium never applied the
    fixed `.page` height and printed a different number of physical pages than
    there are `.page` elements.
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    for pdf in pdfs:
        for page in PdfReader(str(pdf)).pages:
            writer.add_page(page)

    total = len(writer.pages)
    if expected_pages is not None and total != expected_pages:
        raise ValueError(
            f"rendered {total} pages but the manifest says {expected_pages}. "
            "The sources and the PDFs disagree. Check that every page file "
            "resolves its stylesheet, then re-run bookkit.paginate"
        )

    with out.open("wb") as handle:
        writer.write(handle)
    return total


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

    try:
        total = merge(pdfs, out, expected_pages=manifest.total_pages())
    except ValueError as error:
        print(f"FAILED: {error}")
        return 1
    print(f"merged {len(pdfs)} files into {out} ({total} pages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
