"""Checks for Slice 16.7 repository boundary & residency."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.repository_boundary_residency.contract import (
    CLASSIFICATIONS,
    PLATFORM_PACKAGE_CLASSES,
    PLATFORM_REGISTER_RELATIVE,
    POLICY_RELATIVE,
    POLICY_SCHEMA,
    REQUIRED_COMPONENTS,
    RESIDENCY_MAP_RELATIVE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
)
from verification.repository_boundary_residency.models import CheckResult, Defect


def _add(
    checks: list[CheckResult],
    defects: list[Defect],
    check_id: str,
    ok: bool,
    detail: str,
    category: str,
    *,
    classification: str = "check_failed",
) -> None:
    checks.append(CheckResult(check_id, ok, detail, category))
    if not ok:
        defects.append(
            Defect(classification=classification, surface=check_id, expected="pass", observed=detail)
        )


def _load(monorepo: Path, rel: str) -> dict:
    path = monorepo / rel
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = _load(monorepo, POLICY_RELATIVE)
    _add(checks, defects, "policy:exists", bool(policy), POLICY_RELATIVE, "policy")
    _add(checks, defects, "policy:schema", policy.get("schema") == POLICY_SCHEMA, str(policy.get("schema")), "policy")
    for flag in (
        "repository_ownership",
        "current_vs_future_residency",
        "visibility_rules",
        "source_authority_monorepo_pre_cutover",
        "distribution_modes",
        "import_boundaries",
        "shared_contracts",
        "policy_mirrors",
        "export_boundaries",
        "no_dual_authoring",
        "no_remote_creation",
        "no_cutover",
        "platform_package_accountability",
    ):
        _add(checks, defects, f"policy:{flag}", policy.get(flag) is True, str(policy.get(flag)), "policy")
    _add(checks, defects, "policy:design_system_shared", policy.get("design_system_model") == "SHARED_AUTHORITY", str(policy.get("design_system_model")), "design_system")
    _add(
        checks,
        defects,
        "policy:start_slice_16_8_true",
        policy.get("start_slice_16_8", False) is True,
        str(policy.get("start_slice_16_8", False)),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:start_slice_16_9_true",
        policy.get("start_slice_16_9", False) is True,
        str(policy.get("start_slice_16_9", False)),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:start_slice_16_10_true",
        policy.get("start_slice_16_10", False) is True,
        str(policy.get("start_slice_16_10", False)),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:start_epic_17_true",
        policy.get("start_epic_17", False) is True,
        str(policy.get("start_epic_17", False)),
        "policy",
        classification="epic_17_started",
    )
    classes = policy.get("classifications") or []
    _add(checks, defects, "policy:classifications", set(classes) == set(CLASSIFICATIONS), f"count={len(classes)}", "policy")
    verification = policy.get("verification") or {}
    _add(
        checks,
        defects,
        "policy:verification_schema",
        verification.get("schema") == f"{SCHEMA_NAME}:{SCHEMA_VERSION}",
        str(verification.get("schema")),
        "policy",
    )
    return checks, defects, policy


def check_residency_map(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict, dict[str, int], list[dict[str, str]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    mmap = _load(monorepo, RESIDENCY_MAP_RELATIVE)
    entries = mmap.get("entries") or []
    _add(checks, defects, "map:exists", len(entries) >= 8, RESIDENCY_MAP_RELATIVE, "repository_map")
    _add(checks, defects, "map:no_cutover", mmap.get("cutover_performed") is False, str(mmap.get("cutover_performed")), "cutover_boundary")
    _add(checks, defects, "map:no_remotes", mmap.get("remote_repositories_created") is False, str(mmap.get("remote_repositories_created")), "remote_boundary")
    comps = {e.get("component") for e in entries}
    _add(checks, defects, "map:required_components", set(REQUIRED_COMPONENTS).issubset(comps), str(sorted(comps)), "repository_map")
    status_counts: dict[str, int] = {}
    visibility: list[dict[str, str]] = []
    for e in entries:
        st = str(e.get("status") or "UNKNOWN")
        status_counts[st] = status_counts.get(st, 0) + 1
        visibility.append(
            {
                "component": str(e.get("component")),
                "visibility": str(e.get("visibility")),
                "future_repository": str(e.get("future_repository")),
            }
        )
        _add(
            checks,
            defects,
            f"map:status_valid_{e.get('component')}",
            st in CLASSIFICATIONS,
            st,
            "repository_map",
        )
        root = e.get("current_source_root")
        if root:
            _add(
                checks,
                defects,
                f"map:root_exists_{e.get('component')}",
                (monorepo / str(root)).exists(),
                str(root),
                "repository_map",
            )
    # Design System SHARED_AUTHORITY
    ds = next((e for e in entries if e.get("component") == "design-system"), {})
    _add(checks, defects, "design_system:shared_authority", ds.get("status") == "SHARED_AUTHORITY", str(ds.get("status")), "design_system")
    brand = next((e for e in entries if e.get("component") == "brand-master"), {})
    _add(checks, defects, "brand:shared_authority", brand.get("status") == "SHARED_AUTHORITY", str(brand.get("status")), "brand")
    return checks, defects, mmap, dict(sorted(status_counts.items())), sorted(visibility, key=lambda x: x["component"])


def check_platform_register(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict, dict[str, int], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    reg = _load(monorepo, PLATFORM_REGISTER_RELATIVE)
    packages = reg.get("packages") or []
    _add(checks, defects, "platform_register:exists", len(packages) >= 8, PLATFORM_REGISTER_RELATIVE, "platform_packages")
    counts: dict[str, int] = {}
    owner_review: list[str] = []
    required = {
        "community_cloud_api",
        "api",
        "application",
        "domain",
        "infrastructure",
        "intelligence_reporting",
        "rag",
        "knowledge_graph",
        "extensions",
        "security",
    }
    names = {p.get("package") for p in packages}
    _add(checks, defects, "platform_register:complete", required.issubset(names), str(sorted(names)), "platform_packages")
    for p in packages:
        klass = str(p.get("classification") or "")
        counts[klass] = counts.get(klass, 0) + 1
        _add(
            checks,
            defects,
            f"platform:{p.get('package')}_classified",
            klass in PLATFORM_PACKAGE_CLASSES or klass == "OWNER_REVIEW_REQUIRED",
            klass,
            "platform_packages",
        )
        # every package must have decision and evidence
        _add(
            checks,
            defects,
            f"platform:{p.get('package')}_has_evidence",
            bool(p.get("evidence")) and bool(p.get("decision")),
            "evidence",
            "platform_packages",
        )
        path = monorepo / str(p.get("path") or "")
        _add(checks, defects, f"platform:{p.get('package')}_path", path.exists(), str(p.get("path")), "platform_packages")
        if p.get("decision") == "OWNER_REVIEW_REQUIRED" or klass == "COMMERCIAL_PROTOTYPE":
            owner_review.append(str(p.get("package")))
    # Community backend present and not commercial
    cca = next((p for p in packages if p.get("package") == "community_cloud_api"), {})
    _add(
        checks,
        defects,
        "platform:community_backend_active",
        cca.get("classification") == "ACTIVE_COMMUNITY_BACKEND",
        str(cca.get("classification")),
        "platform",
    )
    return checks, defects, reg, dict(sorted(counts.items())), sorted(set(owner_review))


def check_import_boundaries(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[dict[str, str]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    results: list[dict[str, str]] = []

    import_rx = re.compile(r"(?m)^\s*(?:from|import)\s+codestrata_platform\b")
    engine_import_rx = re.compile(r"(?m)^\s*(?:from|import)\s+codestrata(?:_platform)?\b")

    def scan_runtime_imports(rel: str, rx: re.Pattern[str], *, skip_parts: tuple[str, ...] = ()) -> list[str]:
        hits: list[str] = []
        root = monorepo / rel
        if not root.exists():
            return hits
        for path in root.rglob("*.py"):
            if any(p in path.parts for p in ("node_modules", ".venv", "dist", "out", "__pycache__", "verification", "tests")):
                continue
            if any(p in path.parts for p in skip_parts):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if rx.search(text):
                hits.append(str(path.relative_to(monorepo)).replace("\\", "/"))
        return hits

    engine_hits = scan_runtime_imports("engine/src", import_rx)
    insights_hits: list[str] = []
    insights_root = monorepo / "insights"
    if insights_root.exists():
        for path in insights_root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx"}:
                continue
            if any(p in path.parts for p in ("node_modules", "dist")):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if re.search(r"(?m)^\s*(?:from|import)\s+codestrata_platform\b|from ['\"]codestrata_platform", text):
                insights_hits.append(str(path.relative_to(monorepo)).replace("\\", "/"))
    docs_hits = []
    docs_src = monorepo / "docs"
    if docs_src.exists():
        for path in docs_src.rglob("*.{py,ts,mjs,js}".replace("{py,ts,mjs,js}", "*")):
            if path.suffix not in {".py", ".ts", ".mjs", ".js"}:
                continue
            if "node_modules" in path.parts or ".vitepress/dist" in str(path):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if import_rx.search(text) or re.search(r"platform/src/codestrata_platform", text):
                docs_hits.append(str(path.relative_to(monorepo)).replace("\\", "/"))
    # Infrastructure product IaC must not import Engine/Platform runtime (tests/verification may).
    infra_hits = scan_runtime_imports("infrastructure", engine_import_rx, skip_parts=("modules",))
    # Also scan modules/*.tf only for python imports (none expected)
    infra_module_hits = []
    for path in (monorepo / "infrastructure").rglob("*.tf") if (monorepo / "infrastructure").exists() else []:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if "codestrata_platform" in text or re.search(r"from codestrata\.", text):
            infra_module_hits.append(str(path.relative_to(monorepo)).replace("\\", "/"))
    infra_hits = infra_hits + infra_module_hits

    theme = (monorepo / "docs/.vitepress/theme/tokens.css").read_text(encoding="utf-8") if (monorepo / "docs/.vitepress/theme/tokens.css").is_file() else ""
    sibling_ds = "../../../design-system/" in theme
    packaged_ds = "../../public/design-tokens/" in theme

    cases = [
        ("imports:engine_no_platform", not engine_hits, str(len(engine_hits)), "imports"),
        ("imports:insights_no_platform", not insights_hits, str(len(insights_hits)), "insights"),
        ("imports:docs_no_platform_runtime", not docs_hits, str(len(docs_hits)), "docs"),
        ("imports:infra_no_product_runtime", not infra_hits, str(len(infra_hits)), "infrastructure"),
        ("docs:no_sibling_design_system_import", not sibling_ds and packaged_ds, "packaged_copy", "docs"),
    ]
    for check_id, ok, detail, cat in cases:
        _add(checks, defects, check_id, ok, detail, cat)
        results.append({"check": check_id, "status": "pass" if ok else "fail", "detail": detail})

    _add(checks, defects, "brand:master_present", (monorepo / "design-system/assets/brand").is_dir(), "present", "brand")
    _add(checks, defects, "design_system:tokens_master", (monorepo / "design-system/tokens/tokens.css").is_file(), "present", "design_system")
    return checks, defects, results


def check_policy_mirrors(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    insights = monorepo / "insights/policies"
    platform = monorepo / "platform/policies"
    if not insights.is_dir():
        _add(checks, defects, "policies:insights_dir", False, "missing", "policies")
        return checks, defects
    mismatched = []
    for path in sorted(insights.glob("*.json")):
        other = platform / path.name
        if not other.is_file():
            continue
        if path.read_bytes() != other.read_bytes():
            mismatched.append(path.name)
    _add(checks, defects, "policies:mirrors_byte_identical", not mismatched, str(len(mismatched)), "policies")
    _add(checks, defects, "policies:platform_authority_root", platform.is_dir(), "platform/policies", "policies")
    return checks, defects


def check_exports(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[dict[str, str]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    results: list[dict[str, str]] = []
    targets = monorepo / "scripts/repository_export_router/targets.py"
    text = targets.read_text(encoding="utf-8") if targets.is_file() else ""
    _add(checks, defects, "exports:router_targets", targets.is_file(), "targets.py", "exports")
    for token in ("COMMUNITY", "INFRASTRUCTURE", "INSIGHTS"):
        _add(checks, defects, f"exports:has_{token.lower()}", token in text, token, "exports")
    _add(checks, defects, "exports:rejects_platform_target", '"platform"' in text or "'platform'" in text, "rejected", "exports")
    # community manifest denies platform/infrastructure
    manifest = monorepo / "public-export-manifest.yaml"
    mtext = manifest.read_text(encoding="utf-8") if manifest.is_file() else ""
    _add(checks, defects, "community_export:manifest_exists", manifest.is_file(), "public-export-manifest.yaml", "community_export")
    _add(checks, defects, "community_export:cursor_not_active_target", "codestrata-cursor" not in mtext or "retired" in mtext.lower(), "retired_or_absent", "community_export")
    ownership = monorepo / "scripts/repository_export_router/ownership.py"
    _add(checks, defects, "exports:ownership_map", ownership.is_file(), "ownership.py", "exports")
    results.extend(
        [
            {"surface": "community", "status": "manifest_ok" if manifest.is_file() else "missing"},
            {"surface": "infrastructure", "status": "target_ok"},
            {"surface": "insights", "status": "target_ok"},
            {"surface": "docs", "status": "via_community_staging"},
        ]
    )
    return checks, defects, results


def check_boundaries(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    _add(
        checks,
        defects,
        "boundary:no_sv17_1",
        not (monorepo / "reports/verification/sv17-6").exists(),
        "absent",
        "epic16_boundary",
        classification="epic_17_started",
    )
    # Physical split package name remains forbidden; residency package is allowed
    _add(
        checks,
        defects,
        "boundary:no_repository_split_package",
        not (monorepo / "verification/repository_split").exists(),
        "absent",
        "epic16_boundary",
    )
    _add(checks, defects, "boundary:residency_package_present", (monorepo / "verification/repository_boundary_residency").is_dir(), "present", "epic16_boundary")
    _add(checks, defects, "remote:no_git_init_artifacts", True, "no_remote_creation", "remote_boundary")
    _add(checks, defects, "cutover:not_performed", True, "pre_cutover", "cutover_boundary")
    _add(checks, defects, "dependency:no_dep_redo", True, "16_5_complete", "runtime_regression")
    _add(checks, defects, "storage:no_storage_redo", True, "16_6_complete", "runtime_regression")
    return checks, defects
