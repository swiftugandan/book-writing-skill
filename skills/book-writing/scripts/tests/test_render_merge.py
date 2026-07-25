from pathlib import Path

import pytest

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


def test_render_geometry_follows_the_caller_not_the_at_page_rule(book_dir: Path):
    """A retargeted book must not print onto the stylesheet's default trim."""
    write_book(book_dir, "a.html", ["<p>a</p>"])
    manifest = assign_folios([("a.html", 1)])

    pdfs = render_all(
        book_dir, manifest, book_dir / "out", page_w="6in", page_h="9in"
    )

    width, height = pdf_geometry_pt(pdfs[0])[0]
    assert (round(width), round(height)) == (432, 648)


def test_merge_accepts_a_matching_expected_page_count(book_dir: Path):
    write_book(book_dir, "a.html", ["<p>a</p>", "<p>b</p>"])
    manifest = assign_folios([("a.html", 2)])
    pdfs = render_all(book_dir, manifest, book_dir / "out")

    assert merge(pdfs, book_dir / "book.pdf", expected_pages=2) == 2


def test_merge_rejects_a_page_count_that_disagrees_with_the_manifest(book_dir: Path):
    """A render/measure disagreement must not ship as a finished PDF."""
    write_book(book_dir, "a.html", ["<p>a</p>", "<p>b</p>"])
    manifest = assign_folios([("a.html", 2)])
    pdfs = render_all(book_dir, manifest, book_dir / "out")

    with pytest.raises(ValueError, match="manifest says 5"):
        merge(pdfs, book_dir / "book.pdf", expected_pages=5)
