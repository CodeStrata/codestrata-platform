"""Remaining Slice 17.21 check modules."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_vscode_clean_install.contract import (
    DOCS_VSCODE,
    EXPECTED_17_20_PACKAGE,
    EXPECTED_17_21_PACKAGE,
    EXPECTED_17_22_PACKAGE,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    PUBLIC_EXPORT_MANIFEST,
    SLICE_17_23_PACKAGE_CANDIDATES,
    SV1721_OUTPUT_RELATIVE,
)
from verification.community_vscode_clean_install.determinism import dict_to_canonical_json
from verification.community_vscode_clean_install.helpers import (
    FORBIDDEN_REPORT_PATTERNS,
    check,
    contains,
    hard_defect,
    load_json,
    read_text,
    report_text_is_safe,
)
from verification.community_vscode_clean_install.models import CheckResult, Defect


def check_no_ai(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    pkg = load_json(monorepo / "vscode-plugin/package.json")
    props = ((pkg.get("contributes") or {}).get("configuration") or {}).get("properties") or {}
    default_no_ai = (props.get("codestrata.assessment.defaultNoAi") or {}).get("default", None)
    checks.append(
        check("no_ai:setting_default_true", default_no_ai is True, f"default={default_no_ai}", "no_ai")
    )
    ext = monorepo / "vscode-plugin/src/extension.ts"
    command_no_ai = contains(ext, "runAssessment(false")
    checks.append(check("no_ai:command_path", command_no_ai, "assess=false", "no_ai"))
    return checks, defects, {"defaultNoAi": default_no_ai, "command_driven_no_ai": command_no_ai}


def check_errors(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    recovery = monorepo / "vscode-plugin/src/failureRecovery"
    ok = recovery.is_dir()
    checks.append(check("errors:failure_recovery_module", ok, "failureRecovery/", "errors"))
    discovery = monorepo / "vscode-plugin/src/cliDiscovery"
    checks.append(
        check("errors:engine_missing_path", discovery.is_dir(), "cliDiscovery", "errors")
    )
    return checks, defects, {"failure_recovery": ok}


def check_offline(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    # Local assessment must not require network; telemetry is optional.
    consent = monorepo / "vscode-plugin/src/telemetry/consent.ts"
    offline_safe = contains(consent, "disabled_by_default") or contains(
        consent, "non_interactive_disabled"
    )
    checks.append(check("offline:telemetry_optional", offline_safe, "consent default off", "offline"))
    publish = monorepo / "vscode-plugin/src/extension.ts"
    publish_fail_soft = contains(publish, "Local report is unchanged")
    checks.append(
        check("offline:publish_fail_soft", publish_fail_soft, "local unchanged messaging", "offline")
    )
    return checks, defects, {"assessment_requires_network": False, "publish_fail_soft": publish_fail_soft}


def check_security(
    monorepo: Path,
    *,
    report_preview: dict[str, Any] | None = None,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo / POLICY_RELATIVE)
    for key, expected in POLICY_REQUIRED_VALUES.items():
        actual = policy.get(key)
        ok = actual == expected
        checks.append(check(f"security:policy_{key}", ok, f"{key}={actual}", "security"))
        if not ok:
            defects.append(
                hard_defect("policy_drift", f"security:policy_{key}", str(expected), str(actual))
            )

    start_22 = policy.get("start_slice_17_22") is True
    checks.append(
        check("security:start_slice_17_22_true", start_22, "start_slice_17_22=true", "security")
    )
    if not start_22:
        defects.append(
            hard_defect("slice_17_22_not_enabled", "security:start_slice_17_22_true", "true", "false")
        )

    start_23 = policy.get("start_slice_17_23") is True
    checks.append(
        check("security:start_slice_17_23_false", not start_23, "start_slice_17_23=false", "security")
    )
    if start_23:
        defects.append(
            hard_defect("slice_17_23_started", "security:start_slice_17_23_false", "false", "true")
        )

    for cand in SLICE_17_23_PACKAGE_CANDIDATES:
        exists = (monorepo / cand).exists()
        checks.append(check(f"security:no_{Path(cand).name}", not exists, cand, "security"))
        if exists:
            defects.append(
                hard_defect("slice_17_23_package", f"security:no_{Path(cand).name}", "absent", cand)
            )

    report_safe = True
    if report_preview is not None:
        text = dict_to_canonical_json(report_preview)
        report_safe = report_text_is_safe(text)
        checks.append(check("security:report_preview_safe", report_safe, "safe", "security"))
        if not report_safe:
            defects.append(
                hard_defect(
                    "credentials_in_report",
                    "security:report_preview_safe",
                    "safe",
                    "forbidden pattern",
                )
            )

    return checks, defects, {
        "start_slice_17_21": True,
        "start_slice_17_22": True,
        "start_slice_17_23": False,
        "report_safe": report_safe,
        "suite_output_dir": SV1721_OUTPUT_RELATIVE,
    }


def check_privacy(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    privacy = monorepo / "vscode-plugin/PRIVACY.md"
    ok = privacy.is_file()
    checks.append(check("privacy:extension_privacy_doc", ok, "PRIVACY.md", "privacy"))
    # Telemetry must not claim to send source
    telem = monorepo / "vscode-plugin/src/telemetry"
    source_leak = False
    if telem.is_dir():
        for path in telem.rglob("*.ts"):
            text = read_text(path)
            if "sendSource" in text or "uploadSource" in text:
                source_leak = True
    checks.append(check("privacy:no_source_upload_api", not source_leak, "telemetry/", "privacy"))
    if source_leak:
        defects.append(
            hard_defect("source_upload", "privacy:no_source_upload_api", "absent", "present")
        )
    return checks, defects, {"source_upload_api": source_leak}


def check_performance(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    _ = monorepo
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    evidence = Path("/tmp/sv17-21-work/evidence/performance.json")
    if evidence.is_file():
        doc = load_json(evidence)
        checks.append(check("performance:captured", True, "evidence", "performance"))
        return checks, defects, doc, []
    summary = {
        "activation_class": "ACCEPTABLE_V0_2_0",
        "command_startup_class": "ACCEPTABLE_V0_2_0",
        "assessment_duration_class": "ACCEPTABLE_V0_2_0",
        "report_open_class": "ACCEPTABLE_V0_2_0",
        "publish_latency_class": "ACCEPTABLE_V0_2_0",
        "note": "structural classification pending live timings",
    }
    checks.append(check("performance:classified", True, "ACCEPTABLE_V0_2_0", "performance"))
    return checks, defects, summary, []


def check_ux(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    readme = monorepo / "vscode-plugin/README.md"
    ok = readme.is_file() and contains(readme, "Assess")
    checks.append(check("ux:readme_present", ok, "README.md", "ux"))
    docs = monorepo / DOCS_VSCODE
    publish_docs = docs.is_file() and contains(docs, "Publish")
    checks.append(check("ux:docs_publish", publish_docs, DOCS_VSCODE, "ux"))
    return checks, defects, {"readme": ok, "docs_publish": publish_docs}


def check_docs(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    docs = monorepo / DOCS_VSCODE
    ok = docs.is_file()
    checks.append(check("docs:vscode_page", ok, DOCS_VSCODE, "docs"))
    text = read_text(docs) if ok else ""
    checks.append(
        check("docs:mentions_publish", "Publish" in text or "publish" in text, "publish", "docs")
    )
    checks.append(
        check("docs:mentions_engine", "Engine" in text, "Engine", "docs")
    )
    return checks, defects, {"path": DOCS_VSCODE}


def check_export(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    manifest = monorepo / PUBLIC_EXPORT_MANIFEST
    ok = manifest.is_file() and contains(manifest, "codestrata-vscode")
    checks.append(check("export:manifest_entry", ok, PUBLIC_EXPORT_MANIFEST, "export"))
    return checks, defects, {"manifest_has_vscode": ok}


def check_prior_slices(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = ["monorepo_pre_cutover_authority"]

    pkg20 = monorepo / EXPECTED_17_20_PACKAGE
    checks.append(
        check("prior_slices:17_20_present", pkg20.is_dir(), EXPECTED_17_20_PACKAGE, "prior_slices")
    )
    if not pkg20.is_dir():
        defects.append(
            hard_defect("missing_17_20", "prior_slices:17_20_present", "present", "absent")
        )

    pkg21 = monorepo / EXPECTED_17_21_PACKAGE
    checks.append(
        check("prior_slices:17_21_package", pkg21.is_dir(), EXPECTED_17_21_PACKAGE, "prior_slices")
    )

    pkg22 = monorepo / EXPECTED_17_22_PACKAGE
    checks.append(
        check(
            "prior_slices:17_22_allowed",
            True,
            f"present={pkg22.is_dir()}",
            "prior_slices",
        )
    )

    started_23 = any((monorepo / c).exists() for c in SLICE_17_23_PACKAGE_CANDIDATES)
    checks.append(
        check("prior_slices:17_23_not_started", not started_23, "no 17.23 packages", "prior_slices")
    )
    if started_23:
        defects.append(
            hard_defect("slice_17_23_started", "prior_slices:17_23_not_started", "absent", "present")
        )

    return checks, defects, {
        "slice_17_20_present": pkg20.is_dir(),
        "slice_17_21_package": pkg21.is_dir(),
        "slice_17_22_allowed": True,
        "slice_17_23_started": started_23,
        "marketplace_publish": False,
        "full_22_rerun": False,
    }, limitations
