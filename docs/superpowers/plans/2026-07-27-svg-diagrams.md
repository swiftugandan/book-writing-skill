# svg-diagrams Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship an `svg-diagrams` skill for authoring print-legible, token-driven SVG diagrams, plus a `bookkit` checker that mechanically enforces the grayscale rule `interior-design.md` already states.

**Architecture:** Diagrams are hand-authored inline SVG using `var(--token, fallback)` colours, so they inherit the book's palette when inline and degrade sensibly standalone. Checking splits into a browser-free static pass over SVG source and a browser-backed pass that reads computed styles and bounding boxes through the same Playwright Chromium that measures and prints pages. `bookkit.verify` calls the checker so the book pipeline covers diagrams with no extra command.

**Tech Stack:** Python 3.11+, Playwright (reusing `bookkit.measure.browser_page`), pytest.

## Global Constraints

- Skill lives at `skills/svg-diagrams/`. The checker lives in `skills/book-writing/scripts/bookkit/`.
- **1 SVG user unit = 1 point.** Every shipped example and the template obey this.
- Max diagram width is the text measure: `--page-w` minus twice `--margin` = **5.7in = 410.4pt** at the default trim.
- Every `<svg>` declares `width`, `height`, and `viewBox`. Dimensions in `in` or `pt`, **never `px`, never unitless**.
- Every `fill` and `stroke` is `var(--token, fallback)`, `none`, or `currentColor`. No literal hex, `rgb()`, or named colours.
- Thresholds: `MIN_FILL_CONTRAST = 1.5`, `MIN_TEXT_CONTRAST = 4.5`, `MIN_TYPE_PT = 6.0`.
- Font size is checked at **rendered** scale: `effective_pt = user_units × (rendered_width_pt / viewbox_width)`.
- Banned outright: `<image>`, `xlink:href`, remote URLs, `<linearGradient>`, `<radialGradient>`, `<filter>`, `feDropShadow`.
- A diagram may encode at most **three** categories by fill alone. A fourth needs a dash pattern, stroke weight, hatch, or label.
- Python invocation is always `.venv/bin/python` from `skills/book-writing/scripts`.

---

## File Structure

```
skills/svg-diagrams/
  SKILL.md                      router: when to draw, which archetype, how to verify
  references/
    grammar.md                  primitives, tokens, sizing, the three tonal levels
    archetypes.md               the six archetypes and when each fits
    verification.md             what the checker enforces and why each failure is silent
  assets/
    diagram.template.svg
    examples/
      flow.svg  pipeline.svg  cycle.svg
      layered-stack.svg  node-map.svg  annotated-anatomy.svg

skills/book-writing/scripts/bookkit/
  findings.py                   Finding + has_errors, extracted so imports stay acyclic
  diagrams.py                   colour maths, discovery, static + rendered checks, CLI
  verify.py                     MODIFIED: import from findings, call check_diagrams

skills/book-writing/scripts/tests/
  test_diagram_color.py         pure maths, no browser
  test_diagram_static.py        source-level checks, no browser
  test_diagram_rendered.py      browser-backed checks
  test_diagram_examples.py      every shipped example passes
  test_svg_skill_structure.py   SKILL.md and references
  test_verify.py                MODIFIED: diagram integration
```

**Responsibilities.** `findings.py` holds the shared result type and nothing else. `diagrams.py` splits internally into three layers that are tested separately: pure colour maths, `static_findings(source)` over raw SVG text, and `find_diagrams(path)` plus rendered checks that need a browser. `measure.py` remains the only module that launches Chromium.

---

### Task 1: Extract the shared Finding type

**Files:**
- Create: `skills/book-writing/scripts/bookkit/findings.py`
- Modify: `skills/book-writing/scripts/bookkit/verify.py`
- Test: `skills/book-writing/scripts/tests/test_findings.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `Finding` frozen dataclass with `level: str`, `file: str`, `message: str`; `has_errors(findings: Sequence[Finding]) -> bool`. Both re-exported from `bookkit.verify` so existing imports keep working.

**Why:** `verify.py` will import `check_diagrams` from `diagrams.py`, and `diagrams.py` needs `Finding`. Importing it from `verify` would be circular.

- [ ] **Step 1: Write the failing test**

Create `skills/book-writing/scripts/tests/test_findings.py`:

```python
from bookkit.findings import Finding, has_errors


def test_finding_carries_level_file_and_message():
    finding = Finding(level="error", file="a.html", message="broke")

    assert (finding.level, finding.file, finding.message) == ("error", "a.html", "broke")


def test_findings_are_frozen():
    import dataclasses
    import pytest

    finding = Finding(level="error", file="a.html", message="broke")
    with pytest.raises(dataclasses.FrozenInstanceError):
        finding.level = "warning"


def test_has_errors_is_false_for_warnings_only():
    assert not has_errors([Finding(level="warning", file="a.html", message="drift")])


def test_has_errors_is_true_when_any_error_present():
    findings = [
        Finding(level="warning", file="a.html", message="drift"),
        Finding(level="error", file="a.html", message="broke"),
    ]

    assert has_errors(findings)


def test_has_errors_is_false_for_an_empty_list():
    assert not has_errors([])


def test_verify_still_re_exports_the_shared_names():
    """Existing imports from bookkit.verify must keep working."""
    from bookkit.verify import Finding as VerifyFinding, has_errors as verify_has_errors

    assert VerifyFinding is Finding
    assert verify_has_errors is has_errors
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd skills/book-writing/scripts && .venv/bin/pytest tests/test_findings.py -q
```

Expected: FAIL, `ModuleNotFoundError: No module named 'bookkit.findings'`.

- [ ] **Step 3: Create the module**

Create `skills/book-writing/scripts/bookkit/findings.py`:

```python
"""The shared result type for every check in the pipeline.

Extracted so that `verify` can call into `diagrams` while `diagrams` still
reports its results with the same type, without a circular import.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class Finding:
    """One verification result. `level` is "error" or "warning"."""

    level: str
    file: str
    message: str


def has_errors(findings: Sequence[Finding]) -> bool:
    return any(finding.level == "error" for finding in findings)
```

- [ ] **Step 4: Point `verify.py` at it**

In `skills/book-writing/scripts/bookkit/verify.py`, delete the local `Finding` dataclass and the local `has_errors` function, then add to the imports:

```python
from bookkit.findings import Finding, has_errors
```

Keep `from dataclasses import dataclass` only if still used; if not, remove it. `Finding` and `has_errors` remain importable from `bookkit.verify` because the import binds them in that module's namespace.

- [ ] **Step 5: Run the whole suite**

```bash
cd skills/book-writing/scripts && .venv/bin/pytest -q
```

Expected: all pass, including the pre-existing `tests/test_verify.py`.

- [ ] **Step 6: Commit**

```bash
git add skills/book-writing/scripts/bookkit/findings.py \
        skills/book-writing/scripts/bookkit/verify.py \
        skills/book-writing/scripts/tests/test_findings.py
git commit -m "refactor(bookkit): extract the shared Finding type"
```

---

### Task 2: Colour maths

**Files:**
- Create: `skills/book-writing/scripts/bookkit/diagrams.py`
- Test: `skills/book-writing/scripts/tests/test_diagram_color.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `relative_luminance(rgb: tuple[int, int, int]) -> float` — WCAG relative luminance.
  - `contrast_ratio(a: tuple[int, int, int], b: tuple[int, int, int]) -> float`
  - `parse_color(value: str) -> tuple[int, int, int] | None` — `None` for `none`, `transparent`, and any `rgba(...)` with alpha 0.
  - `MIN_FILL_CONTRAST = 1.5`, `MIN_TEXT_CONTRAST = 4.5`, `MIN_TYPE_PT = 6.0`

- [ ] **Step 1: Write the failing test**

Create `skills/book-writing/scripts/tests/test_diagram_color.py`:

```python
import pytest

from bookkit.diagrams import (
    MIN_FILL_CONTRAST,
    contrast_ratio,
    parse_color,
    relative_luminance,
)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# The interior's own tokens, as defined in assets/interior.css.
INK = (0x24, 0x24, 0x24)
PAPER = (0xFF, 0xFF, 0xFF)
ACCENT = (0xD5, 0x4B, 0x20)
SUPPORT = (0x17, 0x7C, 0x83)
CAUTION = (0x9A, 0x5A, 0x12)
MUTED = (0x68, 0x68, 0x68)


def test_luminance_of_black_is_zero():
    assert relative_luminance(BLACK) == pytest.approx(0.0)


def test_luminance_of_white_is_one():
    assert relative_luminance(WHITE) == pytest.approx(1.0)


def test_luminance_of_mid_grey_matches_wcag():
    # #808080 is the canonical WCAG worked example.
    assert relative_luminance((0x80, 0x80, 0x80)) == pytest.approx(0.2159, abs=1e-4)


def test_contrast_of_black_on_white_is_twenty_one():
    assert contrast_ratio(BLACK, WHITE) == pytest.approx(21.0, abs=1e-2)


def test_contrast_is_symmetric():
    assert contrast_ratio(ACCENT, SUPPORT) == pytest.approx(contrast_ratio(SUPPORT, ACCENT))


def test_contrast_of_a_colour_with_itself_is_one():
    assert contrast_ratio(ACCENT, ACCENT) == pytest.approx(1.0)


def test_ink_on_paper_is_strong():
    assert contrast_ratio(INK, PAPER) == pytest.approx(15.52, abs=0.05)


def test_accent_and_support_collapse_in_grayscale():
    """The motivating case. Obviously different in colour, the same grey in print."""
    assert contrast_ratio(ACCENT, SUPPORT) == pytest.approx(1.14, abs=0.02)
    assert contrast_ratio(ACCENT, SUPPORT) < MIN_FILL_CONTRAST


def test_every_mid_tone_pair_collapses():
    """The palette offers three tonal levels, not seven colours."""
    mid_tones = [ACCENT, SUPPORT, CAUTION, MUTED]

    for i, a in enumerate(mid_tones):
        for b in mid_tones[i + 1 :]:
            assert contrast_ratio(a, b) < MIN_FILL_CONTRAST


def test_mid_tones_are_distinguishable_from_ink_and_paper():
    for mid in (ACCENT, SUPPORT, CAUTION, MUTED):
        assert contrast_ratio(mid, INK) >= MIN_FILL_CONTRAST
        assert contrast_ratio(mid, PAPER) >= MIN_FILL_CONTRAST


def test_parse_color_reads_the_browser_rgb_form():
    assert parse_color("rgb(213, 75, 32)") == ACCENT


def test_parse_color_reads_rgba_with_alpha():
    assert parse_color("rgba(213, 75, 32, 0.5)") == ACCENT


def test_parse_color_reads_hex():
    assert parse_color("#d54b20") == ACCENT
    assert parse_color("#FFF") == WHITE


def test_parse_color_returns_none_for_absent_paint():
    assert parse_color("none") is None
    assert parse_color("transparent") is None
    assert parse_color("rgba(0, 0, 0, 0)") is None
    assert parse_color("") is None
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd skills/book-writing/scripts && .venv/bin/pytest tests/test_diagram_color.py -q
```

Expected: FAIL, `ModuleNotFoundError: No module named 'bookkit.diagrams'`.

- [ ] **Step 3: Write the implementation**

Create `skills/book-writing/scripts/bookkit/diagrams.py`:

```python
"""Check that SVG diagrams survive print.

