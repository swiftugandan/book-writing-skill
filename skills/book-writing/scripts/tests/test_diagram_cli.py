from pathlib import Path

from bookkit.diagrams import check_diagrams, main
from bookkit.findings import has_errors

HOST = """<!doctype html><html><head><meta charset="utf-8"><style>
:root {{ --ink: #242424; --paper: #ffffff; }}
</style></head><body>{body}</body></html>"""

GOOD = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="288pt" height="72pt" '
    'viewBox="0 0 288 72">'
    '<rect x="10" y="10" width="100" height="40" fill="var(--paper, #fff)" '
    'stroke="var(--ink, #242424)"/>'
    '<text x="16" y="34" font-size="9" fill="var(--ink, #242424)">Reviewed</text>'
    "</svg>"
)
BAD = GOOD.replace('fill="var(--paper, #fff)"', 'fill="#ff0000"')


def _page(tmp_path: Path, svg: str, name: str = "page.html") -> Path:
    path = tmp_path / name
    path.write_text(HOST.format(body=svg), encoding="utf-8")
    return path


def test_clean_page_produces_no_findings(tmp_path: Path):
    assert check_diagrams([_page(tmp_path, GOOD)]) == []


def test_static_and_rendered_findings_are_combined(tmp_path: Path):
    small = BAD.replace('font-size="9"', 'font-size="3"')

    joined = " ".join(f.message for f in check_diagrams([_page(tmp_path, small)]))

    assert "hardcoded" in joined
    assert "print floor" in joined


def test_a_page_with_no_diagrams_is_fine(tmp_path: Path):
    path = tmp_path / "page.html"
    path.write_text(HOST.format(body="<p>no diagrams here</p>"), encoding="utf-8")

    assert check_diagrams([path]) == []


def test_checks_a_standalone_svg_file(tmp_path: Path):
    path = tmp_path / "diagram.svg"
    path.write_text(BAD, encoding="utf-8")

    assert has_errors(check_diagrams([path]))


def test_cli_exits_zero_on_a_clean_file(tmp_path: Path):
    assert main([str(_page(tmp_path, GOOD))]) == 0


def test_cli_exits_one_and_names_the_problem(tmp_path: Path, capsys):
    assert main([str(_page(tmp_path, BAD))]) == 1
    assert "hardcoded" in capsys.readouterr().out


def test_cli_accepts_a_directory(tmp_path: Path):
    book = tmp_path / "book"
    book.mkdir()
    _page(book, GOOD, "chapter-01.html")
    _page(book, BAD, "chapter-02.html")

    assert main([str(book)]) == 1
