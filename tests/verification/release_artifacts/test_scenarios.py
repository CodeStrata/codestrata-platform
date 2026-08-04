"""Negative scenario detector tests."""

from __future__ import annotations

from verification.release_artifacts.scenarios import check_negative_scenarios


def test_negative_scenarios_all_pass() -> None:
    results = check_negative_scenarios()
    assert results
    assert all(r.ok for r in results)


def test_wheel_platform_detector() -> None:
    results = {r.name: r for r in check_negative_scenarios()}
    assert results["negative:wheel_platform_paths_fail"].ok is True
    assert results["negative:wheel_clean_listing_pass"].ok is True


def test_repo_count_gate() -> None:
    results = {r.name: r for r in check_negative_scenarios()}
    assert results["negative:repo_count_19_fails"].ok is True
    assert results["negative:repo_count_22_passes"].ok is True
