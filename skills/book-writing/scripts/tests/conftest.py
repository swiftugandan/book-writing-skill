from pathlib import Path

import pytest

CORE_CSS_NAME = "interior.css"

# The shared core layer, as a real page file would link it. `counter-reset`
# deliberately stays inline (see `write_book`) because bookkit.paginate rewrites
# it in the HTML source.
CORE_CSS = """
@page { size: 7in 10in; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
.page {
  position: relative;
  width: 7in;
  height: 10in;
  padding: .65in;
  overflow: hidden;
  break-after: page;
  counter-increment: page;
}
.page-number::after { content: counter(page); }
.callout { padding: 13px; }
"""


def write_book(
    dir_: Path, name: str, pages: list[str], extra_css: str = ""
) -> Path:
    """Write a page file that links the core stylesheet, as production does.

    `extra_css` lands in the inline `<style>` block — the chapter-local layer.
    """
    css_path = dir_ / CORE_CSS_NAME
    if not css_path.exists():
        css_path.write_text(CORE_CSS, encoding="utf-8")

    body = "\n".join(f'<div class="page">{p}</div>' for p in pages)
    html = (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        f"<link rel='stylesheet' href='{CORE_CSS_NAME}'>"
        f"<style>body {{ counter-reset: page 0; }}{extra_css}</style>"
        f"</head><body>{body}</body></html>"
    )
    path = dir_ / name
    path.write_text(html, encoding="utf-8")
    return path


@pytest.fixture
def book_dir(tmp_path: Path) -> Path:
    d = tmp_path / "book"
    d.mkdir()
    return d
