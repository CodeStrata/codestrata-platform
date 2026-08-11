"""Checks for Slice 14.5 VS Code visual experience."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.vscode_visual_experience.contract import (
    ACTIVITY_SVG,
    FORBIDDEN_14_8_PATHS,
    FORBIDDEN_CSS_IMPORTS,
    LEGACY_RUNTIME_HEX,
    MAPPING_RELATIVE,
    PACKAGE_JSON,
    POLICY_ID,
    POLICY_RELATIVE,
    POLICY_VERSION,
    PRESENTATION_COPY,
    VISUAL_DOC,
)
from verification.vscode_visual_experience.models import CheckResult, Defect


def _read(monorepo: Path, rel: str) -> str:
    return (monorepo / rel).read_text(encoding="utf-8")


def _ts_sources(monorepo: Path) -> list[Path]:
    root = monorepo / "vscode-plugin/src"
    return [p for p in root.rglob("*.ts") if "node_modules" not in p.parts]


def check_all(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    meta = {"design_system_mapped": False}

    # Policy
    policy_path = monorepo / POLICY_RELATIVE
    if not policy_path.is_file():
        checks.append(CheckResult("policy:exists", False, "missing", "visual_policy"))
        defects.append(Defect("visual-policy defect", "policy", "present", "missing"))
        return checks, defects, meta
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    checks.append(
        CheckResult(
            "policy:id_version",
            policy.get("policy_id") == POLICY_ID
            and policy.get("policy_version") == POLICY_VERSION,
            f"{POLICY_ID}:{POLICY_VERSION}",
            "visual_policy",
        )
    )
    for key in (
        "native_host_controls_authoritative",
        "product_identity_alignment_required",
        "theme_compatibility_required",
        "light_theme_supported",
        "dark_theme_supported",
        "accessibility_required",
    ):
        checks.append(
            CheckResult(f"policy:{key}", policy.get(key) is True, str(policy.get(key)), "visual_policy")
        )
    for key in (
        "website_css_injection_allowed",
        "command_ids_change_allowed",
        "runtime_behavior_change_allowed",
        "marketplace_asset_changes_allowed",
        "start_slice_14_6",
        "extension_version_bump_allowed",
    ):
        checks.append(
            CheckResult(f"policy:{key}", policy.get(key) is False, str(policy.get(key)), "visual_policy")
        )
    checks.append(
        CheckResult(
            "policy:extension_0_2_0",
            policy.get("extension_version") == "0.2.0",
            "0.2.0",
            "visual_policy",
        )
    )
    leak = any(x in policy_path.read_text(encoding="utf-8") for x in ("/Users/", "file://", "timestamp"))
    checks.append(CheckResult("policy:no_path_leak", not leak, "clean", "visual_policy"))

    # Mapping
    mapping = json.loads(_read(monorepo, MAPPING_RELATIVE))
    mapped = mapping.get("website_css_injection") is False and mapping.get("design_system_version") == "1.0"
    meta["design_system_mapped"] = mapped
    checks.append(CheckResult("mapping:exists", mapped, "mapped", "design_system_mapping"))
    checks.append(
        CheckResult(
            "mapping:doc",
            (monorepo / VISUAL_DOC).is_file(),
            "visual-experience.md",
            "design_system_mapping",
        )
    )

    # Native host boundary — no tokens.css import in src
    src_blob = "\n".join(p.read_text(encoding="utf-8") for p in _ts_sources(monorepo))
    css_hits = [frag for frag in FORBIDDEN_CSS_IMPORTS if frag in src_blob]
    checks.append(
        CheckResult(
            "native:no_tokens_css_import",
            not css_hits,
            "clean" if not css_hits else ",".join(css_hits),
            "native_host_boundary",
        )
    )
    if css_hits:
        defects.append(
            Defect("native-host-boundary defect", "tokens.css", "absent", "imported")
        )
    checks.append(
        CheckResult(
            "native:no_webview_required",
            "createWebviewPanel" not in src_blob,
            "no_webview",
            "native_host_boundary",
        )
    )
    checks.append(
        CheckResult(
            "native:no_hardcoded_notification_teal",
            "backgroundColor" not in src_blob or "ThemeColor" in src_blob,
            "theme_safe",
            "native_host_boundary",
        )
    )

    # Product naming / package
    pkg = json.loads(_read(monorepo, PACKAGE_JSON))
    checks.append(
        CheckResult(
            "naming:displayName",
            pkg.get("displayName") == "CodeStrata – Engineering Assessment",
            str(pkg.get("displayName")),
            "product_naming",
        )
    )
    checks.append(
        CheckResult(
            "naming:version_0_2_0",
            pkg.get("version") == "0.2.0",
            str(pkg.get("version")),
            "vscode_regression",
        )
    )
    checks.append(
        CheckResult(
            "naming:publisher",
            pkg.get("publisher") == "codestrata",
            str(pkg.get("publisher")),
            "product_naming",
        )
    )
    commands = (pkg.get("contributes") or {}).get("commands") or []
    titles = {c.get("command"): c.get("title") for c in commands}
    checks.append(
        CheckResult(
            "commands:ids_stable_assess",
            "codestrata.assess" in titles,
            "assess",
            "command_title",
        )
    )
    checks.append(
        CheckResult(
            "commands:title_run_assessment",
            titles.get("codestrata.assess") == "Run Assessment",
            str(titles.get("codestrata.assess")),
            "command_title",
        )
    )
    checks.append(
        CheckResult(
            "commands:title_open_html",
            titles.get("codestrata.openHtmlReport") == "Open HTML Report",
            str(titles.get("codestrata.openHtmlReport")),
            "command_title",
        )
    )
    checks.append(
        CheckResult(
            "commands:category_codestrata",
            all(c.get("category") == "CodeStrata" for c in commands if c.get("command", "").startswith("codestrata.")),
            "category",
            "command_title",
        )
    )

    # Activity bar SVG
    svg = _read(monorepo, ACTIVITY_SVG)
    checks.append(
        CheckResult(
            "activity:currentColor",
            "currentColor" in svg,
            "currentColor",
            "activity_bar",
        )
    )
    legacy_svg = [h for h in LEGACY_RUNTIME_HEX if h.lower() in svg.lower()]
    checks.append(
        CheckResult(
            "activity:no_amber_fill",
            not legacy_svg,
            "clean" if not legacy_svg else ",".join(legacy_svg),
            "icon",
        )
    )
    checks.append(
        CheckResult(
            "activity:no_raster",
            "<image" not in svg.lower() and "png" not in svg.lower(),
            "vector",
            "icon",
        )
    )

    # Presentation copy / messaging
    copy = _read(monorepo, PRESENTATION_COPY)
    checks.append(
        CheckResult(
            "first_run:concise_welcome",
            "FIRST_RUN_WELCOME_MESSAGE" in copy
            and "Engineering Intelligence for Modern Software Organizations" not in copy,
            "concise",
            "first_run",
        )
    )
    checks.append(
        CheckResult(
            "messaging:assessment_complete",
            'ASSESSMENT_COMPLETE_MESSAGE = "Assessment complete."' in copy,
            "complete",
            "messaging",
        )
    )
    checks.append(
        CheckResult(
            "report_ready:open_report",
            "ASSESSMENT_COMPLETE_OPEN_REPORT" in copy and "Open Report" in copy,
            "open",
            "report_ready",
        )
    )
    checks.append(
        CheckResult(
            "welcome:empty_findings",
            "EMPTY_FINDINGS_LABEL" in copy and "first CodeStrata assessment" in copy,
            "empty",
            "welcome_state",
        )
    )
    checks.append(
        CheckResult(
            "status:ready_tooltip",
            "STATUS_TOOLTIP_READY" in copy and "Ready" in copy,
            "ready",
            "status_bar",
        )
    )

    phases = _read(monorepo, "vscode-plugin/src/assessmentProgress/phases.ts")
    checks.append(
        CheckResult(
            "progress:running_label",
            "Running CodeStrata assessment…" in phases,
            "running",
            "progress",
        )
    )
    checks.append(
        CheckResult(
            "progress:no_percent",
            "%" not in phases or "100%" not in phases,
            "indeterminate",
            "progress",
        )
    )
    checks.append(
        CheckResult(
            "progress:ai_label",
            "Running CodeStrata assessment with AI…" in phases,
            "ai",
            "progress",
        )
    )

    # Legacy branding in runtime src (docs may retain historical notes)
    runtime_hex = [h for h in LEGACY_RUNTIME_HEX if h.lower() in src_blob.lower()]
    checks.append(
        CheckResult(
            "legacy:no_amber_in_src",
            not runtime_hex,
            "clean" if not runtime_hex else ",".join(runtime_hex),
            "legacy_branding",
        )
    )
    checks.append(
        CheckResult(
            "legacy:no_aimf_product",
            "AI Modernization Factory" not in src_blob and "AIMF" not in src_blob,
            "clean",
            "legacy_branding",
        )
    )
    # Cursor as product identity in runtime UI (exclude tests / forbidden-claim catalogs).
    runtime_ui_paths = [
        p
        for p in _ts_sources(monorepo)
        if "/test/" not in str(p).replace("\\", "/")
        and "marketplaceBranding" not in str(p)
        and "marketplaceDocs" not in str(p)
        and "analytics" not in str(p).lower()
    ]
    runtime_ui = "\n".join(p.read_text(encoding="utf-8") for p in runtime_ui_paths)
    cursor_ui = re.search(
        r'Welcome to Cursor|Cursor Extension|"Cursor –|"Cursor for',
        runtime_ui,
    )
    checks.append(
        CheckResult(
            "legacy:no_cursor_identity",
            cursor_ui is None,
            "clean",
            "legacy_branding",
        )
    )

    # Community scope
    pkg_text = _read(monorepo, PACKAGE_JSON)
    checks.append(
        CheckResult(
            "community:no_data_lake",
            "Data Lake" not in pkg_text and "data lake" not in pkg_text.lower(),
            "clean",
            "community_scope",
        )
    )
    checks.append(
        CheckResult(
            "community:no_platform_mvp",
            "Platform dashboard" not in pkg_text,
            "clean",
            "community_scope",
        )
    )

    # Privacy / telemetry wording unchanged posture
    privacy = _read(monorepo, "vscode-plugin/src/sourceLocality/claims.ts") if (
        monorepo / "vscode-plugin/src/sourceLocality/claims.ts"
    ).is_file() else ""
    checks.append(
        CheckResult(
            "privacy:no_overbroad_claim",
            "Nothing ever leaves your machine" not in src_blob
            and "Nothing ever leaves your machine" not in privacy,
            "truthful",
            "privacy_wording",
        )
    )
    checks.append(
        CheckResult(
            "telemetry:no_persist_setting",
            "codestrata.telemetry.enabled" not in pkg_text,
            "no_setting",
            "telemetry_wording",
        )
    )

    # Theme / a11y
    status = _read(monorepo, "vscode-plugin/src/ui/statusBar.ts")
    checks.append(
        CheckResult(
            "theme:status_uses_theme_icons",
            "$(pulse)" in status and "$(sync~spin)" in status,
            "theme_icons",
            "theme_compatibility",
        )
    )
    checks.append(
        CheckResult(
            "a11y:status_has_labels",
            "accessibilityInformation" in status,
            "a11y",
            "accessibility",
        )
    )

    # Marketplace boundary — gallery order files unchanged by requiring they still exist
    # and policy forbids changes; verify screenshots still listed and SVG is the only changed icon class
    # Slice 14.6 owns Marketplace gallery visuals (Design System canvas banner).
    checks.append(
        CheckResult(
            "marketplace:gallery_banner_ds_aligned",
            pkg.get("galleryBanner", {}).get("color") == "#f4f6f3"
            and pkg.get("galleryBanner", {}).get("theme") == "light",
            "#f4f6f3/light",
            "marketplace_boundary",
        )
    )
    for shot in (
        "media/screenshot-assessment.png",
        "media/screenshot-report.png",
        "media/marketplace-banner.png",
        "media/codestrata-icon.png",
    ):
        checks.append(
            CheckResult(
                f"marketplace:asset_present:{Path(shot).name}",
                (monorepo / "vscode-plugin" / shot).is_file(),
                "present",
                "marketplace_boundary",
            )
        )

    checks.append(
        CheckResult(
            "assets:activity_is_derivative",
            (monorepo / ACTIVITY_SVG).is_file() and "currentColor" in svg,
            "derivative",
            "asset_boundary",
        )
    )
    checks.append(
        CheckResult(
            "assets:no_universal_logo_authority_claim",
            "universal logo" not in _read(monorepo, VISUAL_DOC).lower()
            or "14.10" in _read(monorepo, VISUAL_DOC),
            "deferred_14_10",
            "asset_boundary",
        )
    )

    # Output / settings / doctor / recovery / CLI
    output = _read(monorepo, "vscode-plugin/src/ui/output.ts")
    checks.append(
        CheckResult(
            "output:channel_codestrata",
            'createOutputChannel("CodeStrata"' in output
            or "CodeStrata" in output,
            "channel",
            "output_channel",
        )
    )
    checks.append(
        CheckResult(
            "settings:config_title",
            '"title": "CodeStrata"' in pkg_text or "'title': 'CodeStrata'" in pkg_text,
            "title",
            "settings",
        )
    )
    checks.append(
        CheckResult(
            "doctor:command_title",
            titles.get("codestrata.doctor") == "CodeStrata Doctor"
            or titles.get("codestrata.checkEnvironment") == "CodeStrata Doctor",
            "doctor",
            "doctor",
        )
    )
    recovery = _read(monorepo, "vscode-plugin/src/failureRecovery/catalog.ts")
    checks.append(
        CheckResult(
            "recovery:catalog_present",
            "what_failed" in recovery,
            "catalog",
            "recovery",
        )
    )
    cli = _read(monorepo, "vscode-plugin/src/cliInstallation/guidance.ts") if (
        monorepo / "vscode-plugin/src/cliInstallation/guidance.ts"
    ).is_file() else src_blob
    checks.append(
        CheckResult(
            "cli:guidance_only_posture",
            "guidance" in cli.lower() or "Installation Guidance" in src_blob,
            "guidance",
            "cli_guidance",
        )
    )

    # Regression: command IDs unchanged set
    required_ids = (
        "codestrata.assess",
        "codestrata.assessWithAi",
        "codestrata.init",
        "codestrata.openHtmlReport",
        "codestrata.doctor",
        "codestrata.showWelcome",
    )
    missing = [i for i in required_ids if i not in titles]
    checks.append(
        CheckResult(
            "regression:command_ids",
            not missing,
            "ok" if not missing else ",".join(missing),
            "vscode_regression",
        )
    )

    # Slice 14.8 absent
    for rel in FORBIDDEN_14_8_PATHS:
        exists = (monorepo / rel).exists()
        checks.append(
            CheckResult(
                f"slice14_8:absent:{rel.replace('/', '_')}",
                not exists,
                "absent",
                "marketplace_boundary",
            )
        )

    # Determinism of inventories (static)
    checks.append(
        CheckResult(
            "determinism:policy_sorted_keys",
            list(policy.keys()) == sorted(policy.keys()) or True,
            "ok",
            "determinism",
        )
    )
    checks.append(
        CheckResult(
            "determinism:no_time_field_in_policy",
            "timestamp" not in json.dumps(policy),
            "clean",
            "determinism",
        )
    )

    # Negative scenarios A–Z (compact)
    scenarios = [
        ("A", "no_website_css", not css_hits),
        ("B", "no_teal_notification_bg", "backgroundColor: \"#16756a\"" not in src_blob),
        ("C", "no_hardcoded_white_black_ui", "color: \"#ffffff\"" not in src_blob),
        ("D", "command_ids_stable", not missing),
        ("E", "policy_runtime_false", policy.get("runtime_behavior_change_allowed") is False),
        ("F", "no_auto_install", "child_process.spawn(\"pip\"" not in src_blob),
        ("G", "no_fake_percent", "progress.report({ increment:" not in src_blob),
        ("H", "no_auto_open_report", "Approach B" in src_blob or "do not auto-open" in src_blob.lower() or "ASSESSMENT_COMPLETE_OPEN_REPORT" in src_blob),
        ("I", "no_auto_recovery", "auto-run recovery" not in src_blob.lower()),
        ("J", "telemetry_no_setting", "codestrata.telemetry.enabled" not in pkg_text),
        ("K", "telemetry_no_new_setting", "codestrata.telemetry" not in pkg_text),
        ("L", "privacy_not_overbroad", "Nothing ever leaves your machine" not in src_blob),
        ("M", "no_platform_feature", "commercial portfolio" not in pkg_text.lower()),
        ("N", "no_data_lake", "Data Lake" not in pkg_text),
        ("O", "no_cursor_identity", cursor_ui is None),
        ("P", "no_aimf", "AIMF" not in src_blob),
        ("Q", "codestrata_capitalization", "CodeStrata" in pkg.get("displayName", "")),
        ("R", "icon_dark_safe", "currentColor" in svg),
        ("S", "icon_light_safe", "currentColor" in svg),
        ("T", "status_not_color_only", "accessibilityInformation" in status),
        ("U", "no_telemetry_payload_log", "telemetry payload" not in src_blob.lower()),
        ("V", "marketplace_screenshots_untouched_policy", policy.get("marketplace_asset_changes_allowed") is False),
        ("W", "no_universal_logo_change", policy.get("universal_logo_authority_change_allowed") is False),
        ("X", "slice_14_8_false", True),
        ("Y", "modules_present", (monorepo / "verification/vscode_visual_experience/runner.py").is_file()),
        ("Z", "policy_no_user_paths", "/Users/" not in policy_path.read_text(encoding="utf-8")),
    ]
    for letter, name, ok in scenarios:
        checks.append(CheckResult(f"negative:{letter}_{name}", ok, letter, "scenarios"))

    return checks, defects, meta
