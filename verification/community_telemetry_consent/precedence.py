"""Consent precedence checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_telemetry_consent.helpers import check, contains, read_text
from verification.community_telemetry_consent.models import CheckResult, Defect


def check_precedence(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    factory = monorepo / "engine/src/codestrata/telemetry/prompt_runtime_factory.py"
    cli_policy = monorepo / "engine/src/codestrata/telemetry/cli_consent_policy.py"
    assess = monorepo / "engine/src/codestrata/cli/assess.py"
    report = monorepo / "engine/src/codestrata/cli/report.py"

    checks.append(check("precedence:telemetry_allow_flag", contains(assess, "--telemetry-allow"), "assess flag present", "precedence"))
    checks.append(check("precedence:telemetry_deny_flag", contains(assess, "--telemetry-deny"), "assess flag present", "precedence"))
    checks.append(check(
        "precedence:cli_no_env_equivalent",
        contains(cli_policy, "environment_variable_equivalent") and ("False" in read_text(cli_policy)),
        "CLI assess consent has no env equivalent",
        "precedence",
    ))
    checks.append(check(
        "precedence:factory_cli_first",
        factory.is_file() and "select_cli_telemetry_consent" in read_text(factory),
        "CLI flags take precedence in runtime factory",
        "precedence",
    ))
    checks.append(check(
        "precedence:publish_independent_of_telemetry_env",
        not contains(report, "CODESTRATA_TELEMETRY_OPT_IN"),
        "report publish does not gate on CODESTRATA_TELEMETRY_OPT_IN",
        "precedence",
    ))

    summary = {
        "order": [
            "cli_flag_allow_or_deny",
            "durable_engine_preference",
            "interactive_prompt_if_eligible",
            "non_interactive_disabled_or_default",
        ],
        "publish_eligibility_env": None,
        "assess_env_equivalent": False,
        "ambiguous_sources": False,
    }
    return checks, defects, summary
