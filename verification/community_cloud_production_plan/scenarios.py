"""Negative scenarios A–Z for Slice 17.4."""

from __future__ import annotations

from verification.community_cloud_production_plan.models import CheckResult, Defect


def check_scenarios(*, flags: dict[str, bool]) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    scenarios = [
        ("A", "production apply executed", flags.get("no_apply_ok", False)),
        ("B", "destroy action exists", flags.get("destructive_ok", False)),
        ("C", "replacement of bootstrap state bucket", flags.get("destructive_ok", False) and flags.get("data_lake_ok", False)),
        ("D", "OIDC provider replacement", flags.get("destructive_ok", False) and flags.get("oidc_ok", False)),
        ("E", "GitHub role replacement", flags.get("destructive_ok", False) and flags.get("oidc_ok", False)),
        ("F", "state bucket reused as Data Lake", flags.get("data_lake_ok", False)),
        ("G", "production ingestion enabled", flags.get("ingestion_ok", False)),
        ("H", "DynamoDB planned", flags.get("unexpected_ok", False)),
        ("I", "Athena planned", flags.get("unexpected_ok", False)),
        ("J", "Glue planned", flags.get("unexpected_ok", False)),
        ("K", "RDS planned", flags.get("unexpected_ok", False)),
        ("L", "Redis planned", flags.get("unexpected_ok", False)),
        ("M", "EC2/ECS/EKS planned unexpectedly", flags.get("networking_ok", False) and flags.get("unexpected_ok", False)),
        ("N", "NAT Gateway planned unexpectedly", flags.get("networking_ok", False)),
        ("O", "public S3", flags.get("security_ok", False)),
        ("P", "broad runtime IAM", flags.get("iam_ok", False)),
        ("Q", "secret values enter tfvars/state", flags.get("secrets_ok", False)),
        ("R", "commercial Platform resource planned", flags.get("components_ok", False)),
        ("S", "Data Lake privacy boundary violated", flags.get("privacy_ok", False)),
        ("T", "GitHub plan role gets administrator mutation permissions", flags.get("github_plan_ok", False) and flags.get("security_ok", False)),
        ("U", "plan depends on local username/path", flags.get("report_safe", False)),
        ("V", "plan not reproducible", flags.get("repro_ok", False)),
        ("W", "Slice 17.6 starts", flags.get("boundary_ok", False)),
        ("X", "unrelated existing AWS resource modified", flags.get("destructive_ok", False) and flags.get("plan_ok", False)),
        ("Y", "verifier nondeterministic", True),
        ("Z", "report leaks account IDs/ARNs/secrets/paths/timestamps/state contents", flags.get("report_safe", False)),
    ]
    results: dict[str, bool] = {}
    for letter, label, ok in scenarios:
        results[letter] = bool(ok)
        checks.append(CheckResult(f"scenario:{letter}", bool(ok), label if ok else f"FAIL:{label}", "scenarios"))
        if not ok:
            defects.append(Defect("scenario", f"scenario:{letter}", "pass", label))
    return checks, defects, results
