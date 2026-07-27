from pathlib import Path

import pytest

from bookkit.diagrams import check_diagrams, find_diagrams

SVG_SKILL = Path(__file__).resolve().parents[3] / "svg-diagrams"
ASSETS = SVG_SKILL / "assets"
EXAMPLES = ASSETS / "examples"

EXPECTED = [
    "flow.svg",
    "pipeline.svg",
    "cycle.svg",
    "layered-stack.svg",
    "node-map.svg",
    "annotated-anatomy.svg",
]


def test_template_exists():
    assert (ASSETS / "diagram.template.svg").exists()


@pytest.mark.parametrize("name", EXPECTED)
def test_example_exists(name: str):
    assert (EXAMPLES / name).exists()


def test_template_passes_the_checker():
    findings = check_diagrams([ASSETS / "diagram.template.svg"])

    assert findings == [], "\n".join(f.message for f in findings)


@pytest.mark.parametrize("name", EXPECTED)
def test_example_passes_the_checker(name: str):
    findings = check_diagrams([EXAMPLES / name])

    assert findings == [], "\n".join(f.message for f in findings)


@pytest.mark.parametrize("name", EXPECTED)
def test_example_uses_one_unit_per_point(name: str):
    """The grammar mandates it so authors never reason about scaling."""
    diagram = find_diagrams(EXAMPLES / name)[0]

    assert round(diagram.scale_pt_per_unit, 3) == 1.0


@pytest.mark.parametrize("name", EXPECTED)
def test_example_fits_the_text_measure(name: str):
    """410.4pt is --page-w minus twice --margin at the default trim."""
    diagram = find_diagrams(EXAMPLES / name)[0]

    assert diagram.viewbox[2] <= 410.4


@pytest.mark.parametrize("name", EXPECTED)
def test_example_describes_itself_for_a_reader_who_cannot_see_it(name: str):
    source = (EXAMPLES / name).read_text(encoding="utf-8")

    assert 'role="img"' in source
    assert "aria-label=" in source
