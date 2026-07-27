from pathlib import Path

from bookkit.manifest import Manifest, ManifestEntry, assign_folios
from bookkit.verify import Finding, has_errors, verify
from tests.conftest import CORE_CSS_NAME, write_book

def _css(book_dir: Path) -> Path:
    """The core stylesheet `write_book` linked into every page file."""
    return book_dir / CORE_CSS_NAME


def test_clean_book_produces_no_findings(book_dir: Path):
    write_book(book_dir, "a.html", ["<p>a</p>", "<p>b</p>"])
    manifest = assign_folios([("a.html", 2)])

    assert verify(book_dir, manifest, _css(book_dir)) == []


def test_overflowing_page_is_an_error(book_dir: Path):
    write_book(book_dir, "a.html", ["<p>x</p>" * 400])
    manifest = assign_folios([("a.html", 1)])

    findings = verify(book_dir, manifest, _css(book_dir))

    assert has_errors(findings)
    assert any("clipped" in f.message for f in findings if f.level == "error")


def test_wrong_geometry_is_an_error(book_dir: Path):
    write_book(book_dir, "a.html", ["<p>a</p>"])
    manifest = assign_folios([("a.html", 1)])

    findings = verify(book_dir, manifest, _css(book_dir), expected_pt=(432.0, 648.0))

    assert has_errors(findings)
    assert any("geometry" in f.message for f in findings)


def test_unprefixed_local_selector_is_an_error(book_dir: Path):
    write_book(book_dir, "a.html", ["<p>a</p>"], extra_css=".kanban { color: red; }")
    manifest = assign_folios([("a.html", 1)])

    findings = verify(book_dir, manifest, _css(book_dir))

    assert has_errors(findings)
    assert any("kanban" in f.message for f in findings)


def test_local_redefinition_of_core_is_an_error(book_dir: Path):
    write_book(book_dir, "a.html", ["<p>a</p>"], extra_css=".callout { padding: 0; }")
    manifest = assign_folios([("a.html", 1)])

    findings = verify(book_dir, manifest, _css(book_dir))

    assert any("shadows-core" in f.message for f in findings if f.level == "error")


def test_folio_discontinuity_is_an_error(book_dir: Path):
    write_book(book_dir, "a.html", ["<p>a</p>"])
    write_book(book_dir, "b.html", ["<p>b</p>"])
    broken = Manifest(
        entries=(
            ManifestEntry(file="a.html", pages=1, start_folio=1),
            ManifestEntry(file="b.html", pages=1, start_folio=7),
        )
    )

    findings = verify(book_dir, broken, _css(book_dir))

    assert any("folio" in f.message for f in findings if f.level == "error")


def test_stale_manifest_page_count_is_an_error(book_dir: Path):
    write_book(book_dir, "a.html", ["<p>a</p>", "<p>b</p>", "<p>c</p>"])
    stale = assign_folios([("a.html", 2)])

    findings = verify(book_dir, stale, _css(book_dir))

    assert any("stale" in f.message for f in findings if f.level == "error")


def test_budget_drift_is_a_warning_not_an_error(book_dir: Path):
    write_book(book_dir, "a.html", ["<p>a</p>", "<p>b</p>", "<p>c</p>"])
    manifest = assign_folios([("a.html", 3)])

    findings = verify(book_dir, manifest, _css(book_dir), budget={"a.html": 12})

    assert not has_errors(findings)
    assert [f.level for f in findings] == ["warning"]
    assert "budget" in findings[0].message


def test_budget_match_produces_no_warning(book_dir: Path):
    write_book(book_dir, "a.html", ["<p>a</p>", "<p>b</p>"])
    manifest = assign_folios([("a.html", 2)])

    assert verify(book_dir, manifest, _css(book_dir), budget={"a.html": 2}) == []


def test_has_errors_ignores_warnings():
    warning = Finding(level="warning", file="a.html", message="budget drift")

    assert not has_errors([warning])
    assert has_errors([warning, Finding(level="error", file="a.html", message="x")])


def test_verify_rejects_a_page_whose_diagram_breaks_the_rules(book_dir: Path):
    """The book pipeline covers diagrams with no extra command."""
    bad_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="288pt" height="72pt" '
        'viewBox="0 0 288 72">'
        '<rect x="10" y="10" width="100" height="40" fill="#ff0000"/>'
        "</svg>"
    )
    write_book(book_dir, "a.html", [f"<p>a</p>{bad_svg}"])
    manifest = assign_folios([("a.html", 1)])

    findings = verify(book_dir, manifest, _css(book_dir))

    assert has_errors(findings)
    assert any("hardcoded" in f.message for f in findings)


def test_verify_accepts_a_page_with_a_clean_diagram(book_dir: Path):
    good_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="288pt" height="72pt" '
        'viewBox="0 0 288 72">'
        '<rect x="10" y="10" width="100" height="40" fill="var(--paper, #ffffff)" '
        'stroke="var(--ink, #242424)"/>'
        '<text x="16" y="34" font-size="9" fill="var(--ink, #242424)">Step</text>'
        "</svg>"
    )
    write_book(book_dir, "a.html", [f"<p>a</p>{good_svg}"])
    manifest = assign_folios([("a.html", 1)])

    assert verify(book_dir, manifest, _css(book_dir)) == []
