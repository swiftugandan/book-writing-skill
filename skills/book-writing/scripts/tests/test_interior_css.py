from pathlib import Path

from bookkit.cssguard import core_selectors
from bookkit.measure import measure_file, px_to_pt

CSS_PATH = Path(__file__).resolve().parents[2] / "assets" / "interior.css"

REQUIRED_TOKENS = [
    "--page-w",
    "--page-h",
    "--margin",
    "--ink",
    "--paper",
    "--accent",
    "--serif",
    "--sans",
    "--mono",
]

REQUIRED_CLASSES = {
    "page", "with-head", "running-head", "page-number", "folio-title",
    "eyebrow", "deck", "lead", "small", "micro", "dropcap", "opener-number",
    "principle", "quote", "callout", "label", "spec", "artifact", "steps",
    "checklist", "comparison-row", "matrix", "flow-box", "columns-2",
    "columns-3", "sidebar-grid", "rule", "accent-rule", "signature", "caption",
}


def test_stylesheet_exists():
    assert CSS_PATH.exists()


def test_declares_every_design_token():
    css = CSS_PATH.read_text(encoding="utf-8")

    missing = [token for token in REQUIRED_TOKENS if f"{token}:" not in css]
    assert missing == []


def test_defines_the_core_component_vocabulary():
    missing = REQUIRED_CLASSES - core_selectors(CSS_PATH)

    assert missing == set()


def test_no_core_class_uses_the_chapter_local_prefix():
    assert not any(name.startswith("ch-") for name in core_selectors(CSS_PATH))


def test_forbidden_decorative_properties_are_absent():
    css = CSS_PATH.read_text(encoding="utf-8")

    for banned in ("box-shadow", "linear-gradient", "radial-gradient", "text-shadow"):
        assert banned not in css, f"{banned} violates the layout discipline"


def test_page_renders_at_the_declared_geometry(tmp_path: Path):
    html = tmp_path / "probe.html"
    html.write_text(
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<link rel='stylesheet' href='{CSS_PATH.as_uri()}'></head>"
        "<body><div class='page'><p>probe</p></div></body></html>",
        encoding="utf-8",
    )

    extent = measure_file(html)[0]

    assert round(px_to_pt(extent.width_px)) == 504
    assert round(px_to_pt(extent.box_px)) == 720


def test_retargeting_the_page_tokens_changes_the_geometry(tmp_path: Path):
    html = tmp_path / "probe.html"
    html.write_text(
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<link rel='stylesheet' href='{CSS_PATH.as_uri()}'>"
        "<style>:root { --page-w: 6in; --page-h: 9in; }</style></head>"
        "<body><div class='page'><p>probe</p></div></body></html>",
        encoding="utf-8",
    )

    extent = measure_file(html)[0]

    assert round(px_to_pt(extent.width_px)) == 432
    assert round(px_to_pt(extent.box_px)) == 648
