"""Focused tests for Slice 12.9 CI/release boundary verification."""

from __future__ import annotations

from pathlib import Path

from verification.ci_release_boundaries.contract import (
    REQUIRED_CI_JOBS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SUPPORTED_EXPORT_TARGETS,
)
from verification.ci_release_boundaries.runner import build_report, run
from verification.ci_release_boundaries.workflow_inventory import (
    classify_jobs,
    load_primary_workflow,
)

ROOT = Path(__file__).resolve().parents[3]


def test_workflow_exists_and_parses() -> None:
    inv = load_primary_workflow(ROOT)
    assert inv is not None
    assert set(REQUIRED_CI_JOBS).issubset(set(inv.job_names))


def test_no_cursor_jobs() -> None:
    inv = load_primary_workflow(ROOT)
    assert inv is not None
    assert not any("cursor" in n.lower() for n in inv.job_names)


def test_vscode_ci_preserved() -> None:
    inv = load_primary_workflow(ROOT)
    assert inv is not None
    body = inv.job_bodies["vscode-ci"].lower()
    assert "npm ci" in body
    assert "npm run compile" in body
    assert "npm test" in body
    assert "package:dry" in body
    assert "vsce publish" not in body


def test_community_and_infra_export_jobs_isolated() -> None:
    inv = load_primary_workflow(ROOT)
    assert inv is not None
    c = inv.job_bodies["community-export-verification"]
    i = inv.job_bodies["infrastructure-export-verification"]
    assert "--target community" in c
    assert "--target infrastructure" in i
    assert "community-export" in c
    assert "infrastructure-export" in i
    assert "infrastructure-export" not in c
    assert "community-export" not in i


def test_infra_opentofu_safe_commands() -> None:
    inv = load_primary_workflow(ROOT)
    assert inv is not None
    body = inv.job_bodies["infrastructure-export-verification"]
    assert "tofu fmt -check -recursive" in body
    assert "tofu init -backend=false" in body
    assert "tofu validate" in body
    assert "tofu plan" not in body.lower()
    assert "tofu apply" not in body.lower()
    assert "tofu destroy" not in body.lower()
    assert "configure-aws-credentials" not in body.lower()
    assert "git init" not in body.lower()
    assert (
        'PYTHONPATH: ""' in body
        or "PYTHONPATH=\"\"" in body
        or "PYTHONPATH=" in body
    )
    assert "PYTHONPATH=." not in body


def test_workflow_permissions_least_privilege() -> None:
    inv = load_primary_workflow(ROOT)
    assert inv is not None
    assert inv.permissions.get("contents") == "read"
    assert inv.permissions.get("id-token") != "write"


def test_classifications_cover_required_jobs() -> None:
    inv = load_primary_workflow(ROOT)
    assert inv is not None
    classes = classify_jobs(inv)
    assert classes["vscode-ci"] == "preserve_vscode_ci"
    assert classes["community-export-verification"] == "add_community_export_verification"
    assert (
        classes["infrastructure-export-verification"]
        == "add_infrastructure_export_verification"
    )
    assert classes["Slice 12.10"] == "Slice_12_10_completion_only"


def test_export_targets_closed() -> None:
    assert set(SUPPORTED_EXPORT_TARGETS) == {
        "community",
        "infrastructure",
        "insights",
    }


def test_runner_passes() -> None:
    report = build_report(ROOT)
    assert report.schema_name == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.failed_checks == 0, [c.name for c in report.checks if not c.ok]
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert report.active_editor_extensions == ["vscode"]
    assert "cursor" not in report.active_editor_extensions


def test_runner_writes_report() -> None:
    r1 = run(ROOT)
    r2 = run(ROOT)
    assert r1.verdict == r2.verdict
    assert r1.failed_checks == r2.failed_checks
    path = ROOT / "reports/verification/sv12-9/ci-release-boundary-verification.json"
    assert path.is_file()
    blob = path.read_text(encoding="utf-8")
    assert "/Users/" not in blob
    assert "AKIA" not in blob
    assert "AWS_SECRET" not in blob


def test_release_inventory_infra_boundary() -> None:
    text = (ROOT / "scripts/release/inventory.py").read_text(encoding="utf-8")
    assert "private_infrastructure_only" in text
    assert "independently versioned" in text
    assert "cursor-plugin" not in text
