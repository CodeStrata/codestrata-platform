"""Unit tests for ReportPublishingService (Slice 17.16)."""

from __future__ import annotations

import json
import re

import pytest

from codestrata_platform.community_cloud_api.models import RequestContext
from codestrata_platform.community_cloud_api.reports.ids import (
    generate_public_report_id,
    validate_public_report_id,
)
from codestrata_platform.community_cloud_api.reports.policy import (
    STATUS_PUBLISHED,
    STATUS_REVOKED,
    public_report_url,
)
from codestrata_platform.community_cloud_api.reports.service import ReportPublishingService
from codestrata_platform.community_cloud_api.reports.store import InMemoryReportArtifactStore

FIXED_CLOCK = 1_700_000_000.0
_OPAQUE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{32,48}$")
LOGICAL_KEY = "github-example-org-example-repo"


def _minimal_assessment_json() -> bytes:
    return json.dumps(
        {
            "schema_version": "1.0",
            "generated_at": "2026-01-01T00:00:00Z",
            "engine_version": "test-engine",
            "summary": {"status": "ok"},
        },
        sort_keys=True,
    ).encode("utf-8")


def _minimal_assessment_html() -> bytes:
    return b"<html><body><p>Assessment summary</p></body></html>"


def _artifacts() -> dict[str, bytes]:
    return {
        "assessment.html": _minimal_assessment_html(),
        "assessment.json": _minimal_assessment_json(),
    }


def _get_context(public_id: str) -> RequestContext:
    return RequestContext(
        api_version="v1",
        method="GET",
        path=f"/reports/{public_id}",
        request_id="req-test-get",
        path_params={"public_id": public_id},
    )


def _publish(service: ReportPublishingService, *, owner_ref: str = "rlscope-test") -> str:
    public_id = generate_public_report_id()
    service._rotate_and_promote(  # noqa: SLF001 — unit test targets rotation/publish core
        report_type="assessment",
        logical_key=LOGICAL_KEY,
        artifacts=_artifacts(),
        public_id=public_id,
        owner_ref=owner_ref,
    )
    return public_id


@pytest.fixture
def service() -> ReportPublishingService:
    return ReportPublishingService(
        store=InMemoryReportArtifactStore(),
        clock=lambda: FIXED_CLOCK,
        available=True,
    )


def test_publish_creates_opaque_id_and_branded_public_url(service: ReportPublishingService) -> None:
    public_id = _publish(service)
    validate_public_report_id(public_id)
    assert _OPAQUE_ID_RE.fullmatch(public_id)

    record = service._store.get_json(f"metadata/public/{public_id}.json")  # noqa: SLF001
    assert record is not None
    assert record.get("status") == STATUS_PUBLISHED

    url = public_report_url(public_id)
    assert url == f"https://reports.codestrata.ai/r/{public_id}"
    assert "amazonaws.com" not in url
    assert "s3://" not in url

    assert service.handle_public_get(_get_context(public_id)).status_code == 200


def test_third_publish_prunes_oldest_public_id(service: ReportPublishingService) -> None:
    ids = [_publish(service) for _ in range(3)]
    oldest, middle, newest = ids

    assert service.handle_public_get(_get_context(oldest)).status_code == 404
    assert service.handle_public_get(_get_context(middle)).status_code == 200
    assert service.handle_public_get(_get_context(newest)).status_code == 200

    logic = service._store.get_json(  # noqa: SLF001
        f"metadata/logic/assessment/{LOGICAL_KEY}.json"
    )
    assert logic is not None
    assert logic.get("current_public_id") == newest
    assert logic.get("previous_public_id") == middle


def test_revoke_marks_record_revoked_and_public_get_404(service: ReportPublishingService) -> None:
    public_id = _publish(service)
    service._revoke_public_id(public_id, delete_artifacts=True)  # noqa: SLF001

    record = service._store.get_json(f"metadata/public/{public_id}.json")  # noqa: SLF001
    assert record is not None
    assert record.get("status") == STATUS_REVOKED
    assert service.handle_public_get(_get_context(public_id)).status_code == 404


def test_metadata_never_contains_raw_s3_hosts(service: ReportPublishingService) -> None:
    public_id = _publish(service)
    for key in service._store.list_keys("metadata/public/"):  # noqa: SLF001
        raw = json.dumps(service._store.get_json(key))
        assert "amazonaws.com" not in raw
        assert "s3://" not in raw

    url = public_report_url(public_id)
    assert ".s3." not in url.lower()
