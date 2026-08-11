"""Schema / safety tests for public-report-urls release manifest (Slice 19.1)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from verification.public_report_urls.manifest import (
    SCHEMA,
    default_manifest_path,
    load_manifest,
    normalize_manifest,
    save_manifest,
    upsert_published_url,
)
from verification.public_report_urls.template import (
    ALLOWED_PUBLIC_HOST_PREFIX,
    EMPTY_MANIFEST,
    FORBIDDEN_URL_FRAGMENTS,
)


def test_empty_template_schema() -> None:
    assert EMPTY_MANIFEST["schema"] == SCHEMA
    assert EMPTY_MANIFEST["assessments"] == []
    assert EMPTY_MANIFEST["engineering_intelligence"] == []


def test_upsert_and_reject_internal_urls(tmp_path: Path) -> None:
    path = tmp_path / "public-report-urls.json"
    save_manifest(path, dict(EMPTY_MANIFEST))
    good = "https://reports.codestrata.ai/r/abcXYZ0123456789_opaque"
    assert good.startswith(ALLOWED_PUBLIC_HOST_PREFIX)
    upsert_published_url(
        path,
        report_type="assessment",
        logical_id="repo-demo",
        public_url=good,
        source_slice="19.1-prep",
    )
    doc = load_manifest(path)
    assert doc["assessments"][0]["current_public_url"] == good
    assert doc["assessments"][0]["repository_id"] == "repo-demo"


@pytest.mark.parametrize(
    "bad",
    [
        "https://bucket.s3.amazonaws.com/key",
        "https://reports.codestrata.ai/r/x?X-Amz-Signature=abc",
        "https://example.com/Authorization=secret",
    ],
)
def test_forbidden_url_fragments_detected(bad: str) -> None:
    assert any(frag.lower() in bad.lower() for frag in FORBIDDEN_URL_FRAGMENTS) or (
        not bad.startswith(ALLOWED_PUBLIC_HOST_PREFIX)
    )


def test_normalize_rejects_non_object_gracefully() -> None:
    out = normalize_manifest({"schema": SCHEMA, "assessments": [], "engineering_intelligence": []})
    assert out["schema"] == SCHEMA


def test_default_path_under_artifacts() -> None:
    root = Path(__file__).resolve().parents[2]
    path = default_manifest_path(root)
    assert path.name == "public-report-urls.json"
    assert "release-v0.2.0" in str(path)
