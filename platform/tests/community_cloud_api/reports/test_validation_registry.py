"""Unit tests for private validation registry helpers."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.reports.validation_registry import (
    DEFAULT_LIST_LIMIT,
    MAX_LIST_LIMIT,
    VALIDATION_ENTRY_SCHEMA,
    VERIFICATION_PENDING,
    build_validation_entry,
    sanitize_list_limit,
    validation_entry_key,
)


def test_validation_entry_key_and_build() -> None:
    key = validation_entry_key("abc123")
    assert key == "metadata/validation/entries/abc123.json"
    entry = build_validation_entry(
        public_id="abc123",
        public_url="https://reports.codestrata.ai/r/abc123",
        report_type="assessment",
        logical_identity_key="github-example-repo",
        logical_identity_type="repository",
        published_at="2026-01-01T00:00:00Z",
    )
    assert entry["schema"] == VALIDATION_ENTRY_SCHEMA
    assert entry["temporary"] is True
    assert entry["verification_status"] == VERIFICATION_PENDING
    assert entry["display_identity"] == "github-example-repo"
    assert entry["purpose"] == "temporary_community_validation"


def test_sanitize_list_limit_bounds() -> None:
    assert sanitize_list_limit(None) == DEFAULT_LIST_LIMIT
    assert sanitize_list_limit("nope") == DEFAULT_LIST_LIMIT
    assert sanitize_list_limit(0) == DEFAULT_LIST_LIMIT
    assert sanitize_list_limit(25) == 25
    assert sanitize_list_limit(9999) == MAX_LIST_LIMIT
