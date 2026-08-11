"""Boundary checks: community-cloud-api stays unaware of the data lake."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
API_MODULE = INFRA / "modules" / "community-cloud-api"
LAKE_MODULE = INFRA / "modules" / "community-data-lake"


def _blob(module: Path) -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in module.glob("*.tf"))


def test_community_cloud_api_still_has_no_s3_bucket() -> None:
    blob = _blob(API_MODULE)
    assert 'resource "aws_s3_bucket"' not in blob


def test_data_lake_not_referenced_in_community_cloud_api_iam() -> None:
    iam = (API_MODULE / "iam.tf").read_text(encoding="utf-8")
    assert "community-data-lake" not in iam
    assert "community_data_lake" not in iam
    assert "s3:" not in iam.lower()


def test_data_lake_not_referenced_anywhere_in_community_cloud_api_module() -> None:
    blob = _blob(API_MODULE)
    assert "community-data-lake" not in blob
    assert "community_data_lake" not in blob


def test_enable_ingestion_wire_false_by_default() -> None:
    variables = (LAKE_MODULE / "variables.tf").read_text(encoding="utf-8")
    assert 'variable "enable_ingestion_wire"' in variables
    assert "default     = false" in variables


def test_data_lake_writer_policy_not_attached_to_any_role() -> None:
    blob = _blob(LAKE_MODULE)
    assert 'resource "aws_iam_role"' not in blob
    assert "aws_iam_role_policy_attachment" not in blob


def test_production_composition_enables_ingestion_wire() -> None:
    prod = INFRA / "production"
    data_lake_tf = (prod / "community-data-lake.tf").read_text(encoding="utf-8")
    assert "enable_ingestion_wire = true" in data_lake_tf
