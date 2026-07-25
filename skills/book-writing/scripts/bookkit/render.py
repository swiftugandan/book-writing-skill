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
    for path in render_all(args.book_dir, manifest, out_dir, args.page_w, args.page_h):
        print(f"rendered {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
