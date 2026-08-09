"""Static checks for Slice 16.2 documentation verification."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.repository_documentation.contract import (
    CLASSIFICATIONS,
    CLEANUP_GUIDE,
    POLICY_ID,
    POLICY_RELATIVE,
    POLICY_SCHEMA,
    POLICY_VERSION,
    SCHEMA_NAME,
    SCHEMA_VERSION,
)
from verification.repository_documentation.models import CheckResult, Defect, DocEntry


def _add(
    checks: list[CheckResult],
    defects: list[Defect],
    check_id: str,
    ok: bool,
    detail: str,
    category: str,
    *,
    classification: str = "documentation",
) -> None:
    checks.append(CheckResult(check_id, ok, detail, category))
    if not ok:
        defects.append(
            Defect(
                classification=classification,
                surface=check_id,
                expected="pass",
                observed=detail,
            )
        )


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / POLICY_RELATIVE
    _add(checks, defects, "policy:exists", path.is_file(), POLICY_RELATIVE, "policy")
    policy: dict = {}
    if path.is_file():
        policy = json.loads(path.read_text(encoding="utf-8"))
    _add(checks, defects, "policy:id", policy.get("policy_id") == POLICY_ID, str(policy.get("policy_id")), "policy")
    _add(
        checks,
        defects,
        "policy:version",
        str(policy.get("policy_version")) == POLICY_VERSION,
        str(policy.get("policy_version")),
        "policy",
    )
    _add(checks, defects, "policy:schema", policy.get("schema") == POLICY_SCHEMA, str(policy.get("schema")), "policy")
    _add(
        checks,
        defects,
        "policy:documentation_only",
        policy.get("documentation_only") is True,
        str(policy.get("documentation_only")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:product_version_0_2_0",
        str(policy.get("product_version")) == "0.2.0",
        str(policy.get("product_version")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:start_slice_16_5_true",
        policy.get("start_slice_16_5", False) is True,
        str(policy.get("start_slice_16_5", False)),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:start_slice_16_6_true",
        policy.get("start_slice_16_6", False) is True,
        str(policy.get("start_slice_16_6", False)),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:start_slice_16_7_true",
        policy.get("start_slice_16_7", False) is True,
        str(policy.get("start_slice_16_7", False)),
        "policy",
    )
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
    _add(
        checks,
        defects,
        "policy:classifications_complete",
        set(classes) == set(CLASSIFICATIONS),
        f"count={len(classes)}",
        "policy",
    )
    registry = policy.get("authoritative_document_registry") or {}
    required_keys = (
        "readme",
        "installation",
        "release",
        "documentation_hierarchy",
        "design_system",
        "privacy_community",
    )
    missing = [k for k in required_keys if k not in registry]
    _add(
        checks,
        defects,
        "policy:registry_keys",
        not missing,
        "ok" if not missing else ",".join(missing),
        "policy",
    )
    verification = policy.get("verification") or {}
    _add(
        checks,
        defects,
        "policy:verification_schema",
        verification.get("schema") == f"{SCHEMA_NAME}:{SCHEMA_VERSION}",
        str(verification.get("schema")),
        "policy",
    )
    guide = monorepo / CLEANUP_GUIDE
    _add(checks, defects, "policy:cleanup_guide_exists", guide.is_file(), CLEANUP_GUIDE, "policy")
    return checks, defects, policy


def check_authorities(monorepo: Path, registry: dict) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    for key, rel in sorted(registry.items()):
        path = monorepo / rel
        # hierarchy keys may be directories
        ok = path.exists()
        _add(checks, defects, f"authority:{key}", ok, rel, "authority")

    readme = (monorepo / "README.md").read_text(encoding="utf-8", errors="ignore")
    _add(
        checks,
        defects,
        "authority:readme_version_0_2_0",
        "0.2.0" in readme and "0.1.0" not in readme.split("Version")[1][:40] if "Version" in readme else "0.2.0" in readme,
        "readme_version",
        "authority",
    )
    _add(
        checks,
        defects,
        "authority:readme_points_install",
        "docs/getting-started/install.md" in readme,
        "install_link",
        "authority",
    )
    install = monorepo / "docs/getting-started/install.md"
    _add(checks, defects, "authority:install_exists", install.is_file(), "docs/getting-started/install.md", "authority")
    changelog = monorepo / "CHANGELOG.md"
    _add(checks, defects, "authority:changelog_exists", changelog.is_file(), "CHANGELOG.md", "authority")
    _add(checks, defects, "authority:docs_hierarchy", (monorepo / "docs").is_dir(), "docs/", "authority")
    return checks, defects


def check_identity_and_links(
    *,
    identity_hits: list[str],
    broken_links: list[str],
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    _add(
        checks,
        defects,
        "identity:no_aimf_or_cursor_product_in_active_docs",
        len(identity_hits) == 0,
        "none" if not identity_hits else ",".join(identity_hits[:12]),
        "identity",
    )
    # Broken unpublished platform routes from active community docs are failures
    hard = [b for b in broken_links if "unpublished_platform_route" in b or "escapes_repo" in b]
    soft = [b for b in broken_links if b not in hard]
    _add(
        checks,
        defects,
        "links:no_hard_broken_refs",
        len(hard) == 0,
        "none" if not hard else ",".join(hard[:12]),
        "links",
    )
    _add(
        checks,
        defects,
        "links:soft_broken_catalogued",
        True,
        f"soft_count={len(soft)}",
        "links",
    )
    return checks, defects


def check_boundaries(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    config = monorepo / "docs/.vitepress/config.ts"
    text = config.read_text(encoding="utf-8") if config.is_file() else ""
    _add(checks, defects, "boundary:vitepress_excludes_platform", "platform/**" in text, "srcExclude", "boundary")
    _add(checks, defects, "boundary:vitepress_excludes_internal", "internal/**" in text, "srcExclude", "boundary")
    platform_index = monorepo / "docs/platform/index.md"
    ptext = platform_index.read_text(encoding="utf-8") if platform_index.is_file() else ""
    _add(
        checks,
        defects,
        "boundary:platform_docs_marked_archive",
        "ARCHIVE" in ptext.upper() or "UNPUBLISHED" in ptext.upper(),
        "docs/platform/index.md",
        "boundary",
    )
    plat_readme = monorepo / "platform/docs/README.md"
    pr = plat_readme.read_text(encoding="utf-8") if plat_readme.is_file() else ""
    _add(
        checks,
        defects,
        "boundary:platform_docs_marked_internal",
        "INTERNAL" in pr.upper(),
        "platform/docs/README.md",
        "boundary",
    )
    findings = monorepo / "docs/reports/findings.md"
    ft = findings.read_text(encoding="utf-8") if findings.is_file() else ""
    _add(
        checks,
        defects,
        "boundary:findings_no_cursor_extensions",
        "Cursor extensions" not in ft and "Cursor extension" not in ft,
        "docs/reports/findings.md",
        "boundary",
    )
    sv166 = monorepo / "reports/verification/sv17-6"
    _add(
        checks,
        defects,
        "boundary:no_sv17_1",
        not sv166.exists(),
        "absent",
        "boundary",
        classification="epic_17_started",
    )
    root_security = monorepo / "SECURITY.md"
    root_coc = monorepo / "CODE_OF_CONDUCT.md"
    _add(checks, defects, "boundary:root_security_pointer", root_security.is_file(), "SECURITY.md", "boundary")
    _add(checks, defects, "boundary:root_coc_pointer", root_coc.is_file(), "CODE_OF_CONDUCT.md", "boundary")
    return checks, defects


def check_inventory(entries: list[DocEntry]) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    _add(checks, defects, "inventory:non_empty", len(entries) > 0, str(len(entries)), "inventory")
    unknown = sorted({e.classification for e in entries} - set(CLASSIFICATIONS))
    _add(
        checks,
        defects,
        "inventory:known_classifications",
        not unknown,
        "ok" if not unknown else ",".join(unknown),
        "inventory",
    )
    active = sum(1 for e in entries if e.classification == "ACTIVE")
    _add(checks, defects, "inventory:has_active", active > 0, str(active), "inventory")
    return checks, defects


def check_readme_no_stale_version(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    text = (monorepo / "README.md").read_text(encoding="utf-8")
    # Table version cell
    m = re.search(r"\|\s*Version\s*\|\s*\*?\*?(0\.\d+\.\d+)", text)
    version = m.group(1) if m else ""
    _add(checks, defects, "readme:version_is_0_2_0", version == "0.2.0", version or "missing", "authority")
    return checks, defects
