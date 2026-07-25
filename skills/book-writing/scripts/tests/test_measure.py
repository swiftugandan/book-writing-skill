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
