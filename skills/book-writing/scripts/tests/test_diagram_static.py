import pytest

from bookkit.diagrams import length_to_pt, static_findings

CLEAN = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="5.7in" height="1in" '
    'viewBox="0 0 410.4 72">'
    '<rect x="0" y="0" width="80" height="40" fill="var(--paper, #ffffff)" '
    'stroke="var(--ink, #242424)"/>'
    '<text x="4" y="20" font-size="8" fill="var(--ink, #242424)">Step</text>'
    "</svg>"
)


def _messages(source: str) -> str:
    return " ".join(f.message for f in static_findings(source, "d.svg", 0))


def test_clean_diagram_produces_no_findings():
    assert static_findings(CLEAN, "d.svg", 0) == []


def test_every_finding_carries_the_file_and_diagram_index():
    bad = CLEAN.replace('fill="var(--paper, #ffffff)"', 'fill="#ff0000"')

    finding = static_findings(bad, "chapter-01.html", 2)[0]

    assert finding.file == "chapter-01.html"
    assert "diagram 3" in finding.message
    assert finding.level == "error"


def test_hardcoded_hex_fill_is_rejected():
    bad = CLEAN.replace('fill="var(--paper, #ffffff)"', 'fill="#ff0000"')

    assert "hardcoded" in _messages(bad)


def test_hardcoded_named_colour_is_rejected():
    bad = CLEAN.replace('stroke="var(--ink, #242424)"', 'stroke="black"')

    assert "hardcoded" in _messages(bad)


def test_hardcoded_rgb_function_is_rejected():
    bad = CLEAN.replace('fill="var(--paper, #ffffff)"', 'fill="rgb(1,2,3)"')

    assert "hardcoded" in _messages(bad)


def test_none_and_currentcolor_are_allowed():
    ok = CLEAN.replace('fill="var(--paper, #ffffff)"', 'fill="none"')
    ok = ok.replace('stroke="var(--ink, #242424)"', 'stroke="currentColor"')

    assert static_findings(ok, "d.svg", 0) == []


def test_fallback_hex_inside_a_var_is_allowed():
    """`var(--ink, #242424)` is the required form, not a hardcoded colour."""
    assert static_findings(CLEAN, "d.svg", 0) == []


def test_raster_image_element_is_rejected():
    bad = CLEAN.replace("</svg>", '<image href="photo.png"/></svg>')

    assert "raster" in _messages(bad) or "external" in _messages(bad)


def test_remote_url_is_rejected():
    bad = CLEAN.replace("</svg>", '<use href="https://example.com/a.svg#x"/></svg>')

    assert "external" in _messages(bad)


def test_gradient_is_rejected():
    bad = CLEAN.replace("</svg>", '<defs><linearGradient id="g"/></defs></svg>')

    assert "gradient" in _messages(bad)


def test_filter_and_drop_shadow_are_rejected():
    bad = CLEAN.replace("</svg>", '<filter id="f"><feDropShadow/></filter></svg>')

    assert "filter" in _messages(bad) or "shadow" in _messages(bad)


def test_missing_viewbox_is_rejected():
    bad = CLEAN.replace(' viewBox="0 0 410.4 72"', "")

    assert "viewBox" in _messages(bad)


def test_missing_width_is_rejected():
    bad = CLEAN.replace(' width="5.7in"', "")

    assert "width" in _messages(bad)


def test_pixel_dimensions_are_rejected():
    bad = CLEAN.replace('width="5.7in"', 'width="540px"')

    assert "px" in _messages(bad)


def test_unitless_dimensions_are_rejected():
    bad = CLEAN.replace('width="5.7in"', 'width="540"')

    assert "unit" in _messages(bad)


# --- length parsing -----------------------------------------------------------
# Print size comes from the declared width attribute, never from how a browser
# window happens to display the document.


@pytest.mark.parametrize(
    "value,expected",
    [
        ("72pt", 72.0),
        ("1in", 72.0),
        ("5.7in", 410.4),
        ("410.4pt", 410.4),
        ("25.4mm", 72.0),
        ("2.54cm", 72.0),
        ("96px", 72.0),
    ],
)
def test_length_to_pt_converts_each_unit(value: str, expected: float):
    assert length_to_pt(value) == pytest.approx(expected)


def test_length_to_pt_treats_a_bare_number_as_px():
    assert length_to_pt("96") == pytest.approx(72.0)


def test_length_to_pt_rejects_what_it_cannot_read():
    assert length_to_pt("") is None
    assert length_to_pt("auto") is None
    assert length_to_pt("50%") is None


# --- XML comment hygiene ------------------------------------------------------
# `--` is illegal inside an XML comment. An SVG carrying one still works inline
# in an HTML page, because the HTML parser is lenient, and fails to parse the
# moment the same file is saved standalone. It then renders nothing at all.


def test_double_hyphen_inside_a_comment_is_rejected():
    bad = CLEAN.replace("<rect", "<!-- uses --pale and --paper --><rect")

    assert "comment" in _messages(bad)


def test_an_ordinary_comment_is_allowed():
    ok = CLEAN.replace("<rect", "<!-- a perfectly normal note --><rect")

    assert static_findings(ok, "d.svg", 0) == []


def test_an_em_dash_in_a_comment_is_allowed():
    ok = CLEAN.replace("<rect", "<!-- a note, with an aside, in prose --><rect")

    assert static_findings(ok, "d.svg", 0) == []
