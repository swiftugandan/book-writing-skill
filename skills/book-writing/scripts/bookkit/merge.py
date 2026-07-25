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
