from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[2]
REFS = SKILL / "references"


@pytest.mark.parametrize(
    "name", ["blueprint-format.md", "chapter-pattern.md", "editorial-standards.md"]
)
def test_reference_exists_and_is_substantial(name: str):
    path = REFS / name
    assert path.exists()
    assert len(path.read_text(encoding="utf-8").split()) > 250


def test_blueprint_format_lists_every_required_field():
    text = (REFS / "blueprint-format.md").read_text(encoding="utf-8")

    for field in [
        "Promise",
        "Audience",
        "Reading paths",
        "Running examples",
        "driving question",
        "Standard chapter pattern",
        "Page budget",
    ]:
        assert field in text


def test_blueprint_format_points_at_the_template():
    text = (REFS / "blueprint-format.md").read_text(encoding="utf-8")

    assert "assets/STRUCTURE.template.md" in text


def test_chapter_pattern_marks_beats_required_or_optional():
    text = (REFS / "chapter-pattern.md").read_text(encoding="utf-8")

    assert "required" in text
    assert "where it fits" in text


def test_chapter_pattern_covers_all_thirteen_beats():
    text = (REFS / "chapter-pattern.md").read_text(encoding="utf-8").lower()

    for beat in [
        "opening situation",
        "chapter promise",
        "problem and consequences",
        "core concept",
        "step-by-step method",
        "worked example",
        "variant example",
        "failure modes",
        "field guide",
        "what to remember",
        "questions for the reader",
        "one action",
        "transition",
    ]:
        assert beat in text, f"missing beat: {beat}"


def test_editorial_standards_delegates_to_avoid_ai_writing():
    text = (REFS / "editorial-standards.md").read_text(encoding="utf-8")

    assert "avoid-ai-writing" in text
    assert "github.com/conorbronsdon/avoid-ai-writing" in text


def test_editorial_standards_keeps_the_evidence_classification():
    text = (REFS / "editorial-standards.md").read_text(encoding="utf-8").lower()

    for term in ["reported practice", "interpretation", "evidence", "speculation"]:
        assert term in text


def test_editorial_standards_does_not_prescribe_subject_matter():
    text = (REFS / "editorial-standards.md").read_text(encoding="utf-8").lower()

    for leaked in ["volunteer operations", "simon martinelli", "self-contained system"]:
        assert leaked not in text, f"source-book content leaked: {leaked}"
