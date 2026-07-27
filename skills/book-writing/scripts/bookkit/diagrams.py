"""Check that SVG diagrams survive print.

`interior-design.md` requires diagrams to read in greyscale and never carry
meaning in colour alone. Nothing enforced it, and the interior's own palette
makes the gap concrete: `--accent` and `--support` differ obviously on screen
and sit at a greyscale contrast of 1.14:1, which is the same grey on paper.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Sequence

from bookkit.findings import Finding, has_errors
from bookkit.measure import browser_page

MIN_FILL_CONTRAST = 1.5
MIN_TEXT_CONTRAST = 4.5
MIN_TYPE_PT = 6.0

_RGB = re.compile(
    r"rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)\s*(?:[,/]\s*([\d.]+)\s*)?\)"
)
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
        return tuple(  # type: ignore[return-value]
            int(round(float(match.group(i)))) for i in (1, 2, 3)
        )

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


# ---------------------------------------------------------------- static checks

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
            _error(file, index, "raster <image>; the PDF will show a missing graphic")
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
        findings.append(
            _error(file, index, "no viewBox; the diagram cannot scale predictably")
        )

    dimensions = {name.lower(): value.strip() for name, value in _DIMENSION.findall(tag)}
    for name in ("width", "height"):
        value = dimensions.get(name)
        if value is None:
            findings.append(_error(file, index, f"no {name} on the <svg> element"))
            continue
        if value.endswith("px"):
            findings.append(
                _error(
                    file, index, f'{name}="{value}" is in px; a page is a physical object'
                )
            )
        elif not value.endswith(_ALLOWED_UNITS):
            findings.append(
                _error(file, index, f'{name}="{value}" has no unit; use in or pt')
            )

    return findings


# -------------------------------------------------------------- rendered checks

_COLLECT_JS = """
() => {
  const paper = getComputedStyle(document.documentElement)
    .getPropertyValue('--paper').trim() || 'rgb(255, 255, 255)';
  return Array.from(document.querySelectorAll('svg')).map((svg, index) => {
    const box = svg.viewBox.baseVal;
    const rendered = svg.getBoundingClientRect();
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
        size_pt: parseFloat(s.fontSize) * scale,
      }, geometry(el));
    });

    return {
      index,
      viewbox: [box.x, box.y, box.width, box.height],
      scale, paper, shapes, texts,
      source: svg.outerHTML,
    };
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
            viewbox=tuple(item["viewbox"]),
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


def _differentiated(left: list[DiagramShape], right: list[DiagramShape]) -> bool:
    """True when two fill groups differ by a channel other than colour."""
    if {s.dash for s in left} != {s.dash for s in right}:
        return True
    return {round(s.stroke_width, 2) for s in left} != {
        round(s.stroke_width, 2) for s in right
    }


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
                        f'text "{text.content[:24]}" has {ratio:.2f}:1 contrast '
                        f"against its background, below {MIN_TEXT_CONTRAST}:1",
                    )
                )

    by_fill: dict[str, list[DiagramShape]] = {}
    for shape in diagram.shapes:
        if parse_color(shape.fill):
            by_fill.setdefault(shape.fill, []).append(shape)

    for left, right in combinations(sorted(by_fill), 2):
        a, b = parse_color(left), parse_color(right)
        if not a or not b:
            continue
        ratio = contrast_ratio(a, b)
        if ratio >= MIN_FILL_CONTRAST or _differentiated(by_fill[left], by_fill[right]):
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
        if shape.width and shape.height and (
            shape.x < x - 0.5
            or shape.y < y - 0.5
            or shape.x + shape.width > x + width + 0.5
            or shape.y + shape.height > y + height + 0.5
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


# ------------------------------------------------------------------------- CLI

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
    parser.add_argument(
        "target", type=Path, help="a book directory, an HTML file, or an SVG file"
    )
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
