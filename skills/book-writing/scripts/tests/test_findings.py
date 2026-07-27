import dataclasses

import pytest

from bookkit.findings import Finding, has_errors


def test_finding_carries_level_file_and_message():
    finding = Finding(level="error", file="a.html", message="broke")

    assert (finding.level, finding.file, finding.message) == ("error", "a.html", "broke")


def test_findings_are_frozen():
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
    from bookkit.verify import Finding as VerifyFinding
    from bookkit.verify import has_errors as verify_has_errors

    assert VerifyFinding is Finding
    assert verify_has_errors is has_errors
