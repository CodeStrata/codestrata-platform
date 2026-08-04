"""Negative fixture checks for release artifact detectors."""

from __future__ import annotations

from verification.release_artifacts.contract import AUTHORITATIVE_REPOSITORY_COUNT
from verification.release_artifacts.models import CheckResult


def _wheel_listing_has_platform(members: list[str]) -> bool:
    forbidden = ("platform/", "infrastructure/", "verification/", "tests/")
    return any(
        name.startswith(prefix) or f"/{prefix}" in name for name in members for prefix in forbidden
    )


def _opentofu_skipped_reported_as_pass(checks: list[dict[str, object]]) -> bool:
    for item in checks:
        if item.get("name") == "opentofu:cli_validation" and item.get("ok") is True:
            detail = str(item.get("detail") or "")
            if "not_executed_tool_unavailable" in detail:
                return True
    return False


def _repo_count_valid(count: int) -> bool:
    return count == AUTHORITATIVE_REPOSITORY_COUNT


def check_negative_scenarios() -> list[CheckResult]:
    results: list[CheckResult] = []

    bad_wheel = ["codestrata/__init__.py", "platform/src/foo.py"]
    results.append(
        CheckResult(
            name="negative:wheel_platform_paths_fail",
            ok=_wheel_listing_has_platform(bad_wheel),
            detail="detector flags platform/ in wheel listing",
            category="negative",
        )
    )

    good_wheel = ["codestrata/__init__.py", "codestrata/cli/main.py"]
    results.append(
        CheckResult(
            name="negative:wheel_clean_listing_pass",
            ok=not _wheel_listing_has_platform(good_wheel),
            detail="clean wheel listing passes",
            category="negative",
        )
    )

    skipped_checks = [
        {
            "name": "opentofu:cli_validation",
            "ok": True,
            "detail": "not_executed_tool_unavailable",
        }
    ]
    results.append(
        CheckResult(
            name="negative:opentofu_skipped_not_pass",
            ok=_opentofu_skipped_reported_as_pass(skipped_checks),
            detail="skipped OpenTofu must not be reported as PASS",
            category="negative",
        )
    )

    results.append(
        CheckResult(
            name="negative:repo_count_19_fails",
            ok=not _repo_count_valid(19),
            detail="19-repo EIR export fails authoritative 22-repo gate",
            category="negative",
        )
    )
    results.append(
        CheckResult(
            name="negative:repo_count_22_passes",
            ok=_repo_count_valid(22),
            detail="22-repo count passes",
            category="negative",
        )
    )

    return results
