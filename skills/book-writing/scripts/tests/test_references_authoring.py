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


def test_editorial_standards_separates_write_time_from_audit_time():
    text = (REFS / "editorial-standards.md").read_text(encoding="utf-8")

    assert "# Part one: write to these" in text
    assert "# Part two: audit what you wrote" in text
    assert text.index("Part one") < text.index("Part two")


def test_editorial_standards_lead_directs_reading_before_drafting():
    text = (REFS / "editorial-standards.md").read_text(encoding="utf-8")

    opening = text[: text.index("# Part one")]
    assert "before drafting" in opening.lower()


def test_write_time_half_carries_the_rhythm_constraints():
    """Structural uniformity is the strongest tell and the hardest to repair."""
    text = (REFS / "editorial-standards.md").read_text(encoding="utf-8")
    part_one = text[text.index("# Part one") : text.index("# Part two")]

    for constraint in ["sentence length", "paragraph length", "em dash"]:
        assert constraint in part_one.lower(), f"missing write-time rule: {constraint}"


def test_audit_half_prefers_detect_mode_over_blanket_rewriting():
    text = (REFS / "editorial-standards.md").read_text(encoding="utf-8")
    part_two = text[text.index("# Part two") :]

    assert "detect mode" in part_two.lower()
    assert "did not flag" in part_two.lower()


def test_editorial_standards_keeps_a_section_on_what_to_preserve():
    """A chapter that clears every pattern and reads sterile has failed differently."""
    text = (REFS / "editorial-standards.md").read_text(encoding="utf-8")

    assert "## Keep" in text
