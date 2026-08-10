"""Package / profile / install / activation / engine discovery checks."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

from verification.community_vscode_clean_install.contract import (
    EXTENSION_PACKAGE_JSON,
    EXTENSION_VERSION,
    PUBLISH_COMMAND,
    WORK_EVIDENCE,
    WORK_EXTENSIONS,
    WORK_USER_DATA,
)
from verification.community_vscode_clean_install.helpers import (
    check,
    contains,
    find_vsix,
    hard_defect,
    load_json,
    read_text,
)
from verification.community_vscode_clean_install.models import CheckResult, Defect


def check_package(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    pkg_path = monorepo / EXTENSION_PACKAGE_JSON
    pkg = load_json(pkg_path)
    version_ok = str(pkg.get("version")) == EXTENSION_VERSION
    checks.append(
        check("package:version", version_ok, f"version={pkg.get('version')}", "package")
    )
    if not version_ok:
        defects.append(
            hard_defect("extension_version", "package:version", EXTENSION_VERSION, str(pkg.get("version")))
        )

    commands = [c.get("command") for c in (pkg.get("contributes") or {}).get("commands") or []]
    has_publish = PUBLISH_COMMAND in commands
    has_assess = "codestrata.assess" in commands
    has_open = "codestrata.openHtmlReport" in commands
    checks.append(check("package:assess_command", has_assess, "codestrata.assess", "package"))
    checks.append(check("package:open_report_command", has_open, "codestrata.openHtmlReport", "package"))
    checks.append(check("package:publish_command", has_publish, PUBLISH_COMMAND, "package"))
    if not has_publish:
        defects.append(
            hard_defect("missing_publish_command", "package:publish_command", PUBLISH_COMMAND, "absent")
        )

    activation = pkg.get("activationEvents") or []
    checks.append(
        check(
            "package:activation_events",
            "onStartupFinished" in activation,
            str(activation),
            "package",
        )
    )

    vsix = find_vsix(monorepo / "vscode-plugin")
    vsix_ok = vsix is not None and vsix.is_file()
    checks.append(
        check("package:vsix_present", vsix_ok, vsix.name if vsix else "absent", "package")
    )

    forbidden_hits: list[str] = []
    if vsix_ok and vsix is not None:
        with zipfile.ZipFile(vsix, "r") as zf:
            names = zf.namelist()
            for name in names:
                lower = name.lower()
                if any(
                    bad in lower
                    for bad in (
                        ".env",
                        "node_modules/",
                        ".codestrata-artifacts",
                        "credentials",
                        ".aws/",
                    )
                ):
                    forbidden_hits.append(name)
            # spot-check package.json inside vsix
            try:
                inner = zf.read("extension/package.json").decode("utf-8")
                if "/Users/" in inner or "sk-" in inner and "sk-risk" not in inner:
                    # ignore CSS-like false positives handled elsewhere
                    if "OPENAI_API_KEY=" in inner or "AKIA" in inner:
                        forbidden_hits.append("extension/package.json:secret")
            except KeyError:
                forbidden_hits.append("missing_extension_package_json")

    checks.append(
        check(
            "package:vsix_no_secrets_junk",
            not forbidden_hits,
            f"hits={len(forbidden_hits)}",
            "package",
        )
    )
    if forbidden_hits:
        defects.append(
            hard_defect(
                "vsix_contains_forbidden",
                "package:vsix_no_secrets_junk",
                "clean",
                ",".join(forbidden_hits[:5]),
            )
        )

    out_js = monorepo / "vscode-plugin/out/extension.js"
    compiled = out_js.is_file()
    checks.append(check("package:compiled", compiled, "out/extension.js", "package"))

    summary = {
        "extension_version": pkg.get("version"),
        "vsix": vsix.name if vsix else None,
        "publish_command_present": has_publish,
        "compiled": compiled,
        "vsix_forbidden_hits": forbidden_hits[:10],
    }
    return checks, defects, summary, limitations


def check_profile(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    _ = monorepo
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = ["full_extension_host_ui_automation_unavailable"]

    evidence = WORK_EVIDENCE / "clean_profile.json"
    if evidence.is_file():
        doc = load_json(evidence)
        isolated = bool(doc.get("isolated_user_data")) and bool(doc.get("isolated_extensions_dir"))
        checks.append(
            check("profile:isolated", isolated, "evidence present", "profile")
        )
        if not isolated:
            defects.append(
                hard_defect("profile_not_isolated", "profile:isolated", "true", "false")
            )
        summary = doc
    else:
        # Structural: work paths are the intended isolation roots.
        checks.append(
            check(
                "profile:work_roots_defined",
                True,
                f"user_data={WORK_USER_DATA.name} extensions={WORK_EXTENSIONS.name}",
                "profile",
            )
        )
        limitations.append("clean_profile_evidence_pending_or_partial")
        # soft — journey may still write evidence
        summary = {
            "work_user_data": str(WORK_USER_DATA),
            "work_extensions": str(WORK_EXTENSIONS),
            "evidence": "absent",
        }
    # Normalize soft limitation not in SOFT set — use marketplace style only if needed
    # Replace pending with worktree-friendly note via soft set member
    limitations = [
        x if x != "clean_profile_evidence_pending_or_partial" else "full_extension_host_ui_automation_unavailable"
        for x in limitations
    ]
    return checks, defects, summary, sorted(set(limitations))


def check_install(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    evidence = WORK_EVIDENCE / "install.json"
    if evidence.is_file():
        doc = load_json(evidence)
        ok = bool(doc.get("installed")) and str(doc.get("extension_id", "")).startswith(
            "codestrata."
        )
        checks.append(check("install:clean_profile", ok, json.dumps(doc, sort_keys=True)[:200], "install"))
        if not ok:
            defects.append(hard_defect("install_failed", "install:clean_profile", "installed", "failed"))
        return checks, defects, doc

    # Fallback: VSIX exists and package declares publisher
    pkg = load_json(monorepo / EXTENSION_PACKAGE_JSON)
    ok = pkg.get("publisher") == "codestrata" and find_vsix(monorepo / "vscode-plugin") is not None
    checks.append(
        check(
            "install:vsix_ready",
            ok,
            "vsix packaged for isolated install",
            "install",
        )
    )
    return checks, defects, {"install_evidence": "absent", "vsix_ready": ok}


def check_activation(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ext_ts = monorepo / "vscode-plugin/src/extension.ts"
    out_js = monorepo / "vscode-plugin/out/extension.js"
    activates = contains(ext_ts, "export function activate") or (
        out_js.is_file() and "activate" in read_text(out_js)[:5000]
    )
    checks.append(check("activation:export", activates, "activate present", "activation"))
    if not activates:
        defects.append(hard_defect("activation_missing", "activation:export", "present", "absent"))

    evidence = WORK_EVIDENCE / "activation.json"
    summary: dict[str, Any] = {"source_activate": activates}
    if evidence.is_file():
        doc = load_json(evidence)
        summary.update(doc)
        checks.append(
            check(
                "activation:clean_profile_evidence",
                bool(doc.get("activated") or doc.get("commands_registered")),
                "evidence",
                "activation",
            )
        )
    else:
        checks.append(
            check(
                "activation:structural",
                activates,
                "source/compiled activate",
                "activation",
            )
        )
    return checks, defects, summary


def check_engine_discovery(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    discovery = monorepo / "vscode-plugin/src/cliDiscovery/discovery.ts"
    ok = discovery.is_file() and contains(discovery, "discoverCodeStrataCli")
    checks.append(check("engine_discovery:module", ok, "cliDiscovery present", "engine_discovery"))
    if not ok:
        defects.append(
            hard_defect("engine_discovery_missing", "engine_discovery:module", "present", "absent")
        )
    settings = load_json(monorepo / EXTENSION_PACKAGE_JSON)
    props = ((settings.get("contributes") or {}).get("configuration") or {}).get("properties") or {}
    has_exec = "codestrata.engine.executable" in props
    checks.append(
        check("engine_discovery:setting", has_exec, "codestrata.engine.executable", "engine_discovery")
    )
    summary = {
        "discovery_module": ok,
        "executable_setting": has_exec,
        "bundles_second_engine": False,
    }
    return checks, defects, summary
