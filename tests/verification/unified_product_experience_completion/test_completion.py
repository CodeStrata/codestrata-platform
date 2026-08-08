"""Unit tests for Slice 14.14 Epic 14 completion verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.unified_product_experience_completion.contract import (
    POLICY_ID,
    POLICY_RELATIVE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    TOTAL_SLICES,
    monorepo_root_from_here,
)
from verification.unified_product_experience_completion.determinism import (
    reports_byte_identical,
)
from verification.unified_product_experience_completion.inventory import load_json
from verification.unified_product_experience_completion.policy_registry import (
    build_policy_registry,
)
from verification.unified_product_experience_completion.runner import build_report
from verification.unified_product_experience_completion.schema_registry import (
    build_schema_registry,
)
from verification.unified_product_experience_completion.scenarios import (
    COMPLETION_SCENARIOS,
    NEGATIVE_COMPLETION_CHECKS,
)
from verification.unified_product_experience_completion.slice_matrix import SLICE_TITLES


def test_completion_policy() -> None:
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    assert policy["policy_id"] == POLICY_ID
    assert policy["policy_version"] == "1.0"
    assert policy["epic"] == 14
    assert policy["slice_count"] == 14
    assert policy["start_epic_15"] is False
    assert policy["production_deploy_complete"] is False
    assert policy["release_tag_created"] is False
    assert policy["design_system_complete"] is True
    assert policy["cross_surface_consistency_complete"] is True


def test_slice_matrix_titles() -> None:
    assert len(SLICE_TITLES) == TOTAL_SLICES
    assert SLICE_TITLES["14.14"] == "Epic 14 Completion Verification"


def test_policy_registry_shape() -> None:
    monorepo = monorepo_root_from_here()
    rows = build_policy_registry(monorepo)
    assert len(rows) >= 15
    ids = [r["policy_id"] for r in rows]
    assert len(ids) == len(set(ids))
    assert POLICY_ID in ids


def test_schema_registry_includes_completion() -> None:
    rows = build_schema_registry()
    names = {r["schema_name"] for r in rows}
    assert SCHEMA_NAME in names
    assert "assessment" in names


def test_scenarios_a_to_z() -> None:
    assert len(COMPLETION_SCENARIOS) == 26
    assert COMPLETION_SCENARIOS[0][0] == "A"
    assert COMPLETION_SCENARIOS[-1][0] == "Z"
    assert len(NEGATIVE_COMPLETION_CHECKS) == 26


def test_build_report_without_heavy_regressions(tmp_path: Path) -> None:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo, run_regressions=False)
    assert report.schema_name == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert report.completed_slices == TOTAL_SLICES
    assert report.total_slices == TOTAL_SLICES
    assert report.epic_complete is True
    assert report.release_posture.get("start_epic_15") is False
    assert report.release_posture.get("commit_created") is False
    assert report.release_posture.get("tag_created") is False
    assert report.release_posture.get("published") is False
    assert report.release_posture.get("deployed") is False
    assert report.release_posture.get("marketplace_published") is False
    assert report.release_posture.get("docs_production_deployed") is False
    assert report.release_posture.get("epic_14_complete") is True
    # Serialize to a temp path so pytest does not overwrite the authoritative
    # sv14-14 completion report produced by the full runner.
    text = json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"
    out = tmp_path / "unified-product-experience-completion-verification.json"
    out.write_text(text, encoding="utf-8")
    assert "timestamp" not in text.lower()
    assert "/Users/" not in text
    assert "file://" not in text


def test_runner_deterministic_without_heavy_regressions() -> None:
    monorepo = monorepo_root_from_here()
    a = build_report(monorepo, run_regressions=False).to_dict()
    b = build_report(monorepo, run_regressions=False).to_dict()
    assert reports_byte_identical(a, b)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
