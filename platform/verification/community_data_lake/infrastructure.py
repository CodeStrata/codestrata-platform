"""Static infrastructure contract checks for community-data-lake (Slice 8.14)."""

from __future__ import annotations

from pathlib import Path

from verification.community_data_lake.models import CheckResult

REPO = Path(__file__).resolve().parents[3]
INFRA = REPO / "infrastructure"
LAKE_MODULE = INFRA / "modules" / "community-data-lake"
CLOUD_API_MODULE = INFRA / "modules" / "community-cloud-api"
PRODUCTION = INFRA / "production"


def _module_blob() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in sorted(LAKE_MODULE.glob("*.tf")))


def check_infrastructure_static() -> list[CheckResult]:
    blob = _module_blob()
    variables = (LAKE_MODULE / "variables.tf").read_text(encoding="utf-8")
    lifecycle = (LAKE_MODULE / "lifecycle.tf").read_text(encoding="utf-8")
    encryption = (LAKE_MODULE / "encryption.tf").read_text(encoding="utf-8")
    iam = (LAKE_MODULE / "iam.tf").read_text(encoding="utf-8")
    bucket_policy = (LAKE_MODULE / "bucket_policy.tf").read_text(encoding="utf-8")
    prod_lake = (PRODUCTION / "community-data-lake.tf").read_text(encoding="utf-8")
    lambda_iam = (CLOUD_API_MODULE / "iam.tf").read_text(encoding="utf-8")

    checks = [
        CheckResult(
            name="infra:retention_accepted_default_365",
            ok="default     = 365" in variables and "accepted_retention_days" in lifecycle,
            detail="365 days",
            category="infrastructure",
        ),
        CheckResult(
            name="infra:retention_quarantine_default_90",
            ok="default     = 90" in variables and "quarantine_retention_days" in lifecycle,
            detail="90 days",
            category="infrastructure",
        ),
        CheckResult(
            name="infra:retention_multipart_default_7",
            ok="default     = 7" in variables and "incomplete_multipart_days" in blob,
            detail="7 days",
            category="infrastructure",
        ),
        CheckResult(
            name="infra:retention_noncurrent_default_30",
            ok="default     = 30" in variables
            and "noncurrent_version_expiration_days" in lifecycle,
            detail="30 days",
            category="infrastructure",
        ),
        CheckResult(
            name="infra:encryption_aes256",
            ok='sse_algorithm = "AES256"' in encryption,
            detail="AES256",
            category="infrastructure",
        ),
        CheckResult(
            name="infra:encryption_bucket_key_disabled",
            ok="bucket_key_enabled = false" in encryption,
            detail="bucket_key_enabled=false",
            category="infrastructure",
        ),
        CheckResult(
            name="infra:encryption_no_kms",
            ok='resource "aws_kms' not in blob,
            detail="no aws_kms resource",
            category="infrastructure",
        ),
        CheckResult(
            name="infra:iam_put_get_present",
            ok="s3:PutObject" in iam and "s3:GetObject" in iam,
            detail="Put/Get",
            category="infrastructure",
        ),
        CheckResult(
            name="infra:iam_deny_deletes_both_prefixes",
            ok="DenyAcceptedObjectDeletion" in iam
            and "DenyQuarantineObjectDeletion" in iam
            and "s3:DeleteObject" in iam,
            detail="deny delete",
            category="infrastructure",
        ),
        CheckResult(
            name="infra:iam_list_bucket_prefix_scoped",
            ok=(
                "s3:ListBucket" in iam
                and "ListApprovedWriterPrefixes" in iam
                and "s3:prefix" in iam
                and "s3:listallmybuckets" not in iam.lower()
            ),
            detail="prefix-scoped ListBucket",
            category="infrastructure",
        ),
        CheckResult(
            name="infra:iam_no_kms_permissions",
            ok="kms:" not in iam.lower(),
            detail="no kms",
            category="infrastructure",
        ),
        CheckResult(
            name="infra:iam_writer_unattached",
            ok='resource "aws_iam_role"' not in blob
            and "aws_iam_role_policy_attachment" not in blob,
            detail="unattached",
            category="infrastructure",
        ),
        CheckResult(
            name="infra:bucket_policy_deny_insecure_transport",
            ok="DenyInsecureTransport" in bucket_policy
            and "aws:SecureTransport" in bucket_policy,
            detail="TLS required",
            category="infrastructure",
        ),
        CheckResult(
            name="infra:production_enable_ingestion_wire_true",
            ok="enable_ingestion_wire = true" in prod_lake,
            detail="enabled",
            category="infrastructure",
        ),
        CheckResult(
            name="infra:lambda_iam_no_s3",
            ok="s3:" not in lambda_iam.lower(),
            detail="no s3 in lambda iam",
            category="infrastructure",
        ),
    ]
    return checks


def check_opentofu(*, run_opentofu: bool = True) -> tuple[str, list[CheckResult], tuple[str, ...]]:
    """Run OpenTofu CLI validation when requested; return status, checks, warnings."""

    if not run_opentofu:
        return "skipped", [], ("opentofu_cli_skipped_by_caller",)

    try:
        from infrastructure.verification.opentofu import detect_tools, run_opentofu_cli_validation
    except ImportError:
        return "not_executed_import_unavailable", [], ("infrastructure_verification_unavailable",)

    tools = detect_tools()
    status, checks = run_opentofu_cli_validation(tools)
    warnings: list[str] = list(tools.warnings)
    if status == "not_executed_tool_unavailable":
        warnings.append("OpenTofu CLI validation not executed because tofu is unavailable")
    return status, [
        CheckResult(
            name=item.name,
            ok=item.ok,
            detail=item.detail,
            category="opentofu",
            scenario=item.scenario,
        )
        for item in checks
    ], tuple(warnings)


__all__ = ["check_infrastructure_static", "check_opentofu"]
