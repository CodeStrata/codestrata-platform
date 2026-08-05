"""Shared assertion helpers for data lake integration tests."""

from __future__ import annotations

from verification.community_data_lake.models import CheckResult


def assert_all_ok(results: list[CheckResult], *, label: str = "") -> None:
    failures = [item for item in results if not item.ok]
    assert not failures, f"{label} failures: {[f'{r.name}:{r.detail}' for r in failures]}"


def assert_named_ok(results: list[CheckResult], name: str) -> None:
    match = [item for item in results if item.name == name]
    assert match, f"missing check {name!r}"
    assert match[0].ok, f"{name}: {match[0].detail}"