`interior-design.md` requires diagrams to read in greyscale and never carry
meaning in colour alone. Nothing enforced it, and the interior's own palette
makes the gap concrete: `--accent` and `--support` differ obviously on screen
and sit at a greyscale contrast of 1.14:1, which is the same grey on paper.
"""

from __future__ import annotations

import re

MIN_FILL_CONTRAST = 1.5
MIN_TEXT_CONTRAST = 4.5
MIN_TYPE_PT = 6.0

_RGB = re.compile(r"rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)\s*(?:[,/]\s*([\d.]+)\s*)?\)")
_HEX = re.compile(r"^#(?:([0-9a-fA-F]{3})|([0-9a-fA-F]{6}))$")

_ABSENT = {"", "none", "transparent", "currentcolor"}


def parse_color(value: str) -> tuple[int, int, int] | None:
    """Read a CSS colour into 8-bit RGB. `None` means no paint is applied."""
    text = (value or "").strip()
    if text.lower() in _ABSENT:
        return None

    match = _RGB.match(text)
    if match:
        if match.group(4) is not None and float(match.group(4)) == 0:
            return None
        return tuple(int(round(float(match.group(i)))) for i in (1, 2, 3))  # type: ignore[return-value]

    match = _HEX.match(text)
    if match:
        short, full = match.groups()
        digits = "".join(c * 2 for c in short) if short else full
        return tuple(int(digits[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]

    return None


def _linearise(channel: int) -> float:
    c = channel / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    """WCAG relative luminance, which is what greyscale conversion preserves."""
    r, g, b = (_linearise(channel) for channel in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    """WCAG contrast ratio, from 1.0 (identical) to 21.0 (black on white)."""
    la, lb = relative_luminance(a), relative_luminance(b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd skills/book-writing/scripts && .venv/bin/pytest tests/test_diagram_color.py -q
```

Expected: 14 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/book-writing/scripts/bookkit/diagrams.py \
        skills/book-writing/scripts/tests/test_diagram_color.py
git commit -m "feat(bookkit): add WCAG luminance and contrast maths for diagrams"
```

---

### Task 3: Static source checks

**Files:**
- Modify: `skills/book-writing/scripts/bookkit/diagrams.py`
- Test: `skills/book-writing/scripts/tests/test_diagram_static.py`

**Interfaces:**
- Consumes: `Finding` (Task 1).
- Produces: `static_findings(source: str, file: str, index: int) -> list[Finding]`, checking hardcoded colour, external and raster references, gradients and filters, and missing or `px` dimensions. No browser.

- [ ] **Step 1: Write the failing test**

Create `skills/book-writing/scripts/tests/test_diagram_static.py`:

```python
from bookkit.diagrams import static_findings

CLEAN = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="5.7in" height="1in" '
    'viewBox="0 0 410.4 72">'
    '<rect x="0" y="0" width="80" height="40" fill="var(--paper, #ffffff)" '
    'stroke="var(--ink, #242424)"/>'
    '<text x="4" y="20" font-size="8" fill="var(--ink, #242424)">Step</text>'
    "</svg>"
)


def _messages(source: str) -> str:
    return " ".join(f.message for f in static_findings(source, "d.svg", 0))


def test_clean_diagram_produces_no_findings():
    assert static_findings(CLEAN, "d.svg", 0) == []


def test_every_finding_carries_the_file_and_diagram_index():
    bad = CLEAN.replace('fill="var(--paper, #ffffff)"', 'fill="#ff0000"')

    finding = static_findings(bad, "chapter-01.html", 2)[0]

    assert finding.file == "chapter-01.html"
    assert "diagram 3" in finding.message
    assert finding.level == "error"


def test_hardcoded_hex_fill_is_rejected():
    bad = CLEAN.replace('fill="var(--paper, #ffffff)"', 'fill="#ff0000"')

    assert "hardcoded" in _messages(bad)


def test_hardcoded_named_colour_is_rejected():
    bad = CLEAN.replace('stroke="var(--ink, #242424)"', 'stroke="black"')

    assert "hardcoded" in _messages(bad)


def test_hardcoded_rgb_function_is_rejected():
    bad = CLEAN.replace('fill="var(--paper, #ffffff)"', 'fill="rgb(1,2,3)"')

    assert "hardcoded" in _messages(bad)


def test_none_and_currentcolor_are_allowed():
    ok = CLEAN.replace('fill="var(--paper, #ffffff)"', 'fill="none"')
    ok = ok.replace('stroke="var(--ink, #242424)"', 'stroke="currentColor"')

    assert static_findings(ok, "d.svg", 0) == []


def test_fallback_hex_inside_a_var_is_allowed():
    """`var(--ink, #242424)` is the required form, not a hardcoded colour."""
    assert static_findings(CLEAN, "d.svg", 0) == []


def test_raster_image_element_is_rejected():
    bad = CLEAN.replace("</svg>", '<image href="photo.png"/></svg>')

    assert "raster" in _messages(bad) or "external" in _messages(bad)


def test_remote_url_is_rejected():
    bad = CLEAN.replace("</svg>", '<use href="https://example.com/a.svg#x"/></svg>')

    assert "external" in _messages(bad)


def test_gradient_is_rejected():
    bad = CLEAN.replace("</svg>", '<defs><linearGradient id="g"/></defs></svg>')

    assert "gradient" in _messages(bad)


def test_filter_and_drop_shadow_are_rejected():
    bad = CLEAN.replace("</svg>", '<filter id="f"><feDropShadow/></filter></svg>')

    assert "filter" in _messages(bad) or "shadow" in _messages(bad)


def test_missing_viewbox_is_rejected():
    bad = CLEAN.replace(' viewBox="0 0 410.4 72"', "")

    assert "viewBox" in _messages(bad)


def test_missing_width_is_rejected():
    bad = CLEAN.replace(' width="5.7in"', "")

    assert "width" in _messages(bad)


def test_pixel_dimensions_are_rejected():
    bad = CLEAN.replace('width="5.7in"', 'width="540px"')

    assert "px" in _messages(bad)


def test_unitless_dimensions_are_rejected():
    bad = CLEAN.replace('width="5.7in"', 'width="540"')

    assert "unit" in _messages(bad)
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd skills/book-writing/scripts && .venv/bin/pytest tests/test_diagram_static.py -q
```

Expected: FAIL, `ImportError: cannot import name 'static_findings'`.

- [ ] **Step 3: Write the implementation**

Append to `skills/book-writing/scripts/bookkit/diagrams.py`:

```python
from bookkit.findings import Finding

_SVG_TAG = re.compile(r"<svg\b[^>]*>", re.IGNORECASE | re.DOTALL)
_PAINT_ATTR = re.compile(r'\b(fill|stroke)\s*=\s*"([^"]*)"', re.IGNORECASE)
_DIMENSION = re.compile(r'\b(width|height)\s*=\s*"([^"]*)"', re.IGNORECASE)
_VIEWBOX = re.compile(r'\bviewBox\s*=\s*"([^"]*)"', re.IGNORECASE)
_ALLOWED_UNITS = ("in", "pt", "mm", "cm")


def _error(file: str, index: int, message: str) -> Finding:
    return Finding(level="error", file=file, message=f"diagram {index + 1}: {message}")


def static_findings(source: str, file: str, index: int) -> list[Finding]:
    """Checks that read the SVG source directly, with no browser."""
    findings: list[Finding] = []

    for attribute, value in _PAINT_ATTR.findall(source):
        text = value.strip()
        if text.lower() in _ABSENT or text.startswith("var("):
            continue
        findings.append(
            _error(
                file,
                index,
                f'hardcoded colour in {attribute}="{text}"; '
                "use var(--token, fallback) so the diagram retargets with the book",
            )
        )

    if re.search(r"<image\b", source, re.IGNORECASE):
        findings.append(
            _error(file, index, "raster <image> element; the PDF will show a missing graphic")
        )
    if re.search(r'\bxlink:href\s*=|href\s*=\s*"(?:https?:)?//', source, re.IGNORECASE):
        findings.append(
            _error(file, index, "external reference; the PDF will show a missing graphic")
        )
    if re.search(r"<(?:linear|radial)Gradient\b", source, re.IGNORECASE):
        findings.append(_error(file, index, "gradient; banned by the layout discipline"))
    if re.search(r"<filter\b|feDropShadow", source, re.IGNORECASE):
        findings.append(
            _error(file, index, "filter or drop shadow; banned by the layout discipline")
        )

    opening = _SVG_TAG.search(source)
    tag = opening.group(0) if opening else ""

    if not _VIEWBOX.search(tag):
        findings.append(_error(file, index, "no viewBox; the diagram cannot scale predictably"))

    dimensions = dict(
        (name.lower(), value.strip()) for name, value in _DIMENSION.findall(tag)
    )
    for name in ("width", "height"):
        value = dimensions.get(name)
        if value is None:
            findings.append(_error(file, index, f"no {name} on the <svg> element"))
            continue
        if value.endswith("px"):
            findings.append(
                _error(file, index, f'{name}="{value}" is in px; a page is a physical object')
            )
        elif not value.endswith(_ALLOWED_UNITS):
            findings.append(
                _error(
                    file,
                    index,
                    f'{name}="{value}" has no unit; use in or pt',
                )
            )

    return findings
```

Note: `_DIMENSION` is applied to the opening `<svg>` tag only, so `width` on a child `<rect>` never trips the dimension rules.

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd skills/book-writing/scripts && .venv/bin/pytest tests/test_diagram_static.py -q
```

Expected: 15 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/book-writing/scripts/bookkit/diagrams.py \
        skills/book-writing/scripts/tests/test_diagram_static.py
git commit -m "feat(bookkit): add source-level diagram checks"
```

---

### Task 4: Discovery and rendered checks

**Files:**
- Modify: `skills/book-writing/scripts/bookkit/diagrams.py`
- Test: `skills/book-writing/scripts/tests/test_diagram_rendered.py`

**Interfaces:**
- Consumes: `browser_page` (`bookkit.measure`), `Finding` (Task 1), colour maths (Task 2).
- Produces:
  - `DiagramShape` frozen dataclass: `tag: str`, `fill: str`, `stroke: str`, `dash: str`, `stroke_width: float`, `x/y/width/height: float` (user units).
  - `DiagramText` frozen dataclass: `content: str`, `fill: str`, `size_pt: float` (rendered), `x/y/width/height: float`.
  - `Diagram` frozen dataclass: `file: str`, `index: int`, `viewbox: tuple[float, float, float, float]`, `scale_pt_per_unit: float`, `paper: str`, `shapes: tuple[DiagramShape, ...]`, `texts: tuple[DiagramText, ...]`, `source: str`.
  - `find_diagrams(path: Path) -> list[Diagram]`
  - `rendered_findings(diagram: Diagram) -> list[Finding]`

- [ ] **Step 1: Write the failing test**

Create `skills/book-writing/scripts/tests/test_diagram_rendered.py`:

```python
from pathlib import Path

from bookkit.diagrams import find_diagrams, rendered_findings

HOST = """<!doctype html><html><head><meta charset="utf-8"><style>
:root {{ --ink: #242424; --paper: #ffffff; --accent: #d54b20; --support: #177c83; }}
</style></head><body>{body}</body></html>"""

SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="288pt" height="72pt"
     viewBox="0 0 288 72">{content}</svg>"""


def _write(tmp_path: Path, content: str, name: str = "page.html") -> Path:
    path = tmp_path / name
    path.write_text(HOST.format(body=SVG.format(content=content)), encoding="utf-8")
    return path


def _messages(path: Path) -> str:
    return " ".join(
        f.message for d in find_diagrams(path) for f in rendered_findings(d)
    )


CLEAN = (
    '<rect x="10" y="10" width="100" height="40" fill="var(--paper, #fff)" '
    'stroke="var(--ink, #242424)"/>'
    '<text x="16" y="34" font-size="9" fill="var(--ink, #242424)">Reviewed</text>'
)


def test_finds_one_diagram_per_svg_element(tmp_path: Path):
    path = tmp_path / "page.html"
    path.write_text(
        HOST.format(body=SVG.format(content=CLEAN) + SVG.format(content=CLEAN)),
        encoding="utf-8",
    )

    diagrams = find_diagrams(path)

    assert [d.index for d in diagrams] == [0, 1]
    assert all(d.file == "page.html" for d in diagrams)


def test_reads_the_viewbox_and_unit_scale(tmp_path: Path):
    diagram = find_diagrams(_write(tmp_path, CLEAN))[0]

    assert diagram.viewbox == (0.0, 0.0, 288.0, 72.0)
    # 288pt wide over 288 user units: one unit is one point.
    assert round(diagram.scale_pt_per_unit, 3) == 1.0


def test_resolves_tokens_to_the_pages_computed_colours(tmp_path: Path):
    diagram = find_diagrams(_write(tmp_path, CLEAN))[0]

    assert diagram.shapes[0].stroke == "rgb(36, 36, 36)"


def test_clean_diagram_produces_no_rendered_findings(tmp_path: Path):
    assert _messages(_write(tmp_path, CLEAN)) == ""


def test_text_below_the_print_floor_is_rejected(tmp_path: Path):
    small = CLEAN.replace('font-size="9"', 'font-size="4"')

    assert "6pt" in _messages(_write(tmp_path, small))


def test_type_size_is_judged_after_viewbox_scaling(tmp_path: Path):
    """font-size 10 in a viewBox scaled by 0.5 renders at 5pt, under the floor."""
    path = tmp_path / "page.html"
    scaled = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="144pt" height="36pt" '
        'viewBox="0 0 288 72">'
        '<rect x="10" y="10" width="100" height="40" fill="var(--paper, #fff)"/>'
        '<text x="16" y="34" font-size="10" fill="var(--ink, #242424)">Reviewed</text>'
        "</svg>"
    )
    path.write_text(HOST.format(body=scaled), encoding="utf-8")

    diagram = find_diagrams(path)[0]

    assert round(diagram.scale_pt_per_unit, 3) == 0.5
    assert "6pt" in " ".join(f.message for f in rendered_findings(diagram))


def test_low_contrast_text_is_rejected(tmp_path: Path):
    faint = CLEAN.replace(
        '<text x="16" y="34" font-size="9" fill="var(--ink, #242424)">',
        '<text x="16" y="34" font-size="9" fill="var(--paper, #ffffff)">',
    )

    assert "contrast" in _messages(_write(tmp_path, faint))


def test_two_mid_tone_fills_without_a_differentiator_are_rejected(tmp_path: Path):
    """accent against support is 1.14:1 in greyscale."""
    pair = (
        '<rect x="10" y="10" width="60" height="40" fill="var(--accent, #d54b20)"/>'
        '<rect x="90" y="10" width="60" height="40" fill="var(--support, #177c83)"/>'
    )

    message = _messages(_write(tmp_path, pair))

    assert "greyscale" in message or "grayscale" in message


def test_a_dash_pattern_rescues_a_low_contrast_pair(tmp_path: Path):
    """Colour alone is not enough; colour plus another channel is."""
    pair = (
        '<rect x="10" y="10" width="60" height="40" fill="var(--accent, #d54b20)" '
        'stroke="var(--ink, #242424)"/>'
        '<rect x="90" y="10" width="60" height="40" fill="var(--support, #177c83)" '
        'stroke="var(--ink, #242424)" stroke-dasharray="4 2"/>'
    )

    assert _messages(_write(tmp_path, pair)) == ""


def test_content_outside_the_viewbox_is_rejected(tmp_path: Path):
    overflowing = CLEAN + '<rect x="260" y="10" width="200" height="40" fill="none" stroke="var(--ink, #242424)"/>'

    assert "viewBox" in _messages(_write(tmp_path, overflowing))


def test_reads_a_standalone_svg_file(tmp_path: Path):
    path = tmp_path / "diagram.svg"
    path.write_text(SVG.format(content=CLEAN), encoding="utf-8")

    diagrams = find_diagrams(path)

    assert len(diagrams) == 1
    assert diagrams[0].file == "diagram.svg"
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd skills/book-writing/scripts && .venv/bin/pytest tests/test_diagram_rendered.py -q
```

Expected: FAIL, `ImportError: cannot import name 'find_diagrams'`.

- [ ] **Step 3: Write the implementation**

Append to `skills/book-writing/scripts/bookkit/diagrams.py`:

```python
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

from bookkit.measure import browser_page

_SHAPE_TAGS = ("rect", "circle", "ellipse", "polygon", "path")

_COLLECT_JS = """
() => {
  const paper = getComputedStyle(document.documentElement)
    .getPropertyValue('--paper').trim() || 'rgb(255, 255, 255)';
  const svgs = document.querySelectorAll('svg');
  return Array.from(svgs).map((svg, index) => {
    const box = svg.viewBox.baseVal;
    const rendered = svg.getBoundingClientRect();
    const viewbox = [box.x, box.y, box.width, box.height];
    // Rendered width is CSS px; 0.75 converts to points.
    const scale = box.width ? (rendered.width * 0.75) / box.width : 1;

    const geometry = (el) => {
      let b;
      try { b = el.getBBox(); } catch (e) { b = {x: 0, y: 0, width: 0, height: 0}; }
      return {x: b.x, y: b.y, width: b.width, height: b.height};
    };

    const shapes = Array.from(svg.querySelectorAll('rect,circle,ellipse,polygon,path'))
      .filter((el) => !el.closest('marker,defs'))
      .map((el) => {
        const s = getComputedStyle(el);
        return Object.assign({
          tag: el.tagName.toLowerCase(),
          fill: s.fill,
          stroke: s.stroke,
          dash: s.strokeDasharray === 'none' ? '' : s.strokeDasharray,
          stroke_width: parseFloat(s.strokeWidth) || 0,
        }, geometry(el));
      });

    const texts = Array.from(svg.querySelectorAll('text')).map((el) => {
      const s = getComputedStyle(el);
      return Object.assign({
        content: (el.textContent || '').trim(),
        fill: s.fill,
        // font-size computes to CSS px in user-unit space; scale to rendered points.
        size_pt: parseFloat(s.fontSize) * scale,
      }, geometry(el));
    });

    return {index, viewbox, scale, paper, shapes, texts, source: svg.outerHTML};
  });
}
"""


@dataclass(frozen=True)
class DiagramShape:
    tag: str
    fill: str
    stroke: str
    dash: str
    stroke_width: float
    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True)
