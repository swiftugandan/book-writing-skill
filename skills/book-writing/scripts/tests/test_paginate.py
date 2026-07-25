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
