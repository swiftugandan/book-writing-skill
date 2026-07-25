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


def assign_folios(counts: Sequence[tuple[str, int]], first_folio: int = 1) -> Manifest:
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