class DiagramText:
    content: str
    fill: str
    size_pt: float
    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True)
class Diagram:
    file: str
    index: int
    viewbox: tuple[float, float, float, float]
    scale_pt_per_unit: float
    paper: str
    shapes: tuple[DiagramShape, ...]
    texts: tuple[DiagramText, ...]
    source: str


def find_diagrams(path: Path) -> list[Diagram]:
    """Every inline <svg> in an HTML file, or the root of an .svg file."""
    with browser_page() as page:
        page.goto(path.resolve().as_uri(), wait_until="load")
        raw = page.evaluate(_COLLECT_JS)

    return [
        Diagram(
            file=path.name,
            index=item["index"],
            viewbox=tuple(item["viewbox"]),  # type: ignore[arg-type]
            scale_pt_per_unit=item["scale"],
            paper=item["paper"],
            shapes=tuple(DiagramShape(**shape) for shape in item["shapes"]),
            texts=tuple(DiagramText(**text) for text in item["texts"]),
            source=item["source"],
        )
        for item in raw
    ]


def _background_for(diagram: Diagram, text: DiagramText) -> str:
    """The fill of the smallest shape whose box contains the text, else paper."""
    containing = [
        shape
        for shape in diagram.shapes
        if parse_color(shape.fill)
        and shape.x <= text.x
        and shape.y <= text.y
        and shape.x + shape.width >= text.x + text.width
        and shape.y + shape.height >= text.y + text.height
    ]
    if not containing:
        return diagram.paper
    return min(containing, key=lambda s: s.width * s.height).fill


