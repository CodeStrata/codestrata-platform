"""Negative scenarios A–Z for Slice 15.11 validation."""

from __future__ import annotations

VALIDATION_SCENARIOS: tuple[tuple[str, str], ...] = tuple(
    (chr(ord("A") + i), msg)
    for i, msg in enumerate(
        [
            "Installation metric counts events instead of distinct installs",
            "Suppression leaks cohort counts below minimum 3",
            "Privacy poison values appear in MetricResult or API JSON",
            "Unbounded raw/ or quarantine S3 prefix reads allowed",
            "Overview API accessible without authentication",
            "Authenticated overview exposes installation_id or model_id",
            "Dashboard polls metrics instead of single overview request",
            "Forbidden chart library in Insights package.json",
            "Production ingestion enabled in validation policy",
            "Athena Glue RDS or Redis introduced in Insights packages",
            "Slice 15.12 verification started",
            "Metric semantics redefined in Slice 15.11",
            "New dashboard capability added in Slice 15.11",
            "Frontend source references installation_id or model_id fields",
            "Password or session token appears in verification report",
            "Absolute filesystem paths appear in verification report",
            "Timestamps appear in verification report",
            "Platform or engine code included in Insights export",
            "IAM grants PutSecretValue to Insights auth runtime",
            "Overview batching replaced by per-metric polling",
            "Malformed object causes metric to report zero without limitation",
            "Auth weakens privacy by returning s3_key in overview",
            "Standalone export target missing or dry-run fails",
            "Prior slice verification packages missing",
            "Verifier report is nondeterministic across double write",
            "Live AWS Secrets Manager or S3 called during verification",
        ]
    )
)
