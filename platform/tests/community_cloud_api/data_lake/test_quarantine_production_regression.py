"""Production fail-closed regression for quarantine (Slice 8.9).

Quarantine persistence exists in-library but must remain unwired from
production ingestion. These tests guard that posture without claiming
production events are quarantined.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
INFRA = REPO_ROOT / "infrastructure"
LAKE_MODULE = INFRA / "modules" / "community-data-lake"
PROD = INFRA / "production"


def test_enable_ingestion_wire_remains_false_in_module_defaults() -> None:
    variables = (LAKE_MODULE / "variables.tf").read_text(encoding="utf-8")
    assert 'variable "enable_ingestion_wire"' in variables
    assert "default     = false" in variables


def test_production_composition_keeps_ingestion_wire_disabled() -> None:
    blob = (PROD / "community-data-lake.tf").read_text(encoding="utf-8")
    assert "enable_ingestion_wire = false" in blob


def test_quarantine_writer_policy_still_unattached() -> None:
    blob = "\n".join(p.read_text(encoding="utf-8") for p in LAKE_MODULE.glob("*.tf"))
    assert 'resource "aws_iam_role"' not in blob
    assert "aws_iam_role_policy_attachment" not in blob


def test_data_lake_package_exports_quarantine_but_docs_do_not_claim_production() -> None:
    from codestrata_platform.community_cloud_api import data_lake

    assert hasattr(data_lake, "QuarantineRecord")
    assert hasattr(data_lake, "build_quarantine_record")
    assert hasattr(data_lake, "project_quarantine_storage_object")
    docs = REPO_ROOT / "platform" / "docs" / "community-cloud-api" / "data-lake-quarantine.md"
    assert docs.is_file()
    text = docs.read_text(encoding="utf-8").lower()
    assert "unwired" in text
    assert "fail-closed" in text or "enable_ingestion_wire" in text
    assert "not claim" in text or "does not claim" in text
    # Must not affirmatively claim operational production quarantine.
    assert "production quarantine is operational" not in text
    assert "are quarantined in production" not in text