def rendered_findings(diagram: Diagram) -> list[Finding]:
    """Checks that need computed styles and real geometry."""
    findings: list[Finding] = []
    file, index = diagram.file, diagram.index

    for text in diagram.texts:
        if text.size_pt < MIN_TYPE_PT:
            findings.append(
                _error(
                    file,
                    index,
                    f'text "{text.content[:24]}" renders at {text.size_pt:.1f}pt, '
                    f"below the {MIN_TYPE_PT:.0f}pt print floor",
                )
            )
        ink = parse_color(text.fill)
        paper = parse_color(_background_for(diagram, text))
        if ink and paper:
            ratio = contrast_ratio(ink, paper)
            if ratio < MIN_TEXT_CONTRAST:
                findings.append(
                    _error(
                        file,
                        index,
                        f'text "{text.content[:24]}" has {ratio:.2f}:1 contrast against '
                        f"its background, below {MIN_TEXT_CONTRAST}:1",
                    )
                )

    painted = [shape for shape in diagram.shapes if parse_color(shape.fill)]
    by_fill: dict[str, list[DiagramShape]] = {}
    for shape in painted:
        by_fill.setdefault(shape.fill, []).append(shape)

    for left, right in combinations(sorted(by_fill), 2):
        a, b = parse_color(left), parse_color(right)
        if not a or not b:
            continue
        ratio = contrast_ratio(a, b)
        if ratio >= MIN_FILL_CONTRAST:
            continue
        if _differentiated(by_fill[left], by_fill[right]):
            continue
        findings.append(
            _error(
                file,
                index,
                f"fills {left} and {right} are {ratio:.2f}:1 apart in greyscale, "
                f"below {MIN_FILL_CONTRAST}:1, and are not separated by a dash "
                "pattern or stroke weight; colour alone is not enough",
            )
        )

    x, y, width, height = diagram.viewbox
    for shape in diagram.shapes:
        if (
            shape.width
            and shape.height
            and (
                shape.x < x - 0.5
                or shape.y < y - 0.5
                or shape.x + shape.width > x + width + 0.5
                or shape.y + shape.height > y + height + 0.5
            )
        ):
            findings.append(
                _error(
                    file,
                    index,
                    f"a <{shape.tag}> extends past the viewBox and will be cropped",
                )
            )
            break

    return findings


def _differentiated(left: list[DiagramShape], right: list[DiagramShape]) -> bool:
    """True when two fill groups differ by a channel other than colour."""
    dashes_left = {shape.dash for shape in left}
    dashes_right = {shape.dash for shape in right}
    if dashes_left != dashes_right:
        return True
    widths_left = {round(shape.stroke_width, 2) for shape in left}
    widths_right = {round(shape.stroke_width, 2) for shape in right}
    return widths_left != widths_right
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd skills/book-writing/scripts && .venv/bin/pytest tests/test_diagram_rendered.py -q
```

Expected: 11 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/book-writing/scripts/bookkit/diagrams.py \
        skills/book-writing/scripts/tests/test_diagram_rendered.py
git commit -m "feat(bookkit): add rendered diagram checks for type, contrast, and overflow"
```

---

### Task 5: Compose the checker and wire it into verify

**Files:**
- Modify: `skills/book-writing/scripts/bookkit/diagrams.py`
- Modify: `skills/book-writing/scripts/bookkit/verify.py`
- Test: `skills/book-writing/scripts/tests/test_diagram_cli.py`
- Test: `skills/book-writing/scripts/tests/test_verify.py` (append)

**Interfaces:**
- Consumes: `static_findings`, `find_diagrams`, `rendered_findings` (Tasks 3–4); `Manifest` and `verify` (existing).
- Produces: `check_diagrams(paths: Sequence[Path]) -> list[Finding]`; CLI `python -m bookkit.diagrams <path>` accepting a book directory, an HTML file, or an SVG file, exiting 1 on any error. `bookkit.verify` calls `check_diagrams` over the manifest's page files.

- [ ] **Step 1: Write the failing test**

Create `skills/book-writing/scripts/tests/test_diagram_cli.py`:

```python
from pathlib import Path

from bookkit.diagrams import check_diagrams, main
from bookkit.findings import has_errors

HOST = """<!doctype html><html><head><meta charset="utf-8"><style>
:root {{ --ink: #242424; --paper: #ffffff; }}
</style></head><body>{body}</body></html>"""

GOOD = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="288pt" height="72pt" viewBox="0 0 288 72">'
    '<rect x="10" y="10" width="100" height="40" fill="var(--paper, #fff)" '
    'stroke="var(--ink, #242424)"/>'
    '<text x="16" y="34" font-size="9" fill="var(--ink, #242424)">Reviewed</text>'
    "</svg>"
)
BAD = GOOD.replace('fill="var(--paper, #fff)"', 'fill="#ff0000"')


def _page(tmp_path: Path, svg: str, name: str = "page.html") -> Path:
    path = tmp_path / name
    path.write_text(HOST.format(body=svg), encoding="utf-8")
    return path


def test_clean_page_produces_no_findings(tmp_path: Path):
    assert check_diagrams([_page(tmp_path, GOOD)]) == []


def test_static_and_rendered_findings_are_combined(tmp_path: Path):
    small = BAD.replace('font-size="9"', 'font-size="3"')

    findings = check_diagrams([_page(tmp_path, small)])

    joined = " ".join(f.message for f in findings)
    assert "hardcoded" in joined
    assert "print floor" in joined


def test_a_page_with_no_diagrams_is_fine(tmp_path: Path):
    path = tmp_path / "page.html"
    path.write_text(HOST.format(body="<p>no diagrams here</p>"), encoding="utf-8")

    assert check_diagrams([path]) == []


def test_checks_a_standalone_svg_file(tmp_path: Path):
    path = tmp_path / "diagram.svg"
    path.write_text(BAD, encoding="utf-8")

    assert has_errors(check_diagrams([path]))


def test_cli_exits_zero_on_a_clean_file(tmp_path: Path, capsys):
    path = _page(tmp_path, GOOD)

    assert main([str(path)]) == 0


def test_cli_exits_one_and_names_the_problem(tmp_path: Path, capsys):
    path = _page(tmp_path, BAD)

    assert main([str(path)]) == 1
    assert "hardcoded" in capsys.readouterr().out


def test_cli_accepts_a_directory(tmp_path: Path):
    book = tmp_path / "book"
    book.mkdir()
    _page(book, GOOD, "chapter-01.html")
    _page(book, BAD, "chapter-02.html")

    assert main([str(book)]) == 1
```

Append to `skills/book-writing/scripts/tests/test_verify.py`:

```python


def test_verify_rejects_a_page_whose_diagram_breaks_the_rules(book_dir: Path):
    """The book pipeline covers diagrams with no extra command."""
    bad_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="288pt" height="72pt" '
        'viewBox="0 0 288 72">'
        '<rect x="10" y="10" width="100" height="40" fill="#ff0000"/>'
        "</svg>"
    )
    write_book(book_dir, "a.html", [f"<p>a</p>{bad_svg}"])
    manifest = assign_folios([("a.html", 1)])

    findings = verify(book_dir, manifest, _css(book_dir))

    assert has_errors(findings)
    assert any("hardcoded" in f.message for f in findings)


def test_verify_accepts_a_page_with_a_clean_diagram(book_dir: Path):
    good_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="288pt" height="72pt" '
        'viewBox="0 0 288 72">'
        '<rect x="10" y="10" width="100" height="40" fill="var(--paper, #ffffff)" '
        'stroke="var(--ink, #242424)"/>'
        '<text x="16" y="34" font-size="9" fill="var(--ink, #242424)">Step</text>'
        "</svg>"
    )
    write_book(book_dir, "a.html", [f"<p>a</p>{good_svg}"])
    manifest = assign_folios([("a.html", 1)])

    assert verify(book_dir, manifest, _css(book_dir)) == []
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd skills/book-writing/scripts && .venv/bin/pytest tests/test_diagram_cli.py -q
```

