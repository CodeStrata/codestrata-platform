"""Workflow inventory — parse and classify active CI surfaces (Slice 12.9)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

from verification.ci_release_boundaries.contract import (
    REQUIRED_CI_JOBS,
    WORKFLOW_RELATIVE,
)
from verification.ci_release_boundaries.models import CheckResult, Defect


@dataclass
class WorkflowInventory:
    workflow_relative: str
    job_names: list[str] = field(default_factory=list)
    job_bodies: dict[str, str] = field(default_factory=dict)
    workflow_text: str = ""
    permissions: dict[str, Any] = field(default_factory=dict)
    classifications: dict[str, str] = field(default_factory=dict)


def _flatten_run_text(job: dict[str, Any]) -> str:
    chunks: list[str] = []
    for step in job.get("steps") or []:
        if not isinstance(step, dict):
            continue
        for key in ("run", "name", "uses", "working-directory"):
            val = step.get(key)
            if isinstance(val, str):
                chunks.append(val)
        env = step.get("env") or {}
        if isinstance(env, dict):
            for k, v in env.items():
                chunks.append(f"{k}={v}")
    # permissions / defaults
    perms = job.get("permissions")
    if isinstance(perms, dict):
        chunks.append(str(perms))
    return "\n".join(chunks)


def load_primary_workflow(monorepo: Path) -> WorkflowInventory | None:
    path = monorepo / WORKFLOW_RELATIVE
    if not path.is_file() or yaml is None:
        return None
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        return None
    jobs = data.get("jobs") or {}
    inv = WorkflowInventory(
        workflow_relative=WORKFLOW_RELATIVE,
        workflow_text=text,
        permissions=dict(data.get("permissions") or {}),
    )
    for name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        inv.job_names.append(str(name))
        inv.job_bodies[str(name)] = _flatten_run_text(job)
    inv.job_names.sort()
    inv.classifications = classify_jobs(inv)
    return inv


def classify_jobs(inv: WorkflowInventory) -> dict[str, str]:
    """Map jobs and surfaces to Slice 12.9 classification labels."""
    out: dict[str, str] = {}
    for name in inv.job_names:
        lower_name = name.lower()
        if "cursor" in lower_name and name not in REQUIRED_CI_JOBS:
            out[name] = "remove_cursor_ci"
        elif name == "engine-tests":
            out[name] = "preserve_engine_ci"
        elif name == "platform-tests":
            out[name] = "preserve_platform_ci"
        elif name == "vscode-ci":
            out[name] = "preserve_vscode_ci"
        elif name == "insights-ci":
            out[name] = "preserve_insights_ci"
        elif name == "reports-ci":
            out[name] = "preserve_reports_ci"
        elif name == "community-export-verification":
            out[name] = "add_community_export_verification"
        elif name == "infrastructure-export-verification":
            out[name] = "add_infrastructure_export_verification"
        elif name == "ci-release-boundaries":
            out[name] = "preserve_release_verification"
        else:
            out[name] = "documentation_only"
    out["scripts/export_repository.py"] = "add_community_export_verification"
    out["scripts/export_infrastructure_repository.py"] = (
        "add_infrastructure_export_verification"
    )
    out["scripts/export-public-repos.py"] = "add_community_export_verification"
    out["infrastructure/ source in monorepo"] = "preserve_infrastructure_source_ci"
    out["Slice 12.10"] = "Slice_12_10_completion_only"
    out["OpenTofu plan/apply/destroy"] = "unsafe_ci_operation"
    out["AWS configure-aws-credentials in export jobs"] = "unsafe_ci_operation"
    out["deployment workflows (if separate)"] = "deployment_job_existing_out_of_scope"
    return out


def check_workflow_inventory(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], WorkflowInventory | None]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    inv = load_primary_workflow(monorepo)

    checks.append(
        CheckResult(
            "workflow:exists",
            inv is not None,
            WORKFLOW_RELATIVE,
            "workflow_inventory",
        )
    )
    if inv is None:
        defects.append(
            Defect(
                "workflow inventory defect",
                WORKFLOW_RELATIVE,
                "present and parseable",
                "missing_or_unparseable",
            )
        )
        return checks, defects, None

    present = set(inv.job_names)
    required = set(REQUIRED_CI_JOBS)
    checks.append(
        CheckResult(
            "workflow:required_jobs",
            required.issubset(present),
            f"have={sorted(present)} need={sorted(required)}",
            "workflow_inventory",
        )
    )
    if not required.issubset(present):
        defects.append(
            Defect(
                "workflow inventory defect",
                "jobs",
                ",".join(sorted(required)),
                ",".join(sorted(present)),
            )
        )

    checks.append(
        CheckResult(
            "workflow:top_level_contents_read",
            inv.permissions.get("contents") == "read",
            str(inv.permissions),
            "workflow_inventory",
        )
    )
    return checks, defects, inv
