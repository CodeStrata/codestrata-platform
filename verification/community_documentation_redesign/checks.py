"""Focused checks for Slice 14.2 Community documentation redesign."""

from __future__ import annotations

import json
from pathlib import Path

from verification.community_documentation_redesign.contract import (
    DESIGN_SYSTEM_TOKENS,
    DOCS_ROOT,
    FORBIDDEN_14_8_PATHS,
    FORBIDDEN_NAV_FRAGMENTS,
    POLICY_ID,
    POLICY_VERSION,
    REQUIRED_COMMUNITY_ROUTES,
)
from verification.community_documentation_redesign.models import CheckResult, Defect


def _add(
    checks: list[CheckResult],
    name: str,
    ok: bool,
    detail: str,
    category: str,
) -> None:
    checks.append(CheckResult(name=name, ok=ok, detail=detail, category=category))


def _read(monorepo: Path, rel: str) -> str:
    return (monorepo / rel).read_text(encoding="utf-8")


def check_all(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    meta = {
        "design_system_consumed": False,
        "community_only_scope": False,
    }

    policy_path = f"{DOCS_ROOT}/policies/community_documentation_redesign_policy.json"
    policy = json.loads(_read(monorepo, policy_path))
    _add(
        checks,
        "policy:id_version",
        policy.get("policy_id") == POLICY_ID
        and policy.get("policy_version") == POLICY_VERSION,
        f"{POLICY_ID}:{POLICY_VERSION}",
        "policy",
    )
    _add(
        checks,
        "policy:start_14_3_false",
        policy.get("start_slice_14_3") is False,
        "false",
        "slice_14_3",
    )
    _add(
        checks,
        "policy:no_adjacent_redesigns",
        policy.get("assessment_html_redesign_allowed") is False
        and policy.get("engineering_intelligence_report_redesign_allowed") is False
        and policy.get("vscode_redesign_allowed") is False
        and policy.get("marketplace_redesign_allowed") is False,
        "guarded",
        "no_product_redesign",
    )

    tokens_bridge = _read(monorepo, f"{DOCS_ROOT}/.vitepress/theme/tokens.css")
    ds_tokens = _read(monorepo, DESIGN_SYSTEM_TOKENS)
    consumes = "design-system/tokens/tokens.css" in tokens_bridge
    meta["design_system_consumed"] = consumes
    _add(checks, "tokens:import_design_system", consumes, "imported", "tokens")
    _add(
        checks,
        "tokens:no_amber_authority_redeclare",
        "--amber: #d98a3d" not in tokens_bridge,
        "no_duplicate_amber",
        "tokens",
    )
    _add(
        checks,
        "tokens:cs_teal_in_design_system",
        "--cs-teal-dark: #0f5d54" in ds_tokens,
        "teal_dark",
        "tokens",
    )
    _add(
        checks,
        "tokens:vp_brand_mapped",
        "--vp-c-brand-1: var(--cs-teal-dark)" in tokens_bridge
        or "--vp-c-brand-1: var(--cs-teal" in tokens_bridge,
        "mapped",
        "tokens",
    )

    config = _read(monorepo, f"{DOCS_ROOT}/.vitepress/config.ts")
    _add(
        checks,
        "nav:srcExclude_platform",
        "platform/**" in config,
        "excluded",
        "navigation",
    )
    _add(
        checks,
        "nav:srcExclude_vs_platform",
        "community/vs-platform.md" in config,
        "excluded",
        "navigation",
    )
    forbidden_hits = [f for f in FORBIDDEN_NAV_FRAGMENTS if f in config]
    _add(
        checks,
        "nav:no_forbidden_fragments",
        not forbidden_hits,
        "clean" if not forbidden_hits else ",".join(forbidden_hits),
        "navigation",
    )
    # Active nav must not include Platform; exclusion of historical files is required.
    community_ok = (
        'link: "/platform/"' not in config
        and 'link: "/community/vs-platform"' not in config
        and 'text: "Platform"' not in config
        and "platform/**" in config
        and "community/vs-platform.md" in config
    )
    meta["community_only_scope"] = community_ok
    _add(checks, "scope:community_only", community_ok, "community", "navigation")

    for route in REQUIRED_COMMUNITY_ROUTES:
        # Map route to file
        if route.endswith("/"):
            rel = f"{DOCS_ROOT}/{route}index.md"
        else:
            rel = f"{DOCS_ROOT}/{route}.md"
        ok = (monorepo / rel).is_file()
        _add(checks, f"content:route:{route.replace('/', '_')}", ok, rel, "navigation")
        if not ok:
            defects.append(
                Defect("content defect", rel, "present", "missing")
            )

    custom = _read(monorepo, f"{DOCS_ROOT}/.vitepress/theme/custom.css")
    components = _read(monorepo, f"{DOCS_ROOT}/.vitepress/theme/components.css")
    _add(
        checks,
        "components:cards_buttons_callouts",
        ".cs-card" in components
        and ".btn--primary" in components
        and ".cs-callout" in components
        and ".cs-footer" in custom,
        "present",
        "components",
    )
    _add(
        checks,
        "typography:display_face",
        "--cs-font-display" in tokens_bridge
        and "Space Grotesk" in ds_tokens,
        "display",
        "typography",
    )
    _add(
        checks,
        "a11y:focus_and_reduced_motion",
        ":focus-visible" in tokens_bridge
        and "prefers-reduced-motion" in tokens_bridge,
        "defined",
        "accessibility",
    )
    _add(
        checks,
        "responsive:mobile_breakpoint",
        "max-width: 720px" in custom or "720px" in custom,
        "mobile",
        "responsive",
    )
    _add(
        checks,
        "mobile:footer_stack",
        "@media (max-width: 720px)" in custom,
        "stack",
        "mobile",
    )
    _add(
        checks,
        "dark_mode:theme_block",
        'html[data-theme="dark"]' in tokens_bridge or "html.dark" in tokens_bridge,
        "supported",
        "dark_mode",
    )
    theme_idx = _read(monorepo, f"{DOCS_ROOT}/.vitepress/theme/index.ts")
    _add(
        checks,
        "dark_mode:sync_theme_color",
        "#101a17" in theme_idx and "#f4f6f3" in theme_idx,
        "synced",
        "dark_mode",
    )

    home = _read(monorepo, f"{DOCS_ROOT}/index.md")
    _add(
        checks,
        "landing:tagline",
        "Engineering decisions grounded in code" in home,
        "tagline",
        "components",
    )
    _add(
        checks,
        "landing:community_only_claim",
        "Community Edition" in home and "/platform/" not in home,
        "community",
        "navigation",
    )

    # No adjacent product redesigns in this slice
    for rel in (
        "engine/src/codestrata/reporting/html/design_system_v2",
        "vscode-plugin/src/designSystemRuntime",
    ):
        exists = (monorepo / rel).exists()
        _add(
            checks,
            f"no_redesign:absent:{Path(rel).name}",
            not exists,
            "absent",
            "no_product_redesign",
        )

    for rel in FORBIDDEN_14_8_PATHS:
        exists = (monorepo / rel).exists()
        _add(
            checks,
            f"slice_14_8:absent:{Path(rel).name}",
            not exists,
            "absent",
            "slice_14_8",
        )

    arch = _read(monorepo, "ARCHITECTURE.md") if (monorepo / "ARCHITECTURE.md").is_file() else ""
    # Soft: 14.8 must remain explicitly not started when mentioned
    ok_14_8 = "Slice 14.8 not started" in arch or "Slice 14.8" not in arch
    _add(checks, "slice_14_8:architecture_posture", ok_14_8, "ok", "slice_14_8")

    # Historical platform file may remain but must be excluded
    _add(
        checks,
        "historical:platform_md_excluded",
        (monorepo / "docs/platform/index.md").is_file() and "platform/**" in config,
        "excluded",
        "navigation",
    )

    return checks, defects, meta


def release_posture() -> dict:
    return {
        "slice_14_2_complete": True,
        "slice_14_3_started": False,
        "slice_14_8_started": False,
        "assessment_html_redesign_performed": False,
        "engineering_intelligence_redesign_performed": False,
        "vscode_redesign_performed": False,
        "marketplace_redesign_performed": False,
        "commit_created": False,
        "tag_created": False,
        "published": False,
        "deployed": False,
    }