Expected: FAIL, `ImportError: cannot import name 'check_diagrams'`.

- [ ] **Step 3: Add the composer and CLI**

Append to `skills/book-writing/scripts/bookkit/diagrams.py`:

```python
import argparse
import sys
from typing import Sequence

from bookkit.findings import has_errors

_SCANNABLE = (".html", ".svg")


def check_diagrams(paths: Sequence[Path]) -> list[Finding]:
    """Run every diagram check over the given HTML or SVG files."""
    findings: list[Finding] = []
    for path in paths:
        for diagram in find_diagrams(path):
            findings.extend(static_findings(diagram.source, diagram.file, diagram.index))
            findings.extend(rendered_findings(diagram))
    return findings


def _expand(target: Path) -> list[Path]:
    if target.is_dir():
        return sorted(p for p in target.iterdir() if p.suffix.lower() in _SCANNABLE)
    return [target]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check SVG diagrams for print.")
    parser.add_argument("target", type=Path, help="a book directory, an HTML file, or an SVG file")
    args = parser.parse_args(argv)

    paths = _expand(args.target)
    findings = check_diagrams(paths)
    for finding in findings:
        print(f"{finding.level.upper():<7} {finding.file}: {finding.message}")

    if has_errors(findings):
        print(f"\nFAILED: {sum(f.level == 'error' for f in findings)} error(s)")
        return 1
    print(f"OK: diagrams in {len(paths)} file(s) verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Move the `import argparse`, `import sys`, and `from typing import Sequence` lines to the top of the module with the other imports rather than leaving them mid-file.

- [ ] **Step 4: Call it from verify**

In `skills/book-writing/scripts/bookkit/verify.py`, add the import:

```python
from bookkit.diagrams import check_diagrams
```

and inside `verify()`, immediately before the `return findings` line:

```python
    findings.extend(check_diagrams(paths))
```

- [ ] **Step 5: Run the whole suite**

```bash
cd skills/book-writing/scripts && .venv/bin/pytest -q
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add skills/book-writing/scripts/bookkit/diagrams.py \
        skills/book-writing/scripts/bookkit/verify.py \
        skills/book-writing/scripts/tests/test_diagram_cli.py \
        skills/book-writing/scripts/tests/test_verify.py
git commit -m "feat(bookkit): compose the diagram checker and fold it into verify"
```

---

### Task 6: The template and the first three examples

**Files:**
- Create: `skills/svg-diagrams/assets/diagram.template.svg`
- Create: `skills/svg-diagrams/assets/examples/flow.svg`
- Create: `skills/svg-diagrams/assets/examples/pipeline.svg`
- Create: `skills/svg-diagrams/assets/examples/cycle.svg`
- Test: `skills/book-writing/scripts/tests/test_diagram_examples.py`

**Interfaces:**
- Consumes: `check_diagrams` (Task 5).
- Produces: four SVG assets. Every one must pass the checker, which is the acceptance criterion.

- [ ] **Step 1: Write the failing test**

Create `skills/book-writing/scripts/tests/test_diagram_examples.py`:

```python
from pathlib import Path

import pytest

from bookkit.diagrams import check_diagrams

SVG_SKILL = Path(__file__).resolve().parents[3] / "svg-diagrams"
ASSETS = SVG_SKILL / "assets"
EXAMPLES = ASSETS / "examples"

EXPECTED = [
    "flow.svg",
    "pipeline.svg",
    "cycle.svg",
    "layered-stack.svg",
    "node-map.svg",
    "annotated-anatomy.svg",
]


def test_template_exists():
    assert (ASSETS / "diagram.template.svg").exists()


@pytest.mark.parametrize("name", EXPECTED)
def test_example_exists(name: str):
    assert (EXAMPLES / name).exists()


def test_template_passes_the_checker():
    assert check_diagrams([ASSETS / "diagram.template.svg"]) == []


@pytest.mark.parametrize("name", EXPECTED)
def test_example_passes_the_checker(name: str):
    findings = check_diagrams([EXAMPLES / name])

    assert findings == [], "\n".join(f.message for f in findings)


@pytest.mark.parametrize("name", EXPECTED)
def test_example_uses_one_unit_per_point(name: str):
    """The grammar mandates it so authors never reason about scaling."""
    from bookkit.diagrams import find_diagrams

    diagram = find_diagrams(EXAMPLES / name)[0]

    assert round(diagram.scale_pt_per_unit, 3) == 1.0


@pytest.mark.parametrize("name", EXPECTED)
def test_example_fits_the_text_measure(name: str):
    """410.4pt is --page-w minus twice --margin at the default trim."""
    from bookkit.diagrams import find_diagrams

    diagram = find_diagrams(EXAMPLES / name)[0]

    assert diagram.viewbox[2] <= 410.4
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd skills/book-writing/scripts && .venv/bin/pytest tests/test_diagram_examples.py -q
```

Expected: FAIL, the asset files do not exist.

- [ ] **Step 3: Write the template**

Create `skills/svg-diagrams/assets/diagram.template.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="410.4pt" height="90pt"
     viewBox="0 0 410.4 90" role="img"
     aria-label="Describe the diagram for a reader who cannot see it">
  <!-- One user unit is one point. Width 410.4 is the text measure at the
       default 7x10in trim: --page-w minus twice --margin.
       Every colour is var(--token, fallback) so the diagram retargets with
       the book when inline and still renders standalone. -->
  <defs>
    <marker id="tpl-arrow" viewBox="0 0 10 10" refX="9" refY="5"
            markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--ink, #242424)"/>
    </marker>
  </defs>

  <rect x="0.5" y="20.5" width="120" height="48" rx="2"
        fill="var(--paper, #ffffff)" stroke="var(--ink, #242424)" stroke-width="1"/>
  <text x="60.5" y="48" text-anchor="middle" font-size="9"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">Replace me</text>

  <line x1="124" y1="44.5" x2="168" y2="44.5"
        stroke="var(--ink, #242424)" stroke-width="1" marker-end="url(#tpl-arrow)"/>

  <rect x="172.5" y="20.5" width="120" height="48" rx="2"
        fill="var(--pale, #f1f1f1)" stroke="var(--ink, #242424)" stroke-width="1"/>
  <text x="232.5" y="48" text-anchor="middle" font-size="9"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">And me</text>
</svg>
```

- [ ] **Step 4: Write `flow.svg`**

Create `skills/svg-diagrams/assets/examples/flow.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="410.4pt" height="86pt"
     viewBox="0 0 410.4 86" role="img"
     aria-label="Four steps in sequence, with the third branching to a rejection">
  <defs>
    <marker id="flow-arrow" viewBox="0 0 10 10" refX="9" refY="5"
            markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--ink, #242424)"/>
    </marker>
  </defs>

  <rect x="0.5" y="8.5" width="86" height="34" rx="2" fill="var(--paper, #ffffff)"
        stroke="var(--ink, #242424)" stroke-width="1"/>
  <text x="43.5" y="30" text-anchor="middle" font-size="8.5"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">Draft</text>

  <line x1="88" y1="25.5" x2="106" y2="25.5" stroke="var(--ink, #242424)"
        stroke-width="1" marker-end="url(#flow-arrow)"/>

  <rect x="108.5" y="8.5" width="86" height="34" rx="2" fill="var(--paper, #ffffff)"
        stroke="var(--ink, #242424)" stroke-width="1"/>
  <text x="151.5" y="30" text-anchor="middle" font-size="8.5"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">Review</text>

  <line x1="196" y1="25.5" x2="214" y2="25.5" stroke="var(--ink, #242424)"
        stroke-width="1" marker-end="url(#flow-arrow)"/>

  <rect x="216.5" y="8.5" width="86" height="34" rx="2" fill="var(--pale, #f1f1f1)"
        stroke="var(--ink, #242424)" stroke-width="1"/>
  <text x="259.5" y="30" text-anchor="middle" font-size="8.5"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">Approve</text>

  <line x1="304" y1="25.5" x2="322" y2="25.5" stroke="var(--ink, #242424)"
        stroke-width="1" marker-end="url(#flow-arrow)"/>

  <rect x="324.5" y="8.5" width="85" height="34" rx="2" fill="var(--paper, #ffffff)"
        stroke="var(--ink, #242424)" stroke-width="1"/>
  <text x="367" y="30" text-anchor="middle" font-size="8.5"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">Ship</text>

  <!-- The rejection branch is dashed, so it reads as exceptional without
       relying on colour. -->
  <path d="M 259.5 44 L 259.5 62 L 151.5 62 L 151.5 44" fill="none"
        stroke="var(--ink, #242424)" stroke-width="1" stroke-dasharray="4 3"
        marker-end="url(#flow-arrow)"/>
  <text x="205.5" y="74" text-anchor="middle" font-size="7.5"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">rejected</text>
