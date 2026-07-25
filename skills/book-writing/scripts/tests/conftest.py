from pathlib import Path

import pytest

PAGE_CSS = """
@page { size: 7in 10in; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body { counter-reset: page 0; }
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
"""


def write_book(dir_: Path, name: str, pages: list[str], extra_css: str = "") -> Path:
    """Write a minimal book page-file with one .page div per entry in `pages`."""
    body = "\n".join(f'<div class="page">{p}</div>' for p in pages)
    html = (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        f"<style>{PAGE_CSS}{extra_css}</style></head><body>{body}</body></html>"
    )
    path = dir_ / name
    path.write_text(html, encoding="utf-8")
    return path


@pytest.fixture
def book_dir(tmp_path: Path) -> Path:
    d = tmp_path / "book"
    d.mkdir()
    return d
