import re
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[3] / "svg-diagrams"
SKILL_MD = SKILL / "SKILL.md"
REFS = SKILL / "references"


def _frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert match, "SKILL.md must open with YAML frontmatter"
    fields = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


@pytest.mark.parametrize("name", ["grammar.md", "archetypes.md", "verification.md"])
def test_reference_exists_and_is_substantial(name: str):
    path = REFS / name
    assert path.exists()
    assert len(path.read_text(encoding="utf-8").split()) > 250


def test_skill_md_exists_and_is_named():
    assert _frontmatter(SKILL_MD.read_text(encoding="utf-8"))["name"] == "svg-diagrams"


def test_description_carries_trigger_phrases():
    description = _frontmatter(SKILL_MD.read_text(encoding="utf-8"))["description"]

    assert len(description) > 80
    assert "diagram" in description.lower()


def test_router_stays_short():
    words = len(SKILL_MD.read_text(encoding="utf-8").split())

    assert words < 700, f"SKILL.md is {words} words; move detail into references/"


def test_router_points_at_every_reference():
    text = SKILL_MD.read_text(encoding="utf-8")

    for ref in [
        "references/grammar.md",
        "references/archetypes.md",
        "references/verification.md",
    ]:
        assert ref in text


def test_every_referenced_path_exists():
    text = SKILL_MD.read_text(encoding="utf-8")

    for rel in re.findall(r"(?:references|assets)/[A-Za-z0-9_.\-/]+", text):
        candidate = SKILL / rel.rstrip(".,)")
        if candidate.suffix:
            assert candidate.exists(), f"SKILL.md points at missing {rel}"


def test_grammar_states_the_unit_convention():
    text = (REFS / "grammar.md").read_text(encoding="utf-8")

    assert "1 user unit = 1 point" in text or "one user unit is one point" in text.lower()


def test_grammar_states_the_text_measure():
    assert "410.4" in (REFS / "grammar.md").read_text(encoding="utf-8")


def test_grammar_explains_the_three_tonal_levels():
    text = (REFS / "grammar.md").read_text(encoding="utf-8").lower()

    assert "three" in text
    assert "1.14" in text, "the accent/support collapse is the motivating number"


def test_grammar_requires_token_colours():
    assert "var(--" in (REFS / "grammar.md").read_text(encoding="utf-8")


def test_archetypes_covers_all_six():
    text = (REFS / "archetypes.md").read_text(encoding="utf-8").lower()

    for archetype in [
        "flow",
        "layered stack",
        "node map",
        "pipeline",
        "cycle",
        "annotated anatomy",
    ]:
        assert archetype in text, f"missing archetype: {archetype}"


def test_archetypes_links_each_worked_example():
    text = (REFS / "archetypes.md").read_text(encoding="utf-8")

    for name in [
        "flow.svg",
        "pipeline.svg",
        "cycle.svg",
        "layered-stack.svg",
        "node-map.svg",
        "annotated-anatomy.svg",
    ]:
        assert name in text


def test_verification_names_the_command_and_thresholds():
    text = (REFS / "verification.md").read_text(encoding="utf-8")

    assert "bookkit.diagrams" in text
    assert "1.5" in text and "4.5" in text and "6pt" in text


def test_verification_explains_why_each_failure_is_silent():
    text = (REFS / "verification.md").read_text(encoding="utf-8").lower()

    assert "silent" in text
