"""Authoritative verification report output under .codestrata-artifacts (Slice 17.12)."""

from __future__ import annotations

from pathlib import Path

ARTIFACT_ROOT_NAME = ".codestrata-artifacts"
VALIDATION_SUITES_RELATIVE = f"{ARTIFACT_ROOT_NAME}/validation/suites"
LEGACY_VERIFICATION_PREFIX = "reports/verification/"


def validation_suite_relative(suite_id: str) -> str:
    """Return repo-relative path for a verification suite report directory."""

    suite = suite_id.strip().strip("/")
    if suite.startswith(VALIDATION_SUITES_RELATIVE):
        return suite
    for prefix in (
        LEGACY_VERIFICATION_PREFIX,
        "engine/reports/verification/",
        "platform/reports/verification/",
    ):
        if suite.startswith(prefix):
            suite = suite[len(prefix):]
            break
    return f"{VALIDATION_SUITES_RELATIVE}/{suite}"


def validation_suite_path(monorepo: Path, suite_id: str) -> Path:
    return monorepo / validation_suite_relative(suite_id)
