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
            Finding(
                level="error", file=problem.split(":")[0], message=f"folio {problem}"
            )
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
    css_path = args.css or args.book_dir / "interior.css"

    findings = verify(args.book_dir, manifest, css_path, (args.width_pt, args.height_pt))
    for finding in findings:
        print(f"{finding.level.upper():<7} {finding.file}: {finding.message}")
    if has_errors(findings):
        print(f"\nFAILED: {sum(f.level == 'error' for f in findings)} error(s)")
        return 1
    print(f"OK: {manifest.total_pages()} pages verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
