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
