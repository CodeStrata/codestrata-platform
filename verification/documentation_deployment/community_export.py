"""Community export manifest checks for codestrata-docs."""

from __future__ import annotations

from verification.documentation_deployment.contract import DOCS_ROOT, EXPORT_MANIFEST
from verification.documentation_deployment.inventory import DeploymentInventory
from verification.documentation_deployment.models import CheckResult

REQUIRED_EXPORT_FILES = (
    "wrangler.jsonc",
    "policies/documentation_deployment_policy.json",
    "scripts/deploy-check.mjs",
    "DEPLOYMENT.md",
)


def _docs_export_entry(manifest: dict) -> dict | None:
    for entry in manifest.get("exports", []):
        if entry.get("name") == "codestrata-docs":
            return entry
    return None


def check_community_export(inv: DeploymentInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    entry = _docs_export_entry(inv.export_manifest)

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, "community_export"))

    add(
        "community_export:manifest_present",
        bool(inv.export_manifest),
        EXPORT_MANIFEST if inv.export_manifest else "missing",
    )
    add(
        "community_export:entry_exists",
        entry is not None,
        "codestrata-docs" if entry else "missing",
    )
    if entry:
        add(
            "community_export:source_root_docs",
            entry.get("source_root") == DOCS_ROOT,
            str(entry.get("source_root")),
        )
        add(
            "community_export:flat_layout",
            entry.get("destination_layout") == "flat",
            str(entry.get("destination_layout")),
        )
        require_files = entry.get("validation", {}).get("require_files", [])
        for rel in REQUIRED_EXPORT_FILES:
            add(
                f"community_export:require_{rel.replace('/', '_').replace('.', '_')}",
                rel in require_files,
                rel,
            )
    else:
        for rel in REQUIRED_EXPORT_FILES:
            add(f"community_export:require_{rel.replace('/', '_').replace('.', '_')}", False, rel)

    for rel in REQUIRED_EXPORT_FILES:
        add(
            f"community_export:file_exists_{rel.replace('/', '_').replace('.', '_')}",
            (inv.docs_root / rel).is_file(),
            rel,
        )
    return checks
