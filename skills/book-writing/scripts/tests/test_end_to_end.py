import shutil
from pathlib import Path

from bookkit.manifest import Manifest
from bookkit.merge import merge, pdf_geometry_pt
from bookkit.paginate import MANIFEST_NAME, paginate, read_order
from bookkit.render import render_all
from bookkit.verify import has_errors, verify

SKILL = Path(__file__).resolve().parents[2]
ASSETS = SKILL / "assets"

PAGE = """<div class="page with-head">
  <div class="running-head"><span>Probe</span><span>Chapter {n}</span></div>
  <h2>Section {i}</h2><p>Body copy for section {i}.</p>
  <div class="folio-title">Chapter {n}</div><div class="page-number"></div>
</div>"""


def _chapter(book_dir: Path, n: int, pages: int) -> None:
    body = "\n".join(PAGE.format(n=n, i=i) for i in range(pages))
    (book_dir / f"chapter-{n:02d}.html").write_text(
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        f"<title>Probe — Chapter {n}</title>"
        '<link rel="stylesheet" href="../assets/interior.css">'
        "<style>body { counter-reset: page 0; }</style></head>"
        f"<body>{body}</body></html>",
        encoding="utf-8",
    )


def _project(tmp_path: Path) -> Path:
    shutil.copytree(ASSETS, tmp_path / "assets")
    book_dir = tmp_path / "book"
    book_dir.mkdir()
    _chapter(book_dir, 1, 3)
    _chapter(book_dir, 2, 2)
    (book_dir / "book.order").write_text(
        "chapter-01.html\nchapter-02.html\n", encoding="utf-8"
    )
    return book_dir


def test_full_pipeline_produces_a_verified_pdf(tmp_path: Path):
    book_dir = _project(tmp_path)
    css = tmp_path / "assets" / "interior.css"

    manifest = paginate(book_dir, read_order(book_dir))
    pdfs = render_all(book_dir, manifest, book_dir / "pdf")
    total = merge(pdfs, book_dir / "book.pdf")
    findings = verify(book_dir, manifest, css)

    assert manifest.total_pages() == 5
    assert total == 5
    assert not has_errors(findings)
    assert all(
        (round(w), round(h)) == (504, 720)
        for w, h in pdf_geometry_pt(book_dir / "book.pdf")
    )


def test_folios_are_continuous_across_chapters(tmp_path: Path):
    book_dir = _project(tmp_path)

    paginate(book_dir, read_order(book_dir))

    assert "counter-reset: page 0;" in (book_dir / "chapter-01.html").read_text("utf-8")
    assert "counter-reset: page 3;" in (book_dir / "chapter-02.html").read_text("utf-8")


def test_manifest_is_written_and_reloadable(tmp_path: Path):
    book_dir = _project(tmp_path)

    manifest = paginate(book_dir, read_order(book_dir))

    reloaded = Manifest.from_json((book_dir / MANIFEST_NAME).read_text("utf-8"))
    assert reloaded == manifest


def test_growing_a_chapter_is_caught_as_a_stale_manifest(tmp_path: Path):
    book_dir = _project(tmp_path)
    css = tmp_path / "assets" / "interior.css"
    manifest = paginate(book_dir, read_order(book_dir))

    _chapter(book_dir, 1, 4)  # the author added a page and forgot to re-paginate

    findings = verify(book_dir, manifest, css)

    assert has_errors(findings)
    assert any("stale" in f.message for f in findings)


def test_overstuffed_page_is_caught_as_clipping(tmp_path: Path):
    book_dir = _project(tmp_path)
    css = tmp_path / "assets" / "interior.css"
    path = book_dir / "chapter-02.html"
    path.write_text(
        path.read_text("utf-8").replace(
            "<p>Body copy for section 0.</p>", "<p>x</p>" * 400
        ),
        encoding="utf-8",
    )
    manifest = paginate(book_dir, read_order(book_dir))

    findings = verify(book_dir, manifest, css)

    assert has_errors(findings)
    assert any("clipped" in f.message for f in findings)
