"""Repository structure consistency."""

from __future__ import annotations

from pathlib import Path

from verification.repository_consistency.contract import (
    FORBIDDEN_TOP_LEVEL,
    REQUIRED_TOP_LEVEL,
)
from verification.repository_consistency.inventory import add_check
from verification.repository_consistency.models import CheckResult, Defect

# Declared purpose for odd/additional top-level entries (not product runtimes).
ADDITIONAL_CLASSIFIED = {
    "knowledge": "Community engineering knowledge foundation (not product runtime)",
    "reports": "Generated verification and report outputs",
    "test-fixtures": "Tracked test fixtures",
    "examples": "Pinned real-world Engine showcases",
    "governance": "Governance archives and historical assets",
    "validation": "Validation tooling and fixtures",
    "scripts": "Monorepo scripts and exporters",
    "tests": "Repository tests",
}


def check_structure(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[dict[str, str]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    top_map: list[dict[str, str]] = []

    for name in REQUIRED_TOP_LEVEL:
        p = monorepo / name
        ok = p.is_dir()
        add_check(checks, defects, f"structure:required:{name}", ok, name, "structure")
        top_map.append(
            {
                "path": f"{name}/",
                "kind": "required",
                "purpose": ADDITIONAL_CLASSIFIED.get(name, f"declared product/engineering area: {name}"),
                "status": "present" if ok else "missing",
            }
        )

    for name in FORBIDDEN_TOP_LEVEL:
        exists = (monorepo / name).exists()
        add_check(
            checks,
            defects,
            f"structure:forbidden_absent:{name}",
            not exists,
            name,
            "structure",
            classification="stale_product_root",
        )

    # No AIMF active product root
    aimf_roots = [p.name for p in monorepo.iterdir() if p.is_dir() and "aimf" in p.name.lower()]
    add_check(
        checks,
        defects,
        "structure:no_aimf_product_root",
        not aimf_roots,
        ",".join(aimf_roots) or "none",
        "structure",
    )

    # Accidental temp/build roots at top level
    bad_temp = []
    for p in monorepo.iterdir():
        if not p.is_dir():
            continue
        n = p.name.lower()
        if n in {".export-staging", "export-staging", "dist", "build", "out", "coverage", ".tox"}:
            bad_temp.append(p.name)
        if n.endswith(".egg-info") or n.endswith(".vsix"):
            bad_temp.append(p.name)
    add_check(
        checks,
        defects,
        "structure:no_accidental_temp_build_roots",
        not bad_temp,
        ",".join(bad_temp) or "none",
        "structure",
    )

    # Classify remaining top-level dirs
    known = set(REQUIRED_TOP_LEVEL) | set(FORBIDDEN_TOP_LEVEL) | {
        "knowledge",
        "reports",
        "test-fixtures",
        ".git",
        ".github",
        ".venv",
        "venv",
        "node_modules",
        ".cursor",
        ".codestrata-examples",
    }
    unexplained = []
    for p in sorted(monorepo.iterdir()):
        if not p.is_dir() or p.name.startswith("."):
            continue
        if p.name in known or p.name in REQUIRED_TOP_LEVEL:
            if p.name in {"knowledge", "reports", "test-fixtures"}:
                top_map.append(
                    {
                        "path": f"{p.name}/",
                        "kind": "classified_additional",
                        "purpose": ADDITIONAL_CLASSIFIED.get(p.name, "classified"),
                        "status": "present",
                    }
                )
            continue
        # skip common tooling dirs already known
        if p.name in {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}:
            continue
        unexplained.append(p.name)
        top_map.append(
            {
                "path": f"{p.name}/",
                "kind": "unexplained",
                "purpose": "needs_classification",
                "status": "present",
            }
        )
    add_check(
        checks,
        defects,
        "structure:no_unexplained_product_dirs",
        not unexplained,
        ",".join(unexplained) or "none",
        "structure",
    )
    return checks, defects, top_map
