import pytest

from bookkit.manifest import (
    Manifest,
    ManifestEntry,
    assign_folios,
    folio_discontinuities,
)


def test_assign_folios_starts_at_one_by_default():
    manifest = assign_folios([("front-matter.html", 4), ("chapter-01.html", 12)])

    assert manifest.entries == (
        ManifestEntry(file="front-matter.html", pages=4, start_folio=1),
        ManifestEntry(file="chapter-01.html", pages=12, start_folio=5),
    )


def test_assign_folios_honours_a_custom_first_folio():
    manifest = assign_folios([("chapter-01.html", 3)], first_folio=9)

    assert manifest.entries[0].start_folio == 9


def test_assign_folios_accumulates_across_many_files():
    manifest = assign_folios([("a.html", 2), ("b.html", 5), ("c.html", 1)])

    assert [e.start_folio for e in manifest.entries] == [1, 3, 8]


def test_total_pages_sums_entries():
    assert assign_folios([("a.html", 2), ("b.html", 5)]).total_pages() == 7


def test_entry_for_returns_the_named_entry():
    manifest = assign_folios([("a.html", 2), ("b.html", 5)])

    assert manifest.entry_for("b.html").start_folio == 3


def test_entry_for_raises_on_unknown_file():
    manifest = assign_folios([("a.html", 2)])

    with pytest.raises(KeyError, match="missing.html"):
        manifest.entry_for("missing.html")


def test_json_round_trips():
    manifest = assign_folios([("a.html", 2), ("b.html", 5)])

    assert Manifest.from_json(manifest.to_json()) == manifest


def test_json_is_human_readable_and_stable():
    text = assign_folios([("a.html", 2)]).to_json()

    assert '"file": "a.html"' in text
    assert text.endswith("\n")


def test_no_discontinuities_in_a_well_formed_manifest():
    assert folio_discontinuities(assign_folios([("a.html", 2), ("b.html", 5)])) == []


def test_detects_a_gap_between_entries():
    manifest = Manifest(
        entries=(
            ManifestEntry(file="a.html", pages=2, start_folio=1),
            ManifestEntry(file="b.html", pages=5, start_folio=9),
        )
    )

    problems = folio_discontinuities(manifest)

    assert len(problems) == 1
    assert "b.html" in problems[0]
    assert "expected 3" in problems[0]


def test_detects_a_wrong_first_folio():
    manifest = Manifest(entries=(ManifestEntry(file="a.html", pages=2, start_folio=4),))

    assert "expected 1" in folio_discontinuities(manifest)[0]
