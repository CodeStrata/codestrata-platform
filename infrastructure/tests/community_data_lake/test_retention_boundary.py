"""Retention / lifecycle architecture boundary (Slice 8.10)."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
LAKE_MODULE = INFRA / "modules" / "community-data-lake"
API_MODULE = INFRA / "modules" / "community-cloud-api"


def _blob(module: Path) -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in module.glob("*.tf"))


def test_lifecycle_rule_ids_stable_and_unique() -> None:
    lifecycle = (LAKE_MODULE / "lifecycle.tf").read_text(encoding="utf-8")
    ids = [
        "accepted-retention",
        "quarantine-retention",
        "abort-incomplete-multipart-uploads",
        "expire-delete-markers",
    ]
    for rule_id in ids:
        assert lifecycle.count(f'id     = "{rule_id}"') == 1


def test_no_storage_class_transitions_anywhere_in_module() -> None:
    blob = _blob(LAKE_MODULE).lower()
    assert "transition {" not in blob
    assert "glacier" not in blob
    assert "deep_archive" not in blob


def test_no_object_lock_anywhere_in_module() -> None:
    blob = _blob(LAKE_MODULE).lower()
    assert "object_lock" not in blob


def test_writer_deny_delete_accepted_no_allow_delete() -> None:
    iam = (LAKE_MODULE / "iam.tf").read_text(encoding="utf-8")
    assert "DenyAcceptedObjectDeletion" in iam
    assert "DenyQuarantineObjectDeletion" in iam
    assert "s3:DeleteObject" in iam
    assert 'effect = "Deny"' in iam
    # Ensure DeleteObject never appears under an Allow effect before Deny.
    # Simpler: no "Allow" statement that lists DeleteObject as an action.
    lines = iam.splitlines()
    in_allow = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("effect"):
            in_allow = '"Allow"' in stripped
        if in_allow and "DeleteObject" in stripped:
            raise AssertionError(f"Allow DeleteObject found: {stripped}")


def test_community_cloud_api_module_unaffected_by_retention() -> None:
    blob = _blob(API_MODULE)
    assert "accepted_retention_days" not in blob
    assert "expire-delete-markers" not in blob
    assert "community-data-lake" not in blob


def test_enable_ingestion_wire_still_false() -> None:
    variables = (LAKE_MODULE / "variables.tf").read_text(encoding="utf-8")
    validation = (LAKE_MODULE / "validation.tf").read_text(encoding="utf-8")
    assert "default     = false" in variables
    assert "var.enable_ingestion_wire == false" in validation
