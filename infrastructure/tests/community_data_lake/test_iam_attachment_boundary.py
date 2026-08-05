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


def test_community_cloud_api_has_no_s3_permissions() -> None:
    iam = (API_MODULE / "iam.tf").read_text(encoding="utf-8").lower()
    assert "s3:" not in iam


def test_production_enable_ingestion_wire_false() -> None:
    text = (PRODUCTION / "community-data-lake.tf").read_text(encoding="utf-8")
    assert "enable_ingestion_wire = false" in text


def test_no_data_lake_env_vars_in_community_cloud_api_module() -> None:
    blob = _blob(API_MODULE)
    assert "DATA_LAKE" not in blob
    assert "community-data-lake" not in blob
    assert "community_data_lake" not in blob
