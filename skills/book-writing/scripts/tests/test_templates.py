import re
from pathlib import Path

import pytest

from bookkit.cssguard import check_css_layering
from bookkit.measure import measure_file, px_to_pt
from bookkit.paginate import set_counter_offset

ASSETS = Path(__file__).resolve().parents[2] / "assets"
CSS_PATH = ASSETS / "interior.css"
HTML_TEMPLATES = [
    "chapter.template.html",
    "front-matter.template.html",
    "cover.template.html",
]


def _localised(name: str, tmp_path: Path) -> Path:
    """Copy a template with its stylesheet link resolved to an absolute URI."""
    source = (ASSETS / name).read_text(encoding="utf-8")
    probe = tmp_path / name
    probe.write_text(
        source.replace("../assets/interior.css", CSS_PATH.as_uri()), encoding="utf-8"
    )
    return probe


@pytest.mark.parametrize("name", HTML_TEMPLATES)
def test_template_exists(name: str):
    assert (ASSETS / name).exists()


@pytest.mark.parametrize("name", HTML_TEMPLATES)
def test_template_links_the_core_stylesheet(name: str):
    html = (ASSETS / name).read_text(encoding="utf-8")

    assert 'href="../assets/interior.css"' in html


@pytest.mark.parametrize("name", HTML_TEMPLATES)
def test_template_carries_a_rewritable_counter_reset(name: str):
    html = (ASSETS / name).read_text(encoding="utf-8")

    assert set_counter_offset(html, 5) != html


@pytest.mark.parametrize("name", HTML_TEMPLATES)
def test_template_declares_at_least_one_page(name: str):
    html = (ASSETS / name).read_text(encoding="utf-8")

    assert 'class="page' in html


@pytest.mark.parametrize("name", HTML_TEMPLATES)
def test_template_respects_css_layering(name: str, tmp_path: Path):
    assert check_css_layering(_localised(name, tmp_path), CSS_PATH) == []


def test_chapter_template_renders_at_the_declared_geometry(tmp_path: Path):
    for extent in measure_file(_localised("chapter.template.html", tmp_path)):
        assert round(px_to_pt(extent.width_px)) == 504
        assert round(px_to_pt(extent.box_px)) == 720


def test_chapter_template_pages_do_not_overflow(tmp_path: Path):
    extents = measure_file(_localised("chapter.template.html", tmp_path))

    overflowing = [e.index for e in extents if e.overflow_px > 1.0]
    assert overflowing == []


def test_chapter_template_marks_every_required_beat():
    html = (ASSETS / "chapter.template.html").read_text(encoding="utf-8")

    for beat in [
        "OPENING SITUATION",
        "CHAPTER PROMISE",
        "PROBLEM AND CONSEQUENCES",
        "CORE CONCEPT",
        "STEP-BY-STEP METHOD",
        "WORKED EXAMPLE",
        "FAILURE MODES",
        "FIELD GUIDE",
        "WHAT TO REMEMBER",
        "ONE ACTION",
        "TRANSITION",
    ]:
        assert beat in html, f"chapter template is missing the {beat} beat"


def test_structure_template_declares_every_required_field():
    md = (ASSETS / "STRUCTURE.template.md").read_text(encoding="utf-8")

    for field in [
        "## Promise",
        "## Audience",
        "## Reading paths",
        "## Running examples",
        "# Standard chapter pattern",
        "# Page budget",
    ]:
        assert field in md


def test_structure_template_requires_a_driving_question_per_chapter():
    md = (ASSETS / "STRUCTURE.template.md").read_text(encoding="utf-8")

    assert re.search(r"\*\*Question:\*\*", md)
