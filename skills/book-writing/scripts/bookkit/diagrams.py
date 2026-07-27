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