</svg>
```

- [ ] **Step 5: Write `pipeline.svg`**

Create `skills/svg-diagrams/assets/examples/pipeline.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="410.4pt" height="94pt"
     viewBox="0 0 410.4 94" role="img"
     aria-label="Three ordered stages, each labelled with its input and output">
  <defs>
    <marker id="pipe-arrow" viewBox="0 0 10 10" refX="9" refY="5"
            markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--ink, #242424)"/>
    </marker>
  </defs>

  <text x="0" y="10" font-size="7.5" letter-spacing="0.8"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">SOURCE</text>

  <rect x="0.5" y="18.5" width="126" height="40" fill="var(--paper, #ffffff)"
        stroke="var(--ink, #242424)" stroke-width="1"/>
  <text x="63.5" y="36" text-anchor="middle" font-size="9"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">Measure</text>
  <text x="63.5" y="50" text-anchor="middle" font-size="7.5"
        font-family="var(--mono, 'Courier New', monospace)"
        fill="var(--ink, #242424)">paginate</text>

  <line x1="128" y1="38.5" x2="146" y2="38.5" stroke="var(--ink, #242424)"
        stroke-width="1" marker-end="url(#pipe-arrow)"/>

  <rect x="148.5" y="18.5" width="126" height="40" fill="var(--paper, #ffffff)"
        stroke="var(--ink, #242424)" stroke-width="1"/>
  <text x="211.5" y="36" text-anchor="middle" font-size="9"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">Print</text>
  <text x="211.5" y="50" text-anchor="middle" font-size="7.5"
        font-family="var(--mono, 'Courier New', monospace)"
        fill="var(--ink, #242424)">render</text>

  <line x1="276" y1="38.5" x2="294" y2="38.5" stroke="var(--ink, #242424)"
        stroke-width="1" marker-end="url(#pipe-arrow)"/>

  <rect x="296.5" y="18.5" width="113" height="40" fill="var(--pale, #f1f1f1)"
        stroke="var(--ink, #242424)" stroke-width="1"/>
  <text x="353" y="36" text-anchor="middle" font-size="9"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">Assemble</text>
  <text x="353" y="50" text-anchor="middle" font-size="7.5"
        font-family="var(--mono, 'Courier New', monospace)"
        fill="var(--ink, #242424)">merge</text>

  <line x1="0" y1="70.5" x2="409.4" y2="70.5" stroke="var(--ink, #242424)"
        stroke-width="0.5"/>
  <text x="0" y="84" font-size="7.5"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">Each stage reruns when the one before it changes.</text>
</svg>
```

- [ ] **Step 6: Write `cycle.svg`**

Create `skills/svg-diagrams/assets/examples/cycle.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="288pt" height="150pt"
     viewBox="0 0 288 150" role="img"
     aria-label="A four-step loop that returns to its start">
  <defs>
    <marker id="cycle-arrow" viewBox="0 0 10 10" refX="9" refY="5"
            markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--ink, #242424)"/>
    </marker>
  </defs>

  <rect x="84.5" y="0.5" width="118" height="32" rx="2" fill="var(--paper, #ffffff)"
        stroke="var(--ink, #242424)" stroke-width="1"/>
  <text x="143.5" y="21" text-anchor="middle" font-size="8.5"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">Specify</text>

  <rect x="170.5" y="58.5" width="117" height="32" rx="2" fill="var(--paper, #ffffff)"
        stroke="var(--ink, #242424)" stroke-width="1"/>
  <text x="229" y="79" text-anchor="middle" font-size="8.5"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">Build</text>

  <rect x="84.5" y="116.5" width="118" height="32" rx="2" fill="var(--pale, #f1f1f1)"
        stroke="var(--ink, #242424)" stroke-width="1"/>
  <text x="143.5" y="137" text-anchor="middle" font-size="8.5"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">Verify</text>

  <rect x="0.5" y="58.5" width="117" height="32" rx="2" fill="var(--paper, #ffffff)"
        stroke="var(--ink, #242424)" stroke-width="1"/>
  <text x="59" y="79" text-anchor="middle" font-size="8.5"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">Learn</text>

  <path d="M 203 20 L 229 20 L 229 56" fill="none" stroke="var(--ink, #242424)"
        stroke-width="1" marker-end="url(#cycle-arrow)"/>
  <path d="M 229 92 L 229 132 L 204 132" fill="none" stroke="var(--ink, #242424)"
        stroke-width="1" marker-end="url(#cycle-arrow)"/>
  <path d="M 84 132 L 59 132 L 59 92" fill="none" stroke="var(--ink, #242424)"
        stroke-width="1" marker-end="url(#cycle-arrow)"/>
  <path d="M 59 58 L 59 20 L 83 20" fill="none" stroke="var(--ink, #242424)"
        stroke-width="1" marker-end="url(#cycle-arrow)"/>
</svg>
```

- [ ] **Step 7: Run the example tests**

```bash
cd skills/book-writing/scripts && .venv/bin/pytest tests/test_diagram_examples.py -q
```

Expected: the three written examples pass; `layered-stack.svg`, `node-map.svg`, and `annotated-anatomy.svg` still fail on existence. That is correct until Task 7.

- [ ] **Step 8: Commit**

```bash
git add skills/svg-diagrams/assets skills/book-writing/scripts/tests/test_diagram_examples.py
git commit -m "feat(svg-diagrams): add the diagram template and the linear archetypes"
```

---

### Task 7: The three spatial examples

**Files:**
- Create: `skills/svg-diagrams/assets/examples/layered-stack.svg`
- Create: `skills/svg-diagrams/assets/examples/node-map.svg`
- Create: `skills/svg-diagrams/assets/examples/annotated-anatomy.svg`

**Interfaces:**
- Consumes: `check_diagrams` (Task 5), the test from Task 6.
- Produces: three SVG assets, each passing the checker.

- [ ] **Step 1: Write `layered-stack.svg`**

Create `skills/svg-diagrams/assets/examples/layered-stack.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="410.4pt" height="112pt"
     viewBox="0 0 410.4 112" role="img"
     aria-label="Four responsibility bands stacked from interface down to storage">
  <rect x="0.5" y="0.5" width="409" height="26" fill="var(--pale, #f1f1f1)"
        stroke="var(--ink, #242424)" stroke-width="1"/>
  <text x="8" y="17" font-size="8.5"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">Interface</text>
  <text x="402" y="17" text-anchor="end" font-size="7.5"
        font-family="var(--mono, 'Courier New', monospace)"
        fill="var(--ink, #242424)">what the reader touches</text>

  <rect x="0.5" y="28.5" width="409" height="26" fill="var(--paper, #ffffff)"
        stroke="var(--ink, #242424)" stroke-width="1"/>
  <text x="8" y="45" font-size="8.5"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">Behaviour</text>
  <text x="402" y="45" text-anchor="end" font-size="7.5"
        font-family="var(--mono, 'Courier New', monospace)"
        fill="var(--ink, #242424)">rules that must hold</text>

  <rect x="0.5" y="56.5" width="409" height="26" fill="var(--paper, #ffffff)"
        stroke="var(--ink, #242424)" stroke-width="1"/>
  <text x="8" y="73" font-size="8.5"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">Domain</text>
  <text x="402" y="73" text-anchor="end" font-size="7.5"
        font-family="var(--mono, 'Courier New', monospace)"
        fill="var(--ink, #242424)">the shared language</text>

  <!-- The band outside the boundary is dashed rather than differently
       coloured, so the distinction survives greyscale. -->
  <rect x="0.5" y="84.5" width="409" height="26" fill="var(--paper, #ffffff)"
        stroke="var(--ink, #242424)" stroke-width="1" stroke-dasharray="5 3"/>
  <text x="8" y="101" font-size="8.5"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">Storage</text>
  <text x="402" y="101" text-anchor="end" font-size="7.5"
        font-family="var(--mono, 'Courier New', monospace)"
        fill="var(--ink, #242424)">outside the boundary</text>
</svg>
```

- [ ] **Step 2: Write `node-map.svg`**

Create `skills/svg-diagrams/assets/examples/node-map.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="410.4pt" height="128pt"
     viewBox="0 0 410.4 128" role="img"
     aria-label="Two actors on the left connected to three capabilities on the right">
  <text x="0" y="10" font-size="7.5" letter-spacing="0.8"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">ACTORS</text>
  <text x="409" y="10" text-anchor="end" font-size="7.5" letter-spacing="0.8"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">CAPABILITIES</text>

  <rect x="0.5" y="22.5" width="108" height="30" rx="15" fill="var(--paper, #ffffff)"
        stroke="var(--ink, #242424)" stroke-width="1"/>
  <text x="54.5" y="41" text-anchor="middle" font-size="8.5"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">Coordinator</text>

  <rect x="0.5" y="74.5" width="108" height="30" rx="15" fill="var(--paper, #ffffff)"
        stroke="var(--ink, #242424)" stroke-width="1"/>
  <text x="54.5" y="93" text-anchor="middle" font-size="8.5"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">Volunteer</text>

  <rect x="272.5" y="8.5" width="137" height="28" fill="var(--pale, #f1f1f1)"
        stroke="var(--ink, #242424)" stroke-width="1"/>
  <text x="341" y="26" text-anchor="middle" font-size="8.5"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">Publish a shift</text>

  <rect x="272.5" y="48.5" width="137" height="28" fill="var(--pale, #f1f1f1)"
        stroke="var(--ink, #242424)" stroke-width="1"/>
  <text x="341" y="66" text-anchor="middle" font-size="8.5"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">Claim a shift</text>

  <rect x="272.5" y="88.5" width="137" height="28" fill="var(--pale, #f1f1f1)"
        stroke="var(--ink, #242424)" stroke-width="1"/>
  <text x="341" y="106" text-anchor="middle" font-size="8.5"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">Withdraw</text>

  <line x1="110" y1="37.5" x2="271" y2="22.5" stroke="var(--ink, #242424)" stroke-width="1"/>
  <line x1="110" y1="37.5" x2="271" y2="62.5" stroke="var(--ink, #242424)" stroke-width="1"/>
  <line x1="110" y1="89.5" x2="271" y2="62.5" stroke="var(--ink, #242424)" stroke-width="1"/>
  <line x1="110" y1="89.5" x2="271" y2="102.5" stroke="var(--ink, #242424)" stroke-width="1"/>

  <text x="0" y="124" font-size="7.5"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">A capability reached by two actors needs two sets of preconditions.</text>
