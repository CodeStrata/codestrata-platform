"""Infrastructure source inventory and classification (Slice 12.5)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.infrastructure_repository_contract.contract import (
    OPTIONAL_ALLOWLIST,
    PROHIBITED_CATEGORIES,
    REQUIRED_ALLOWLIST,
    VALIDATION_ROOTS,
)
from verification.infrastructure_repository_contract.models import CheckResult, Defect

# Deterministic classified inventory (relative monorepo paths / categories).
CLASSIFIED_ENTRIES: tuple[dict[str, str], ...] = (
    {"path": "infrastructure/modules/", "class": "export_required"},
    {"path": "infrastructure/production/", "class": "export_required"},
    {"path": "infrastructure/tests/", "class": "export_required"},
    {"path": "infrastructure/verification/", "class": "export_required"},
    {"path": "infrastructure/docs/", "class": "export_required"},
    {"path": "infrastructure/policies/", "class": "export_required"},
    {"path": "infrastructure/scripts/", "class": "export_required"},
    {"path": "infrastructure/README.md", "class": "export_required"},
    {"path": "infrastructure/__init__.py", "class": "export_required"},
    {"path": "infrastructure/.gitignore", "class": "export_required"},
    {"path": "infrastructure/docs/repository-contract.md", "class": "export_required"},
    {"path": "infrastructure/production/backend.tf.example", "class": "export_optional"},
    {
        "path": "infrastructure/production/terraform.tfvars.example",
        "class": "export_optional",
    },
    {"path": "infrastructure/**/.terraform.lock.hcl", "class": "export_optional"},
    {"path": "infrastructure/reports/", "class": "generated_not_exported"},
    {"path": "infrastructure/**/__pycache__/", "class": "generated_not_exported"},
    {"path": "infrastructure/**/.terraform/", "class": "secret_or_state_forbidden"},
    {"path": "infrastructure/**/*.tfstate", "class": "secret_or_state_forbidden"},
    {"path": "infrastructure/**/*.tfplan", "class": "secret_or_state_forbidden"},
    {"path": "engine/", "class": "source_repository_only"},
    {"path": "platform/", "class": "source_repository_only"},
    {"path": "vscode-plugin/", "class": "source_repository_only"},
    {"path": "public-export-manifest.yaml", "class": "source_repository_only"},
    {
        "path": "infrastructure/tests/verification/test_boundary.py#platform_engine_imports",
        "class": "shared_contract_to_reimplement",
    },
    {
        "path": "platform/docs/community-cloud-api/* (from infra docs)",
        "class": "documentation_link_to_update_later",
    },
    {"path": ".github/workflows Infrastructure jobs", "class": "CI_reference_deferred_to_12_9"},
    {"path": "scripts/release Infrastructure refs", "class": "release_reference_deferred_to_12_9"},
    {"path": "owner migration runbook", "class": "migration_runbook_reference_deferred"},
)


def build_classification() -> dict[str, Any]:
    by_class: dict[str, list[str]] = {}
    for item in CLASSIFIED_ENTRIES:
        by_class.setdefault(item["class"], []).append(item["path"])
    return {
        "by_class": {k: sorted(v) for k, v in sorted(by_class.items())},
        "entries": sorted(CLASSIFIED_ENTRIES, key=lambda x: (x["class"], x["path"])),
    }


def required_source_inventory() -> list[str]:
    return sorted(REQUIRED_ALLOWLIST)


def optional_source_inventory() -> list[str]:
    return sorted(OPTIONAL_ALLOWLIST)


def excluded_category_inventory() -> list[str]:
    return sorted(PROHIBITED_CATEGORIES)


def validation_roots() -> list[str]:
    return sorted(VALIDATION_ROOTS)


def check_inventory(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    infra = monorepo / "infrastructure"
    required_dirs = (
        "modules",
        "production",
        "tests",
        "verification",
        "docs",
        "policies",
        "scripts",
    )
    for name in required_dirs:
        path = infra / name
        ok = path.is_dir()
        checks.append(
            CheckResult(
                name=f"inventory:dir_{name}",
                ok=ok,
                detail=f"infrastructure/{name}/",
                category="inventory",
            )
        )
        if not ok:
            defects.append(
                Defect("inventory defect", f"infrastructure/{name}", "present", "missing")
            )

    for rel in (
        "README.md",
        "__init__.py",
        ".gitignore",
        "docs/repository-contract.md",
        "modules/community-cloud-api",
        "modules/community-data-lake",
        "production/main.tf",
        "production/community-data-lake.tf",
        "scripts/validate.sh",
    ):
        path = infra / rel
        ok = path.exists()
        checks.append(
            CheckResult(
                name=f"inventory:path_{rel.replace('/', '_')}",
                ok=ok,
                detail=rel,
                category="inventory",
            )
        )
        if not ok:
            defects.append(
                Defect("inventory defect", rel, "present", "missing")
            )

    classification = build_classification()
    checks.append(
        CheckResult(
            name="inventory:classified_entries",
            ok=len(CLASSIFIED_ENTRIES) >= 20,
            detail=f"entries={len(CLASSIFIED_ENTRIES)} classes={len(classification['by_class'])}",
            category="inventory",
        )
    )
    return checks, defects


def check_classification(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    _ = monorepo
    classification = build_classification()
    checks = [
        CheckResult(
            name=f"classification:{name}",
            ok=True,
            detail=f"count={len(paths)}",
            category="classification",
        )
        for name, paths in classification["by_class"].items()
    ]
    # Must not classify engine/platform as export_required
    export_required = set(classification["by_class"].get("export_required", []))
    bad = [p for p in export_required if p.startswith(("engine/", "platform/", "vscode-plugin/"))]
    defects: list[Defect] = []
    checks.append(
        CheckResult(
            name="classification:no_product_runtime_in_export_required",
            ok=not bad,
            detail=f"bad={len(bad)}",
            category="classification",
        )
    )
    if bad:
        defects.append(
            Defect(
                "allowlist defect",
                "classification",
                "no product runtime",
                ",".join(bad),
            )
        )
    return checks, defects
