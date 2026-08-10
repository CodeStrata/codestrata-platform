"""Negative scenarios A–Z for Slice 17.21."""

from __future__ import annotations

from typing import Any

from verification.community_vscode_clean_install.helpers import check
from verification.community_vscode_clean_install.models import CheckResult, Defect


def check_scenarios(
    *,
    flags: dict[str, bool],
) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    """flags values True means the negative scenario did NOT occur (pass)."""

    scenarios = [
        ("A", "clean extension cannot activate", flags.get("activates", False)),
        ("B", "extension relies on owner settings", flags.get("isolated_profile", False)),
        ("C", "Engine missing causes crash", flags.get("engine_missing_safe", False)),
        ("D", "default telemetry silently enabled", flags.get("telemetry_default_off", False)),
        ("E", "extension uses execute-api hostname", flags.get("api_authority_ok", False)),
        ("F", "assessment outputs outside artifacts", flags.get("artifacts_boundary", False)),
        ("G", "Open Report opens stale report", flags.get("opens_current", False)),
        ("H", "second run creates third version", flags.get("lifecycle_ok", False)),
        ("I", "telemetry sends source/findings/report", flags.get("privacy_ok", False)),
        ("J", "report auto-publishes after assessment", flags.get("no_auto_publish", False)),
        ("K", "Publish works without confirmation", flags.get("explicit_confirm", False)),
        ("L", "private repo publish lacks warning", flags.get("private_ack", False)),
        ("M", "public URL is raw S3", flags.get("branded_url", False)),
        ("N", "offline telemetry breaks assessment", flags.get("offline_ok", False)),
        ("O", "failed assessment replaces current", flags.get("failure_preserves_current", False)),
        ("P", "extension logs credentials", flags.get("security_ok", False)),
        ("Q", "package contains secret/local files", flags.get("vsix_clean", False)),
        ("R", "no-AI requires provider key", flags.get("no_ai_ok", False)),
        ("S", "consent differs from CLI", flags.get("consent_aligned", False)),
        ("T", "report publishing differs from CLI", flags.get("publish_uses_cli", False)),
        ("U", "full 22-repo corpus starts", flags.get("no_full_22", False)),
        ("V", "marketplace publish occurs", flags.get("no_marketplace", False)),
        ("W", "CLI publish occurs", flags.get("no_cli_publish", False)),
        ("X", "Community Status starts", flags.get("no_status", False)),
        ("Y", "Slice 17.23 starts", flags.get("no_17_23", False)),
        ("Z", "verifier nondeterministic", flags.get("deterministic", False)),
    ]
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    results: dict[str, bool] = {}
    for letter, title, ok in scenarios:
        results[letter] = bool(ok)
        checks.append(
            check(f"scenario:{letter}", bool(ok), title, "scenarios")
        )
    return checks, defects, results
