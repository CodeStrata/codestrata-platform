"""Negative scenario matrix for Slice 17.20 (A–Z)."""

from __future__ import annotations

from pathlib import Path

from verification.community_ai_providers.helpers import check
from verification.community_ai_providers.models import CheckResult, Defect


def check_scenarios(
    monorepo: Path,
    *,
    flags: dict[str, bool],
) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    scenarios: list[tuple[str, str, bool]] = [
        ("A", "provider changes deterministic finding", flags.get("findings_stable", False)),
        ("B", "provider changes evidence", flags.get("evidence_stable", False)),
        ("C", "--no-ai still calls provider", flags.get("no_ai_zero_calls", False)),
        ("D", "missing provider credential breaks baseline assessment", flags.get("no_ai_no_creds", False)),
        ("E", "provider timeout hangs assessment", flags.get("timeout_bounded", False)),
        ("F", "infinite retries", flags.get("no_infinite_retry", False)),
        ("G", "provider key appears in report", flags.get("no_key_in_report", False)),
        ("H", "provider key appears in log", flags.get("no_key_in_log", False)),
        ("I", "prompt appears in telemetry", flags.get("no_prompt_telemetry", False)),
        ("J", "response appears in telemetry", flags.get("no_response_telemetry", False)),
        ("K", "exact prohibited model ID enters Data Lake", flags.get("model_id_privacy", False)),
        ("L", "malformed provider response corrupts report", flags.get("response_validated", False)),
        ("M", "provider response injects unsafe HTML/script", flags.get("safe_markup", False)),
        ("N", "one provider failure breaks another", flags.get("failure_isolated", False)),
        ("O", "invalid provider silently falls back", flags.get("no_silent_fallback", False)),
        ("P", "Bedrock uses static AWS key unnecessarily", flags.get("bedrock_chain", False)),
        ("Q", "broad Bedrock IAM introduced", flags.get("no_broad_iam", False)),
        ("R", "docs falsely claim no source/context is sent", flags.get("docs_accurate", False)),
        ("S", "OpenAI test actually uses OpenRouter", flags.get("openai_is_openai", False)),
        ("T", "Bedrock test actually routes elsewhere", flags.get("bedrock_is_bedrock", False)),
        ("U", "full 22-repo corpus starts", flags.get("no_full_22", False)),
        ("V", "VS Code publish starts", flags.get("no_vscode_publish", False)),
        ("W", "Community Status starts", flags.get("no_status_api", False)),
        ("X", "release tag created", flags.get("no_release_tag", False)),
        ("Y", "Slice 17.22 starts", flags.get("no_17_22", False)),
        ("Z", "verifier nondeterministic", flags.get("deterministic", False)),
    ]
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    results: dict[str, bool] = {}
    for letter, detail, ok in scenarios:
        results[letter] = bool(ok)
        checks.append(check(f"scenario:{letter}", bool(ok), detail, "scenarios"))
        if not ok:
            defects.append(
                Defect(
                    classification=f"scenario_{letter}",
                    check_id=f"scenario:{letter}",
                    expected="pass",
                    detail=detail,
                )
            )
    _ = monorepo
    return checks, defects, results