</svg>
```

- [ ] **Step 3: Write `annotated-anatomy.svg`**

Create `skills/svg-diagrams/assets/examples/annotated-anatomy.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="410.4pt" height="132pt"
     viewBox="0 0 410.4 132" role="img"
     aria-label="A specification artifact with three callouts naming its parts">
  <defs>
    <marker id="anat-tick" viewBox="0 0 8 8" refX="7" refY="4"
            markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 8 4 L 0 8 z" fill="var(--ink, #242424)"/>
    </marker>
  </defs>

  <rect x="0.5" y="0.5" width="228" height="118" fill="var(--paper, #ffffff)"
        stroke="var(--ink, #242424)" stroke-width="1"/>

  <rect x="0.5" y="0.5" width="228" height="24" fill="var(--pale, #f1f1f1)"
        stroke="var(--ink, #242424)" stroke-width="1"/>
  <text x="10" y="16" font-size="8.5"
        font-family="var(--mono, 'Courier New', monospace)"
        fill="var(--ink, #242424)">Claim a shift</text>

  <text x="10" y="42" font-size="8"
        font-family="var(--mono, 'Courier New', monospace)"
        fill="var(--ink, #242424)">Given a published shift</text>
  <text x="10" y="58" font-size="8"
        font-family="var(--mono, 'Courier New', monospace)"
        fill="var(--ink, #242424)">When a volunteer claims it</text>
  <text x="10" y="74" font-size="8"
        font-family="var(--mono, 'Courier New', monospace)"
        fill="var(--ink, #242424)">Then the roster shows them</text>

  <line x1="10" y1="88" x2="218" y2="88" stroke="var(--ink, #242424)" stroke-width="0.5"/>
  <text x="10" y="104" font-size="8"
        font-family="var(--mono, 'Courier New', monospace)"
        fill="var(--ink, #242424)">Capacity must not be exceeded</text>

  <line x1="232" y1="12" x2="262" y2="12" stroke="var(--ink, #242424)"
        stroke-width="1" marker-start="url(#anat-tick)"/>
  <text x="266" y="15" font-size="8"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">Name, in the domain language</text>

  <line x1="232" y1="58" x2="262" y2="58" stroke="var(--ink, #242424)"
        stroke-width="1" marker-start="url(#anat-tick)"/>
  <text x="266" y="61" font-size="8"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">Observable behaviour</text>

  <line x1="232" y1="100" x2="262" y2="100" stroke="var(--ink, #242424)"
        stroke-width="1" marker-start="url(#anat-tick)"/>
  <text x="266" y="103" font-size="8"
        font-family="var(--sans, 'Avenir Next', Arial, sans-serif)"
        fill="var(--ink, #242424)">Invariant that always holds</text>
</svg>
```

- [ ] **Step 4: Run the example tests**

```bash
cd skills/book-writing/scripts && .venv/bin/pytest tests/test_diagram_examples.py -q
```

Expected: all pass. If any example reports a finding, the message names the rule and the fix belongs in the SVG, not in the checker.

- [ ] **Step 5: Commit**

```bash
git add skills/svg-diagrams/assets/examples
git commit -m "feat(svg-diagrams): add the spatial archetypes"
```

---

### Task 8: The reference documents

**Files:**
- Create: `skills/svg-diagrams/references/grammar.md`
- Create: `skills/svg-diagrams/references/archetypes.md`
- Create: `skills/svg-diagrams/references/verification.md`
- Test: `skills/book-writing/scripts/tests/test_svg_skill_structure.py`

**Interfaces:**
- Consumes: the assets from Tasks 6 and 7.
- Produces: three reference documents, each loaded for a specific job.

- [ ] **Step 1: Write the failing test**

Create `skills/book-writing/scripts/tests/test_svg_skill_structure.py`:

```python
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

    for ref in ["references/grammar.md", "references/archetypes.md",
                "references/verification.md"]:
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

    for archetype in ["flow", "layered stack", "node map", "pipeline", "cycle",
                      "annotated anatomy"]:
        assert archetype in text, f"missing archetype: {archetype}"


def test_archetypes_links_each_worked_example():
    text = (REFS / "archetypes.md").read_text(encoding="utf-8")

    for name in ["flow.svg", "pipeline.svg", "cycle.svg", "layered-stack.svg",
                 "node-map.svg", "annotated-anatomy.svg"]:
        assert name in text


def test_verification_names_the_command_and_thresholds():
    text = (REFS / "verification.md").read_text(encoding="utf-8")

    assert "bookkit.diagrams" in text
    assert "1.5" in text and "4.5" in text and "6pt" in text


def test_verification_explains_why_each_failure_is_silent():
    text = (REFS / "verification.md").read_text(encoding="utf-8").lower()

    assert "silent" in text
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd skills/book-writing/scripts && .venv/bin/pytest tests/test_svg_skill_structure.py -q
```

Expected: FAIL, the skill directory does not exist.

- [ ] **Step 3: Write `references/grammar.md`**

Required content:

- **The unit convention.** State `1 user unit = 1 point` explicitly. Explain why: `font-size="9"` then means 9pt on paper, so nobody has to reason about `viewBox` scaling. Note that the checker computes the true rendered size regardless, so a deviation is caught rather than silently shipped.
- **Sizing.** Maximum width 410.4 units, which is 5.7in, which is `--page-w` minus twice `--margin` at the default trim. Dimensions in `in` or `pt`, never `px`, never unitless. Every `<svg>` declares `width`, `height`, and `viewBox`.
- **Colour.** Every `fill` and `stroke` is `var(--token, fallback)`. Inline in a page the token resolves to the book's palette; standalone the fallback applies. List the tokens: `--ink`, `--paper`, `--pale`, `--accent`, `--support`, `--caution`, `--muted`.
- **The three tonal levels.** Reproduce the contrast table from the spec. State the rule: dark, one mid grey, light, so at most three categories by fill alone. Cite `--accent` against `--support` at **1.14:1** as the motivating case, and `--caution` against `--muted` at 1.02:1 as the worst. A fourth category needs a dash pattern, stroke weight, hatch, or label.
- **Primitives**, with a code fragment each: box (`rect` with 0.5 offsets so a 1-unit stroke lands on a whole pixel), arrow (`marker` in `defs`, `orient="auto-start-reverse"`), lane, label, rule, annotation (leader line plus text).
- **Type.** Body labels at 8 to 9 units, secondary at 7.5, nothing below 6. The interior's smallest type is `.label` at 6.8pt for comparison.
- **Accessibility.** Every diagram carries `role="img"` and an `aria-label` that describes it for a reader who cannot see it.

- [ ] **Step 4: Write `references/archetypes.md`**

Required content: one section per archetype, each naming when it fits, when it does not, and linking its worked example.

- **Flow** (`assets/examples/flow.svg`): a sequence of steps with branches. The exceptional branch is dashed rather than coloured. Not for concurrent work.
- **Pipeline** (`assets/examples/pipeline.svg`): ordered stages, each with an input and an output. Use when the stages have names a reader will type as commands. Timelines are this archetype with dates.
- **Cycle** (`assets/examples/cycle.svg`): a loop returning to its start. Four steps maximum before it stops reading as a loop.
- **Layered stack** (`assets/examples/layered-stack.svg`): responsibility bands. Anything outside the boundary is dashed.
- **Node map** (`assets/examples/node-map.svg`): actors against capabilities. Not a class diagram, and not for more than about eight nodes.
- **Annotated anatomy** (`assets/examples/annotated-anatomy.svg`): callouts naming the parts of an artifact. The strongest choice when a chapter introduces a template.

Close with what to use instead: matrices stay HTML tables via `.matrix` in `interior.css`, because a table is not a drawing.

- [ ] **Step 5: Write `references/verification.md`**

Required content:

- The command, for a book directory, an HTML file, or a standalone SVG:

  ```bash
  cd skills/book-writing/scripts
  .venv/bin/python -m bookkit.diagrams /path/to/book
  ```

- A note that `bookkit.verify` already calls these checks, so a book needs no extra command, and that standalone use requires `bookkit` installed.
- A table of the eight checks with the thresholds `1.5:1` fill contrast, `4.5:1` text contrast, `6pt` type floor, and for each one the sentence explaining why the failure is **silent** without it.
- The escape for a low-contrast pair: separate the two by a dash pattern or a stroke weight. Explain that this is what `interior.css` already does for callouts with border style and label glyphs, so the rule is "colour alone is not enough" rather than "these colours are banned".

Every reference is prose that ships, so run the `avoid-ai-writing` skill over all three before committing, per `book-writing/references/editorial-standards.md`.

- [ ] **Step 6: Run the tests**

```bash
cd skills/book-writing/scripts && .venv/bin/pytest tests/test_svg_skill_structure.py -q
```

Expected: the reference tests pass; `test_skill_md_exists_and_is_named` and the router tests still fail until Task 9.

- [ ] **Step 7: Commit**

```bash
git add skills/svg-diagrams/references \
        skills/book-writing/scripts/tests/test_svg_skill_structure.py
git commit -m "docs(svg-diagrams): add grammar, archetypes, and verification references"
```

---

### Task 9: The SKILL.md router

**Files:**
- Create: `skills/svg-diagrams/SKILL.md`

**Interfaces:**
- Consumes: every reference and asset from Tasks 6 to 8.
- Produces: the skill entry point, under 700 words.

- [ ] **Step 1: Write the router**

Create `skills/svg-diagrams/SKILL.md`:

```markdown
---
name: svg-diagrams
description: Author SVG diagrams that survive print. Token-driven, legible in greyscale, and checked mechanically. Use when a chapter, article, or document needs a flow, architecture stack, node map, pipeline, cycle, or annotated artifact.
---

# Drawing a diagram

Diagrams here are hand-authored inline SVG. They inherit the surrounding design tokens, so
they retarget when the document does, and they are checked before they ship.

Work in this order.

## ① Decide whether a diagram earns its place

A diagram is worth making when the relationship between things is the point. If the content
is a list, write a list. If it is a set of values across two axes, use a table: `.matrix` in
`interior.css` already handles those, and a table is not a drawing.

## ② Pick the archetype

Read `references/archetypes.md`. Six archetypes cover most of what a technical book needs:
flow, pipeline, cycle, layered stack, node map, annotated anatomy. Each links a worked
example under `assets/examples/` that already passes the checker. Start from the closest one
rather than from scratch.

## ③ Draw it

Read `references/grammar.md` before writing any SVG. Three rules do most of the work:

- **One user unit is one point.** `font-size="9"` then means 9pt on paper.
- **Maximum width is 410.4 units**, the text measure at the default 7 × 10in trim.
- **Every colour is `var(--token, fallback)`.** Never a literal hex.

The constraint that catches people: **the palette has three tonal levels, not seven
colours.** In greyscale `--accent` and `--support` sit at 1.14:1, and `--caution` and
`--muted` at 1.02:1. They are the same grey on paper. So a diagram can encode at most three
categories by fill alone. A fourth needs a dash pattern, a stroke weight, a hatch, or a
label.

Start from `assets/diagram.template.svg`.

## ④ Check it

Read `references/verification.md`.

```bash
cd skills/book-writing/scripts
.venv/bin/python -m bookkit.diagrams /path/to/file-or-directory
```

Inside a book this is already covered: `bookkit.verify` runs the same checks over every page
file, so the production pipeline catches diagrams with no extra command.

The checker rejects text below the 6pt print floor, text under 4.5:1 contrast, fills that
collapse in greyscale without another differentiating channel, content cropped by the
`viewBox`, hardcoded colours, external or raster references, gradients and filters, and
missing or `px` dimensions. Every one of those is invisible on a backlit screen and obvious
on paper, which is why none of them is a warning.
```

- [ ] **Step 2: Run the tests**

```bash
cd skills/book-writing/scripts && .venv/bin/pytest tests/test_svg_skill_structure.py -q
```

Expected: all pass.

- [ ] **Step 3: Run the whole suite**

```bash
cd skills/book-writing/scripts && .venv/bin/pytest -q
```

Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add skills/svg-diagrams/SKILL.md
git commit -m "feat(svg-diagrams): add the router"
```

---

### Task 10: Delegation, packaging, and docs

**Files:**
- Modify: `skills/book-writing/SKILL.md`
- Modify: `skills/book-writing/references/interior-design.md`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `README.md`
- Modify: `.github/workflows/test.yml`
- Test: `skills/book-writing/scripts/tests/test_skill_structure.py` (append)

**Interfaces:**
- Consumes: the finished `svg-diagrams` skill.
- Produces: `book-writing` phase ④ delegating to it, a second plugin entry, and CI coverage.

- [ ] **Step 1: Write the failing test**

Append to `skills/book-writing/scripts/tests/test_skill_structure.py`:

```python


def test_drafting_phase_delegates_diagrams_to_the_svg_skill():
    """Diagrams are a distinct capability, delegated the way the gate is."""
    text = SKILL_MD.read_text(encoding="utf-8")

    drafting = _phase_section(text, "## \\u2463 Chapter")

    assert "svg-diagrams" in drafting


def test_interior_design_points_at_the_diagram_skill():
    reference = SKILL / "references" / "interior-design.md"
    text = reference.read_text(encoding="utf-8")

    assert "svg-diagrams" in text
```

- [ ] **Step 2: Run it to verify it fails**

```bash
cd skills/book-writing/scripts && .venv/bin/pytest tests/test_skill_structure.py -q
```

Expected: FAIL on both new tests.

- [ ] **Step 3: Add the delegation to phase ④**

In `skills/book-writing/SKILL.md`, inside the `## ④ Chapter: draft and typeset` section,
after the paragraph about `ch-` prefixed diagram CSS, add:

```markdown
When a chapter needs a diagram, invoke the **`svg-diagrams`** skill. Diagrams are inline SVG
driven by the same tokens as the interior, so they need no `ch-` class at all, and
`bookkit.verify` already checks them.
```

- [ ] **Step 4: Point `interior-design.md` at the skill**

In `skills/book-writing/references/interior-design.md`, in the layout-discipline section,
after the bullet requiring diagrams to read in greyscale, add:

```markdown
The **`svg-diagrams`** skill enforces this mechanically rather than leaving it as a rule
nobody can check by eye. It also documents the constraint the palette imposes: in greyscale
the tokens resolve to three tonal levels, so a diagram can encode at most three categories
by fill alone.
```

- [ ] **Step 5: Add the plugin entry**

In `.claude-plugin/marketplace.json`, add a second object to the `plugins` array:

```json
    {
      "name": "svg-diagrams",
      "source": "./",
      "description": "Author SVG diagrams that survive print: token-driven, legible in greyscale, and checked mechanically against a type floor, contrast thresholds, and the page geometry.",
      "category": "productivity",
      "keywords": ["svg", "diagrams", "typesetting", "accessibility", "publishing"]
    }
```

- [ ] **Step 6: Extend CI**

In `.github/workflows/test.yml`, in the `pipeline` job, after the clipped-page step, add:

```yaml
      - name: Diagram checker rejects a colour-only encoding
        run: |
          cat > "$RUNNER_TEMP/bad.svg" <<'SVG'
          <svg xmlns="http://www.w3.org/2000/svg" width="288pt" height="72pt" viewBox="0 0 288 72">
            <rect x="10" y="10" width="60" height="40" fill="var(--accent, #d54b20)"/>
            <rect x="90" y="10" width="60" height="40" fill="var(--support, #177c83)"/>
          </svg>
          SVG
          if python -m bookkit.diagrams "$RUNNER_TEMP/bad.svg"; then
            echo "::error::diagram checker passed a colour-only encoding"
            exit 1
          fi
          echo "diagram checker correctly rejected the colour-only encoding"

      - name: Shipped diagram examples all pass
        run: python -m bookkit.diagrams ../../svg-diagrams/assets/examples
```

- [ ] **Step 7: Update the README**

In `README.md`, add `svg-diagrams` to the install section as a second plugin, and add a short
section after "Why verification is not optional":

```markdown
## Diagrams

The companion `svg-diagrams` skill covers diagrams. They are inline SVG driven by the same
tokens as the interior, so they retarget with the book, and `bookkit.verify` checks them
alongside everything else.

The check that earns its keep is greyscale. `interior-design.md` always said diagrams must
never carry meaning in colour alone; nothing enforced it. Measuring the palette shows why
that mattered: `--accent` and `--support` sit at 1.14:1 in greyscale and `--caution` and
`--muted` at 1.02:1. Obviously different on a monitor, the same grey on paper. A diagram may
encode three categories by fill; a fourth needs a dash pattern or a stroke weight.
```

Update the test count in the README to the number reported by the suite.

- [ ] **Step 8: Run everything**

```bash
cd skills/book-writing/scripts && .venv/bin/pytest -q
```

Expected: all pass.

- [ ] **Step 9: Verify the CI pipeline job locally**

```bash
cd skills/book-writing/scripts
.venv/bin/python -m bookkit.diagrams ../../svg-diagrams/assets/examples
```

Expected: `OK: diagrams in 6 file(s) verified`, exit 0.

- [ ] **Step 10: Commit**

```bash
git add -A
git commit -m "feat: delegate diagrams from book-writing to the svg-diagrams skill"
```

---

## Self-Review

**Spec coverage.**

| Spec section | Task |
|---|---|
| Packaging and skill layout | 6–9 |
| Token contract, `var(--token, fallback)` | 3 (check), 6 (template), 8 (grammar.md) |
| Sizing, 410.4pt measure, no `px` | 3 (check), 6 (examples), 8 (grammar.md) |
| Three tonal levels, 1.14:1 motivating case | 2 (test), 8 (grammar.md), 10 (README) |
| Six archetypes | 6, 7 (assets), 8 (archetypes.md) |
| `findings.py` extraction | 1 |
| Colour maths | 2 |
| Checks 5–8, static | 3 |
| Checks 1–4, rendered | 4 |
| Non-colour differentiator escape | 4 |
| Rendered-scale type floor | 4 |
| `check_diagrams`, CLI, verify integration | 5 |
| Dogfooding the examples | 6, 7 |
| Skill structure tests | 8, 9 |
| book-writing delegation | 10 |

Every spec requirement maps to a task.

**Type consistency.** `Finding(level, file, message)` is defined in Task 1 and used unchanged in Tasks 3, 4, 5. `parse_color`, `relative_luminance`, `contrast_ratio` are defined in Task 2 and consumed in Task 4. `static_findings(source, file, index)` from Task 3 and `find_diagrams(path)` plus `rendered_findings(diagram)` from Task 4 are both consumed by `check_diagrams` in Task 5 with matching signatures. `Diagram.source` is populated in Task 4 and read by `check_diagrams` in Task 5. `_error(file, index, message)` is defined once in Task 3 and reused in Task 4. No name drifts.

**Known ordering dependency.** Task 6's test file asserts all six examples exist, so three of its cases fail until Task 7 completes. This is called out in Task 6 Step 7 rather than hidden, because splitting the test file across two tasks would be worse than a briefly red test the plan predicts.
