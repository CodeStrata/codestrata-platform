"""IAM attachment boundary: writer policy stays unattached (Slice 8.12)."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
LAKE_MODULE = INFRA / "modules" / "community-data-lake"
API_MODULE = INFRA / "modules" / "community-cloud-api"
PRODUCTION = INFRA / "production"


def _blob(module: Path) -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in module.glob("*.tf"))


def test_lake_module_has_no_role_or_attachment() -> None:
    blob = _blob(LAKE_MODULE)
    assert 'resource "aws_iam_role"' not in blob
    assert "aws_iam_role_policy_attachment" not in blob


def test_community_cloud_api_foundation_iam_has_no_s3_permissions() -> None:
    """Foundation iam.tf remains logging+ECR; Insights S3 lives in production/runtime-security.tf."""
    iam = (API_MODULE / "iam.tf").read_text(encoding="utf-8").lower()
    assert "s3:" not in iam


def test_production_enable_ingestion_wire_true() -> None:
    text = (PRODUCTION / "community-data-lake.tf").read_text(encoding="utf-8")
    assert "enable_ingestion_wire = true" in text


def test_data_lake_env_vars_gated_on_enable_ingestion() -> None:
    config = (API_MODULE / "configuration.tf").read_text(encoding="utf-8")
    assert "CODESTRATA_DATA_LAKE_ADAPTER" in config
    assert "CODESTRATA_DATA_LAKE_BUCKET" in config
    assert "var.enable_ingestion" in config
    blob = _blob(API_MODULE)
    assert "community-data-lake" not in blob
    assert "community_data_lake" not in blob


def test_production_runtime_security_attaches_writer_for_ingestion() -> None:
    text = (PRODUCTION / "runtime-security.tf").read_text(encoding="utf-8")
    main = (PRODUCTION / "main.tf").read_text(encoding="utf-8")
    assert "codestrata-community-insights-production-reader" in text
    assert "codestrata-community-insights-production-secrets" in text
    assert "aws_iam_role_policy_attachment" in text
    assert "lambda_data_lake_writer" in text
    assert "module.community_data_lake.writer_policy_arn" in text
    assert "enable_ingestion                = true" in main