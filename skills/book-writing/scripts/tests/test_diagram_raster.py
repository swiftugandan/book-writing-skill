"""The rendered pass.

Every other check reads what the SVG declares. These read what it draws, which
is the only way to catch paint that never reaches the page: `fill-opacity` near
zero, an `opacity="0"` group, or a diagram with no painted content at all.
"""

from pathlib import Path

from bookkit.diagrams import find_diagrams, rasterised_findings

HOST = """<!doctype html><html><head><meta charset="utf-8"><style>
:root {{ --ink: #242424; --paper: #ffffff; --pale: #f1f1f1;
         --accent: #d54b20; --support: #177c83; }}
body {{ margin: 0; background: #ffffff; }}
</style></head><body>{body}</body></html>"""

SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="288pt" height="72pt"
     viewBox="0 0 288 72">{content}</svg>"""

CLEAN = (
    '<rect x="10" y="10" width="100" height="40" fill="var(--paper, #fff)" '
    'stroke="var(--ink, #242424)"/>'
    '<text x="16" y="34" font-size="9" fill="var(--ink, #242424)">Reviewed</text>'
)


def _write(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "page.html"
    path.write_text(HOST.format(body=SVG.format(content=content)), encoding="utf-8")
    return path


def _messages(path: Path) -> str:
    return " ".join(
        f.message for d in find_diagrams(path) for f in rasterised_findings(d)
    )


def test_a_drawn_diagram_produces_no_findings(tmp_path: Path):
    assert _messages(_write(tmp_path, CLEAN)) == ""


def test_ink_coverage_is_measured(tmp_path: Path):
    diagram = find_diagrams(_write(tmp_path, CLEAN))[0]

    assert 0 < diagram.ink_coverage < 1


def test_a_diagram_with_no_painted_content_is_rejected(tmp_path: Path):
    """`fill="none"` leaves nothing to compare, so only pixels catch this."""
    empty = '<rect x="10" y="10" width="100" height="40" fill="none" stroke="none"/>'

    assert "blank" in _messages(_write(tmp_path, empty))


def test_a_fully_transparent_group_is_rejected(tmp_path: Path):
    hidden = (
        '<g opacity="0">'
        '<rect x="10" y="10" width="100" height="40" fill="var(--ink, #242424)"/>'
        "</g>"
    )

    assert "blank" in _messages(_write(tmp_path, hidden))


def test_a_shape_that_declares_ink_and_renders_paper_is_rejected(tmp_path: Path):
    """fill-opacity is invisible to computed style; the fill still reads as ink."""
    faded = (
        '<rect x="10" y="10" width="100" height="40" fill="var(--ink, #242424)" '
        'fill-opacity="0.02" stroke="var(--ink, #242424)"/>'
        '<text x="16" y="34" font-size="9" fill="var(--ink, #242424)">Reviewed</text>'
    )

    assert "renders" in _messages(_write(tmp_path, faded))


def test_a_shape_legitimately_filled_with_paper_is_not_flagged(tmp_path: Path):
    """Declaring paper and rendering paper is correct, not a defect."""
    assert "renders" not in _messages(_write(tmp_path, CLEAN))


def test_opacity_driven_tonal_collapse_is_rejected(tmp_path: Path):
    """Ink against paper is 15.5:1 on declared values. Greyed out to a tenth,
    the two render a fifth of that apart, and only pixels show it."""
    collapsed = (
        '<rect x="10" y="10" width="60" height="40" fill="var(--ink, #242424)" '
        'fill-opacity="0.1" stroke="none"/>'
        '<rect x="90" y="10" width="60" height="40" fill="var(--paper, #ffffff)" '
        'stroke="none"/>'
        '<rect x="4" y="4" width="280" height="64" fill="none" '
        'stroke="var(--ink, #242424)"/>'
    )

    assert "render" in _messages(_write(tmp_path, collapsed))


def test_findings_name_the_file_and_diagram(tmp_path: Path):
    empty = '<rect x="10" y="10" width="100" height="40" fill="none" stroke="none"/>'
    path = _write(tmp_path, empty)

    finding = [f for d in find_diagrams(path) for f in rasterised_findings(d)][0]

    assert finding.file == "page.html"
    assert "diagram 1" in finding.message
    assert finding.level == "error"
