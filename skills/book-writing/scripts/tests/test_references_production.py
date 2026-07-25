from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[2]
REFS = SKILL / "references"


@pytest.mark.parametrize("name", ["interior-design.md", "production.md"])
def test_reference_exists_and_is_substantial(name: str):
    path = REFS / name
    assert path.exists()
    assert len(path.read_text(encoding="utf-8").split()) > 250


def test_interior_design_documents_every_token():
    text = (REFS / "interior-design.md").read_text(encoding="utf-8")

    for token in ["--page-w", "--page-h", "--margin", "--ink", "--paper",
                  "--accent", "--serif", "--sans", "--mono"]:
        assert token in text


def test_interior_design_explains_the_two_css_layers():
    text = (REFS / "interior-design.md").read_text(encoding="utf-8")

    assert "ch-" in text
    assert "interior.css" in text
    assert "shadow" in text.lower()


def test_interior_design_states_the_layout_discipline():
    text = (REFS / "interior-design.md").read_text(encoding="utf-8").lower()

    assert "grayscale" in text or "greyscale" in text
    assert "colour alone" in text or "color alone" in text
    assert "gradient" in text


def test_production_documents_the_folio_offset_rule():
    text = (REFS / "production.md").read_text(encoding="utf-8")

    assert "counter-reset" in text
    assert "F - 1" in text or "start_folio - 1" in text


def test_production_names_every_cli():
    text = (REFS / "production.md").read_text(encoding="utf-8")

    for module in ["bookkit.paginate", "bookkit.render", "bookkit.merge",
                   "bookkit.verify"]:
        assert module in text


def test_production_lists_the_hard_failures_and_the_warning():
    text = (REFS / "production.md").read_text(encoding="utf-8").lower()

    for failure in ["geometry", "clip", "layering", "folio"]:
        assert failure in text
    assert "budget" in text


def test_production_explains_the_single_engine_requirement():
    text = (REFS / "production.md").read_text(encoding="utf-8").lower()

    assert "same" in text and "chromium" in text
