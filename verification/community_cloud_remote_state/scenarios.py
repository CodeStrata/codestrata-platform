"""Negative scenarios A–Z for Slice 17.2."""

from __future__ import annotations

from verification.community_cloud_remote_state.models import CheckResult, Defect


def check_scenarios(*, flags: dict[str, bool]) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    scenarios = [
        ("A", "prior partial attempt ignored and duplicate bucket created", flags.get("forensic_ok", False)),
        ("B", "unknown existing bucket adopted", flags.get("naming_ok", False)),
        ("C", "wrong-region bucket adopted", flags.get("region_ok", False)),
        ("D", "wrong-account bucket adopted", flags.get("identity_ok", False)),
        ("E", "state bucket equals Data Lake", flags.get("datalake_ok", False)),
        ("F", "DynamoDB created", flags.get("no_ddb_ok", False)),
        ("G", "dynamodb_table returns", flags.get("no_ddb_ok", False)),
        ("H", "DynamoDB IAM permissions added", flags.get("no_ddb_ok", False)),
        ("I", "bucket public", flags.get("pab_ok", False)),
        ("J", "versioning disabled", flags.get("versioning_ok", False)),
        ("K", "encryption disabled", flags.get("encryption_ok", False)),
        ("L", "website hosting enabled", flags.get("security_ok", False)),
        ("M", "state committed", flags.get("source_ok", False)),
        ("N", "bootstrap state committed", flags.get("source_ok", False)),
        ("O", "credential/profile hardcoded in portable backend", flags.get("backend_ok", False)),
        ("P", "raw state printed in report", flags.get("report_safe", False)),
        ("Q", "production tofu apply runs", flags.get("boundary_ok", False)),
        ("R", "Lambda/API/ECR created", flags.get("boundary_ok", False)),
        ("S", "Data Lake created", flags.get("boundary_ok", False)),
        ("T", "Secrets created", flags.get("boundary_ok", False)),
        ("U", "OIDC role created early", flags.get("epic17_ok", False)),
        ("V", "production ingestion enabled", flags.get("boundary_ok", False)),
        ("W", "Slice 17.6 starts", flags.get("epic17_ok", False)),
        ("X", "bootstrap is non-idempotent", flags.get("bucket_ok", False)),
        ("Y", "verifier nondeterministic", True),
        ("Z", "report leaks account/ARN/profile/session/secret/path/timestamp/state data", flags.get("report_safe", False)),
    ]
    results: dict[str, bool] = {}
    for letter, label, ok in scenarios:
        results[letter] = bool(ok)
        checks.append(CheckResult(f"scenario:{letter}", bool(ok), label if ok else f"FAIL:{label}", "scenarios"))
        if not ok:
            defects.append(Defect("scenario", f"scenario:{letter}", "pass", label))
    return checks, defects, results
