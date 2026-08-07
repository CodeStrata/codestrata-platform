"""Tests for Slice 12.7 Infrastructure repository export verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.infrastructure_repository_export.contract import (
    REPORT_JSON,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV127_OUTPUT_RELATIVE,
    VALIDATION_ROOTS,
    default_contract,
    monorepo_root_from_here,
)


def test_contract_flags() -> None:
    c = default_contract()
    assert c.start_slice_12_8 is False
    assert c.no_git is True
    assert c.no_aws is True
    assert c.no_plan is True
    assert c.no_apply is True
    assert c.schema_name == SCHEMA_NAME
    assert c.schema_version == SCHEMA_VERSION
    assert len(VALIDATION_ROOTS) == 3


def test_verification_report_artifact() -> None:
    """Assert the latest SV12.7 report artifact (produced by the runner)."""

    path = monorepo_root_from_here() / SV127_OUTPUT_RELATIVE / REPORT_JSON
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schema_name"] == SCHEMA_NAME
    assert data["schema_version"] == SCHEMA_VERSION
    assert data["verdict"] in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert data["failed_checks"] == 0
    assert data["dual_export_status"] == "pass"
    assert data["deterministic_tree_status"] == "pass"
    assert data["manifest_status"] == "pass"
    assert data["opentofu_validate_status"] == "pass"
    assert data["python_test_status"] == "pass"
    assert data["git_boundary_status"] == "pass"
    assert "modules/community-cloud-api" in data["validation_roots"]
    blob = path.read_text(encoding="utf-8")
    assert "/Users/" not in blob
    assert "timestamp" not in blob.lower() or "timestamps" in blob.lower()
    # Forbid credential-shaped and account leaks
    for tok in ("AKIA", "-----BEGIN", "amazonaws.com"):
        assert tok not in blob
