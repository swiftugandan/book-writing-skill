"""Enforce the two-layer CSS boundary.

The core layer (`assets/interior.css`) is shared by every page file. A chapter
may add its own diagram components in an inline `<style>` block, but those must
be prefixed `ch-` and must never redefine a core selector — otherwise one
chapter silently changes the look of the whole book.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

LOCAL_PREFIX = "ch-"

_STYLE_BLOCK = re.compile(r"<style[^>]*>(.*?)</style>", re.DOTALL | re.IGNORECASE)
_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_DECLARATIONS = re.compile(r"\{[^{}]*\}", re.DOTALL)
_CLASS_NAME = re.compile(r"\.(-?[_a-zA-Z][_a-zA-Z0-9-]*)")


@dataclass(frozen=True)
class CssViolation:
    """A chapter-local selector that breaks the layering rule."""

    file: str
    selector: str
    reason: str  # "unprefixed" | "shadows-core"


def _class_names(css: str) -> frozenset[str]:
    """Every class name appearing in a selector position."""
    without_comments = _COMMENT.sub(" ", css)
    selectors_only = _DECLARATIONS.sub(" ", without_comments)
    return frozenset(_CLASS_NAME.findall(selectors_only))


def core_selectors(css_path: Path) -> frozenset[str]:
    """Class names defined by the shared core stylesheet."""
    return _class_names(css_path.read_text(encoding="utf-8"))


def local_selectors(html_path: Path) -> frozenset[str]:
    """Class names defined in a page file's inline `<style>` blocks."""
    html = html_path.read_text(encoding="utf-8")
    names: set[str] = set()
    for block in _STYLE_BLOCK.findall(html):
        names |= _class_names(block)
    return frozenset(names)


def check_css_layering(html_path: Path, css_path: Path) -> list[CssViolation]:
    """Report every chapter-local selector that is unprefixed or shadows core."""
    core = core_selectors(css_path)
    violations = []
    for name in local_selectors(html_path):
        if name in core:
            reason = "shadows-core"
        elif not name.startswith(LOCAL_PREFIX):
            reason = "unprefixed"
        else:
            continue
        violations.append(
            CssViolation(file=html_path.name, selector=name, reason=reason)
        )
    return sorted(violations, key=lambda v: v.selector)
