"""Boundary: quarantine HCL posture unchanged for Slice 8.9."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
API_MODULE = INFRA / "modules" / "community-cloud-api"
LAKE_MODULE = INFRA / "modules" / "community-data-lake"


def _blob(module: Path) -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in module.glob("*.tf"))


def test_community_cloud_api_still_unaware_of_data_lake() -> None:
    blob = _blob(API_MODULE)
    assert "community-data-lake" not in blob
    assert "community_data_lake" not in blob
    assert "quarantine" not in blob.lower() or "s3:" not in blob.lower()


def test_enable_ingestion_wire_defaults_false() -> None:
    variables = (LAKE_MODULE / "variables.tf").read_text(encoding="utf-8")
    assert "default     = false" in variables


def test_quarantine_prefix_unchanged() -> None:
    locals_tf = (LAKE_MODULE / "locals.tf").read_text(encoding="utf-8")
    assert 'quarantine_prefix = "quarantine/"' in locals_tf
