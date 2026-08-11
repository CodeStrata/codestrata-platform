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

    response = service.handle_public_get(_get_context(public_id))
    assert response.status_code == 200
    assert "text/html" in (response.media_type or "")
    assert response.headers.get("X-CodeStrata-Public-Id") == public_id
    body = response.body.decode("utf-8")
    assert "Endpoint not found" not in body
    assert f'codestrata-public-id" content="{public_id}"' in body


def test_oversized_html_returns_presigned_redirect_with_public_id_header(
    service: ReportPublishingService,
) -> None:
    """Oversized HTML skips chrome but must still expose stable identity header."""

    public_id = generate_public_report_id()
    huge = ("x" * 5_000_001).encode("utf-8")
    service._rotate_and_promote(  # noqa: SLF001
        report_type="assessment",
        logical_key=LOGICAL_KEY + "-oversized",
        artifacts={
            "assessment.html": huge,
            "assessment.json": _minimal_assessment_json(),
        },
        public_id=public_id,
        owner_ref="rlscope-test",
    )
    response = service.handle_public_get(_get_context(public_id))
    assert response.status_code == 307
    assert response.headers.get("X-CodeStrata-Public-Id") == public_id
    assert response.headers.get("X-CodeStrata-Report-Delivery") == "presigned_get"
    assert "codestrata-public-id" not in (response.body.decode("utf-8", errors="replace"))


def test_third_publish_prunes_oldest_public_id(service: ReportPublishingService) -> None:
    ids = [_publish(service) for _ in range(3)]
    oldest, middle, newest = ids

    oldest_resp = service.handle_public_get(_get_context(oldest))
    assert oldest_resp.status_code == 404
    oldest_body = json.loads(oldest_resp.body.decode("utf-8"))
    assert oldest_body["error"]["code"] == "report_not_found"
    assert oldest_body["error"]["message"] == "Report not found."
    assert "Endpoint not found" not in oldest_body["error"]["message"]

    assert service.handle_public_get(_get_context(middle)).status_code == 200
    assert service.handle_public_get(_get_context(newest)).status_code == 200

    logic = service._store.get_json(  # noqa: SLF001
        f"metadata/logic/assessment/{LOGICAL_KEY}.json"
    )
    assert logic is not None
    assert logic.get("current_public_id") == newest
    assert logic.get("previous_public_id") == middle


def test_unknown_public_id_is_report_not_found_not_endpoint_not_found(
    service: ReportPublishingService,
) -> None:
    unknown = generate_public_report_id()
    response = service.handle_public_get(_get_context(unknown))
    assert response.status_code == 404
    payload = json.loads(response.body.decode("utf-8"))
    assert payload["error"]["code"] == "report_not_found"
    assert payload["error"]["message"] == "Report not found."


def test_revoke_marks_record_revoked_and_public_get_404(service: ReportPublishingService) -> None:
    public_id = _publish(service)
    service._revoke_public_id(public_id, delete_artifacts=True)  # noqa: SLF001

    record = service._store.get_json(f"metadata/public/{public_id}.json")  # noqa: SLF001
    assert record is not None
    assert record.get("status") == STATUS_REVOKED
    response = service.handle_public_get(_get_context(public_id))
    assert response.status_code == 404
    payload = json.loads(response.body.decode("utf-8"))
    assert payload["error"]["code"] == "report_not_found"


def test_metadata_never_contains_raw_s3_hosts(service: ReportPublishingService) -> None:
    public_id = _publish(service)
    for key in service._store.list_keys("metadata/public/"):  # noqa: SLF001
        raw = json.dumps(service._store.get_json(key))
        assert "amazonaws.com" not in raw
        assert "s3://" not in raw

    url = public_report_url(public_id)
    assert ".s3." not in url.lower()


def test_publish_writes_pending_validation_registry_entry(
    service: ReportPublishingService,
) -> None:
    public_id = _publish(service)
    entry = service._store.get_json(  # noqa: SLF001
        f"metadata/validation/entries/{public_id}.json"
    )
    assert entry is not None
    assert entry.get("schema") == "community-validation-report-entry:1.0"
    assert entry.get("temporary") is True
    assert entry.get("public_report_id") == public_id
    assert entry.get("public_url") == public_report_url(public_id)
    assert entry.get("report_type") == "assessment"
    assert entry.get("logical_identity_key") == LOGICAL_KEY
    assert entry.get("display_identity") == LOGICAL_KEY
    assert entry.get("verification_status") == "published_pending_verification"


def test_verification_marks_entry_verified(service: ReportPublishingService) -> None:
    from codestrata_platform.community_cloud_api.reports.models import (
        ReportVerificationRequest,
    )

    public_id = _publish(service)

    class _Principal:
        def to_stable_dict(self) -> dict[str, str]:
            return {"client_id": "test"}

    context = RequestContext(
        api_version="v1",
        method="POST",
        path=f"/reports/{public_id}/verification",
        request_id="req-verify",
        path_params={"public_id": public_id},
        authenticated_client=_Principal(),
        validated_request=ReportVerificationRequest(
            schema_version="1.0",
            verification_status="verified",
            http_status=200,
        ),
    )
    response = service.handle_verification(context)
    assert response.status_code == 200
    payload = json.loads(response.body.decode("utf-8"))
    assert payload.get("verification_status") == "verified"
    assert payload.get("temporary") is True

    entry = service._store.get_json(  # noqa: SLF001
        f"metadata/validation/entries/{public_id}.json"
    )
    assert entry is not None
    assert entry.get("verification_status") == "verified"
    assert entry.get("verified_http_status") == 200
    assert entry.get("verified_at")


def test_list_validation_registry_paginates(service: ReportPublishingService) -> None:
    ids = [_publish(service) for _ in range(3)]
    # Distinct logical keys so each publish is a separate validation entry
    # (same LOGICAL_KEY rotates current/previous but keeps all public ids in
    # validation entries until pruned — third publish revokes oldest public
    # meta but validation entries remain for corpus history).
    page1 = service.list_validation_registry(limit=2)
    assert page1["temporary"] is True
    assert len(page1["items"]) == 2
    assert page1["next_cursor"] is not None
    page2 = service.list_validation_registry(
        limit=2, cursor=str(page1["next_cursor"])
    )
    assert len(page2["items"]) >= 1
    seen = {row["public_report_id"] for row in page1["items"] + page2["items"]}
    assert set(ids).issubset(seen)
    for row in page1["items"]:
        assert "artifact_prefix" not in row
        assert row.get("temporary") is True


def test_list_published_registry_includes_verification_status(
    service: ReportPublishingService,
) -> None:
    public_id = _publish(service)
    registry = service.list_published_registry()
    assert len(registry["assessments"]) == 1
    row = registry["assessments"][0]
    assert row["repository_id"] == LOGICAL_KEY
    assert row["public_report_id"] == public_id
    assert row["verification_status"] == "published_pending_verification"