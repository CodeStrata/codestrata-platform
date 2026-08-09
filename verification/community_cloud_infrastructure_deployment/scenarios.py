"""Negative scenarios A–Z for Slice 17.5."""

from __future__ import annotations

from verification.community_cloud_infrastructure_deployment.models import CheckResult, Defect


def check_scenarios(*, flags: dict[str, bool]) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    scenarios = [
        ("A", "infrastructure not actually deployed", flags.get("deployed_ok", False)),
        ("B", "destroy or replace in apply path", flags.get("preapply_ok", False) and flags.get("apply_ok", False)),
        ("C", "production ingestion enabled", flags.get("ingestion_ok", False)),
        ("D", "Data Lake writer attached", flags.get("writer_ok", False)),
        ("E", "application secrets configured", flags.get("secrets_ok", False)),
        ("F", "Insights deployed", flags.get("insights_ok", False)),
        ("G", "Docs product deployed", flags.get("docs_ok", False)),
        ("H", "DynamoDB created", flags.get("unexpected_ok", False)),
        ("I", "Athena created", flags.get("unexpected_ok", False)),
        ("J", "Glue created", flags.get("unexpected_ok", False)),
        ("K", "RDS created", flags.get("unexpected_ok", False)),
        ("L", "Redis created", flags.get("unexpected_ok", False)),
        ("M", "unexpected resources appear", flags.get("unexpected_ok", False)),
        ("N", "post-apply drift non-zero", flags.get("idempotency_ok", False) and flags.get("apply_ok", False)),
        ("O", "public S3 Data Lake", flags.get("security_ok", False)),
        ("P", "AdministratorAccess on apply role", flags.get("security_ok", False) and flags.get("iam_ok", False)),
        ("Q", "apply workflow on pull_request", flags.get("workflow_ok", False)),
        ("R", "casual tofu apply -auto-approve on unreviewed plan", flags.get("workflow_ok", False) and flags.get("apply_ok", False)),
        ("S", "image defaults enable ingestion", flags.get("image_ok", False) and flags.get("ingestion_ok", False)),
        ("T", "state bucket reused as Data Lake", flags.get("data_lake_ok", False)),
        ("U", "report depends on local username/path", flags.get("report_safe", False)),
        ("V", "verifier nondeterministic", True),
        ("W", "Slice 17.7 starts early", flags.get("boundary_ok", False)),
        ("X", "rollback posture undocumented", flags.get("rollback_ok", False)),
        ("Y", "GitHub apply policy missing or admin", flags.get("apply_perm_ok", False)),
        ("Z", "report leaks account IDs/ARNs/secrets/paths/timestamps", flags.get("report_safe", False)),
    ]
    results: dict[str, bool] = {}
    for letter, label, ok in scenarios:
        results[letter] = bool(ok)
        checks.append(CheckResult(f"scenario:{letter}", bool(ok), label if ok else f"FAIL:{label}", "scenarios"))
        if not ok:
            defects.append(Defect("scenario", f"scenario:{letter}", "pass", label))
    return checks, defects, results
