"""Integration smoke for SV.16."""

from __future__ import annotations

from verification.release_artifacts import RELEASE_ARTIFACTS_ID
from verification.release_artifacts.contract import monorepo_root_from_here
from verification.release_artifacts.runner import run_release_artifacts


def test_runner_import_and_dry_run() -> None:
    assert RELEASE_ARTIFACTS_ID.startswith("sv16")
    report = run_release_artifacts(
        monorepo=monorepo_root_from_here(),
        skip_build=True,
        skip_install=True,
    )
    assert report.schema_name == "release-artifact-verification"
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS", "FAIL", "BLOCKED"}
    assert report.confirmations["start_sv17"] is False
    assert report.confirmations["no_tag"] is True
