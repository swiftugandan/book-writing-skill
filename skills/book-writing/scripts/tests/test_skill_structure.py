import re
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2]
SKILL_MD = SKILL / "SKILL.md"


def _frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert match, "SKILL.md must open with YAML frontmatter"
    fields = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def test_skill_md_exists():
    assert SKILL_MD.exists()


def test_frontmatter_names_the_skill():
    assert _frontmatter(SKILL_MD.read_text(encoding="utf-8"))["name"] == "book-writing"


def test_description_carries_trigger_phrases():
    description = _frontmatter(SKILL_MD.read_text(encoding="utf-8"))["description"]

    assert len(description) > 80
    assert "book" in description.lower()
    assert "drafts" in description.lower()


def test_router_stays_short_enough_to_load_cheaply():
    words = len(SKILL_MD.read_text(encoding="utf-8").split())

    assert words < 900, f"SKILL.md is {words} words; move detail into references/"


def test_router_names_all_six_phases():
    text = SKILL_MD.read_text(encoding="utf-8").lower()

    for phase in ["intake", "blueprint", "interior", "chapter", "editorial",
                  "production"]:
        assert phase in text


def test_router_points_at_every_reference():
    text = SKILL_MD.read_text(encoding="utf-8")

    for ref in [
        "references/blueprint-format.md",
        "references/chapter-pattern.md",
        "references/editorial-standards.md",
        "references/interior-design.md",
        "references/production.md",
    ]:
        assert ref in text


def test_every_referenced_path_exists():
    text = SKILL_MD.read_text(encoding="utf-8")

    for rel in re.findall(r"(?:references|assets|scripts)/[A-Za-z0-9_.\-/]+", text):
        candidate = SKILL / rel.rstrip(".,)")
        if candidate.suffix:
            assert candidate.exists(), f"SKILL.md points at missing {rel}"


def test_router_names_the_drafts_input():
    assert "drafts/" in SKILL_MD.read_text(encoding="utf-8")


def test_router_requires_the_editorial_gate():
    assert "avoid-ai-writing" in SKILL_MD.read_text(encoding="utf-8")


def test_router_refuses_to_invent_source_material():
    text = SKILL_MD.read_text(encoding="utf-8").lower()

    assert "do not invent" in text or "never invent" in text
