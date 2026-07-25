from pathlib import Path

from bookkit.cssguard import (
    CssViolation,
    check_css_layering,
    core_selectors,
    local_selectors,
)

CORE = """
:root { --ink: #242424; }
.page { width: 7in; }
.page-number::after { content: counter(page); }
.callout { padding: 13px; }
.callout.teal { border-top-color: teal; }
h1, h2, .sans { font-family: sans-serif; }
"""


def _write(tmp_path: Path, css: str, inline: str) -> tuple[Path, Path]:
    css_path = tmp_path / "interior.css"
    css_path.write_text(css, encoding="utf-8")
    html_path = tmp_path / "chapter-01.html"
    html_path.write_text(
        f"<!doctype html><html><head><style>{inline}</style></head>"
        "<body><div class='page'></div></body></html>",
        encoding="utf-8",
    )
    return html_path, css_path


def test_core_selectors_extracts_class_names(tmp_path: Path):
    css_path = tmp_path / "interior.css"
    css_path.write_text(CORE, encoding="utf-8")

    assert core_selectors(css_path) == {"page", "page-number", "callout", "teal", "sans"}


def test_local_selectors_reads_inline_style_block(tmp_path: Path):
    html_path, _ = _write(tmp_path, CORE, ".ch-kanban { display: grid; }")

    assert local_selectors(html_path) == {"ch-kanban"}


def test_local_selectors_empty_when_no_style_block(tmp_path: Path):
    html_path = tmp_path / "chapter-01.html"
    html_path.write_text("<!doctype html><html><body></body></html>", encoding="utf-8")

    assert local_selectors(html_path) == frozenset()


def test_prefixed_novel_selector_is_allowed(tmp_path: Path):
    html_path, css_path = _write(tmp_path, CORE, ".ch-usecase-map { display: grid; }")

    assert check_css_layering(html_path, css_path) == []


def test_unprefixed_local_selector_is_a_violation(tmp_path: Path):
    html_path, css_path = _write(tmp_path, CORE, ".kanban { display: grid; }")

    assert check_css_layering(html_path, css_path) == [
        CssViolation(file="chapter-01.html", selector="kanban", reason="unprefixed")
    ]


def test_local_redefinition_of_core_selector_is_a_violation(tmp_path: Path):
    html_path, css_path = _write(tmp_path, CORE, ".callout { padding: 40px; }")

    assert check_css_layering(html_path, css_path) == [
        CssViolation(file="chapter-01.html", selector="callout", reason="shadows-core")
    ]


def test_prefixed_name_colliding_with_core_is_still_shadowing(tmp_path: Path):
    core = CORE + "\n.ch-legacy { color: red; }\n"
    html_path, css_path = _write(tmp_path, core, ".ch-legacy { color: blue; }")

    assert check_css_layering(html_path, css_path) == [
        CssViolation(file="chapter-01.html", selector="ch-legacy", reason="shadows-core")
    ]


def test_violations_are_sorted_by_selector(tmp_path: Path):
    html_path, css_path = _write(tmp_path, CORE, ".zebra{color:red}.alpha{color:blue}")

    assert [v.selector for v in check_css_layering(html_path, css_path)] == [
        "alpha",
        "zebra",
    ]
