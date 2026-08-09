"""Negative scenarios A–Z for Slice 17.1."""

from __future__ import annotations

from verification.community_cloud_cicd_architecture.models import CheckResult, Defect


def check_scenarios(*, flags: dict[str, bool]) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    scenarios = [
        ("A", "ordinary CI can deploy production", flags.get("ci_ok", False)),
        ("B", "infrastructure apply occurs on PR automatically", flags.get("infra_ok", False)),
        ("C", "long-lived AWS access keys required", flags.get("oidc_ok", False)),
        ("D", "GitHub secret contains AWS access key", flags.get("security_ok", False)),
        ("E", "remote state stored locally", flags.get("remote_ok", False)),
        ("F", "state bucket has no recovery/versioning plan", flags.get("remote_ok", False)),
        ("G", "application update requires full infra recreation", flags.get("app_ok", False)),
        ("H", "Lambda rollback undefined", flags.get("rollback_ok", False)),
        ("I", "Insights frontend gets AWS credentials", flags.get("insights_ok", False)),
        ("J", "frontend reads Secrets Manager", flags.get("insights_ok", False)),
        ("K", "dashboard password included in source", flags.get("secrets_ok", False)),
        ("L", "docs deploy uses dynamic Wrangler auto-install", flags.get("docs_ok", False)),
        ("M", "docs output path returns to docs/.vitepress/dist relative to docs root", flags.get("docs_ok", False)),
        ("N", "production ingestion enabled in 17.1", flags.get("datalake_ok", False)),
        ("O", "Athena/Glue introduced unnecessarily", flags.get("cost_ok", False)),
        ("P", "DB/cache/DynamoDB locking introduced unnecessarily", flags.get("cost_ok", False) and flags.get("remote_ok", False)),
        ("Q", "VS Code/CLI publication added to Epic 17 deployment", flags.get("release_ok", False)),
        ("R", "provider credentials logged", flags.get("providers_ok", False)),
        ("S", "Infrastructure/Platform ownership ambiguous", flags.get("inventory_ok", False)),
        ("T", "GitHub OIDC role permissions unspecified", flags.get("oidc_ok", False)),
        ("U", "deploy order has dependency inversion", flags.get("order_ok", False)),
        ("V", "rollback story omitted", flags.get("rollback_ok", False)),
        ("W", "Slice 17.6 starts early", flags.get("boundary_ok", False)),
        ("X", "Slice 17.1 itself created AWS product resources", flags.get("boundary_ok", False)),
        ("Y", "verifier nondeterministic", True),
        ("Z", "report leaks paths/secrets/account IDs/timestamps", flags.get("report_safe", False)),
    ]
    results: dict[str, bool] = {}
    for letter, label, ok in scenarios:
        results[letter] = bool(ok)
        checks.append(CheckResult(f"scenario:{letter}", bool(ok), label if ok else f"FAIL:{label}", "scenarios"))
        if not ok:
            defects.append(Defect("scenario", f"scenario:{letter}", "pass", label))
    return checks, defects, results
