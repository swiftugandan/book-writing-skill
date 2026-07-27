from pathlib import Path

from bookkit.diagrams import find_diagrams, rendered_findings

HOST = """<!doctype html><html><head><meta charset="utf-8"><style>
:root {{ --ink: #242424; --paper: #ffffff; --accent: #d54b20; --support: #177c83; }}
</style></head><body>{body}</body></html>"""

SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="288pt" height="72pt"
     viewBox="0 0 288 72">{content}</svg>"""

CLEAN = (
    '<rect x="10" y="10" width="100" height="40" fill="var(--paper, #fff)" '
    'stroke="var(--ink, #242424)"/>'
    '<text x="16" y="34" font-size="9" fill="var(--ink, #242424)">Reviewed</text>'
)


def _write(tmp_path: Path, content: str, name: str = "page.html") -> Path:
    path = tmp_path / name
    path.write_text(HOST.format(body=SVG.format(content=content)), encoding="utf-8")
    return path


def _messages(path: Path) -> str:
    return " ".join(f.message for d in find_diagrams(path) for f in rendered_findings(d))


def test_finds_one_diagram_per_svg_element(tmp_path: Path):
    path = tmp_path / "page.html"
    path.write_text(
        HOST.format(body=SVG.format(content=CLEAN) + SVG.format(content=CLEAN)),
        encoding="utf-8",
    )

    diagrams = find_diagrams(path)

    assert [d.index for d in diagrams] == [0, 1]
    assert all(d.file == "page.html" for d in diagrams)


def test_reads_the_viewbox_and_unit_scale(tmp_path: Path):
    diagram = find_diagrams(_write(tmp_path, CLEAN))[0]

    assert diagram.viewbox == (0.0, 0.0, 288.0, 72.0)
    assert round(diagram.scale_pt_per_unit, 3) == 1.0


def test_resolves_tokens_to_the_pages_computed_colours(tmp_path: Path):
    diagram = find_diagrams(_write(tmp_path, CLEAN))[0]

    assert diagram.shapes[0].stroke == "rgb(36, 36, 36)"


def test_clean_diagram_produces_no_rendered_findings(tmp_path: Path):
    assert _messages(_write(tmp_path, CLEAN)) == ""


def test_text_below_the_print_floor_is_rejected(tmp_path: Path):
    small = CLEAN.replace('font-size="9"', 'font-size="4"')

    assert "print floor" in _messages(_write(tmp_path, small))


def test_type_size_is_judged_after_viewbox_scaling(tmp_path: Path):
    """font-size 10 in a viewBox scaled by 0.5 renders at 5pt, under the floor."""
    path = tmp_path / "page.html"
    scaled = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="144pt" height="36pt" '
        'viewBox="0 0 288 72">'
        '<rect x="10" y="10" width="100" height="40" fill="var(--paper, #fff)"/>'
        '<text x="16" y="34" font-size="10" fill="var(--ink, #242424)">Reviewed</text>'
        "</svg>"
    )
    path.write_text(HOST.format(body=scaled), encoding="utf-8")

    diagram = find_diagrams(path)[0]

    assert round(diagram.scale_pt_per_unit, 3) == 0.5
    assert "print floor" in " ".join(f.message for f in rendered_findings(diagram))


def test_low_contrast_text_is_rejected(tmp_path: Path):
    faint = CLEAN.replace(
        '<text x="16" y="34" font-size="9" fill="var(--ink, #242424)">',
        '<text x="16" y="34" font-size="9" fill="var(--paper, #ffffff)">',
    )

    assert "contrast" in _messages(_write(tmp_path, faint))


def test_two_mid_tone_fills_without_a_differentiator_are_rejected(tmp_path: Path):
    """accent against support is 1.14:1 in greyscale."""
    pair = (
        '<rect x="10" y="10" width="60" height="40" fill="var(--accent, #d54b20)"/>'
        '<rect x="90" y="10" width="60" height="40" fill="var(--support, #177c83)"/>'
    )

    assert "greyscale" in _messages(_write(tmp_path, pair))


def test_a_dash_pattern_rescues_a_low_contrast_pair(tmp_path: Path):
    """Colour alone is not enough; colour plus another channel is."""
    pair = (
        '<rect x="10" y="10" width="60" height="40" fill="var(--accent, #d54b20)" '
        'stroke="var(--ink, #242424)"/>'
        '<rect x="90" y="10" width="60" height="40" fill="var(--support, #177c83)" '
        'stroke="var(--ink, #242424)" stroke-dasharray="4 2"/>'
    )

    assert _messages(_write(tmp_path, pair)) == ""


def test_content_outside_the_viewbox_is_rejected(tmp_path: Path):
    overflowing = CLEAN + (
        '<rect x="260" y="10" width="200" height="40" fill="none" '
        'stroke="var(--ink, #242424)"/>'
    )

    assert "viewBox" in _messages(_write(tmp_path, overflowing))


def test_reads_a_standalone_svg_file(tmp_path: Path):
    path = tmp_path / "diagram.svg"
    path.write_text(SVG.format(content=CLEAN), encoding="utf-8")

    diagrams = find_diagrams(path)

    assert len(diagrams) == 1
    assert diagrams[0].file == "diagram.svg"
