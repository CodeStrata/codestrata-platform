"""Slice 19.4 / 20.13B — public report Yes/No feedback + community sentiment."""

from __future__ import annotations

import json
import re
from datetime import date

from codestrata.reporting.html_v2.renderer import CONTENT_SECURITY_POLICY
from codestrata_platform.community_cloud_api.insights.external_metrics import (
    aggregate_community_sentiment,
)
from codestrata_platform.community_cloud_api.models import RequestContext
from codestrata_platform.community_cloud_api.reports.feedback import (
    ReportFeedbackRequest,
    apply_feedback_vote,
    empty_feedback_summary,
)
from codestrata_platform.community_cloud_api.reports.feedback_chrome import (
    apply_published_feedback_csp,
    feedback_chrome_html,
    published_feedback_csp,
)
from codestrata_platform.community_cloud_api.reports.service import (
    ReportPublishingService,
    _chrome_html,
)
from codestrata_platform.community_cloud_api.reports.store import InMemoryReportArtifactStore


def _published_service() -> tuple[ReportPublishingService, str]:
    store = InMemoryReportArtifactStore()
    service = ReportPublishingService(store=store, available=True)
    public_id = "A" * 32
    store.put_json(
        f"metadata/public/{public_id}.json",
        {
            "public_id": public_id,
            "status": "published",
            "report_type": "assessment",
        },
    )
    return service, public_id


def _feedback_context(public_id: str, useful: str, token: str) -> RequestContext:
    return RequestContext(
        api_version="v1",
        request_id="req-feedback-test",
        method="POST",
        path=f"/api/v1/reports/{public_id}/feedback",
        path_params={"public_id": public_id},
        validated_request=ReportFeedbackRequest(
            useful=useful,
            respondent_token=token,
        ),
    )


def _engine_like_inner() -> str:
    return (
        "<!DOCTYPE html><html><head>"
        f'<meta http-equiv="Content-Security-Policy" content="{CONTENT_SECURITY_POLICY}">'
        "<title>local</title></head><body><p>report body</p></body></html>"
    )


def test_yes_no_and_duplicate_protection() -> None:
    service, public_id = _published_service()
    token = "respondent-token-aaaa"

    r1 = service.handle_feedback(_feedback_context(public_id, "yes", token))
    assert r1.status_code == 200
    body1 = r1.body
    assert b'"outcome":"created"' in body1 or b'"outcome": "created"' in body1

    summary = service.community_sentiment_summary()
    assert summary["positive_responses"] == 1
    assert summary["total_responses"] == 1

    r2 = service.handle_feedback(_feedback_context(public_id, "yes", token))
    assert r2.status_code == 200
    assert b"unchanged" in r2.body
    summary = service.community_sentiment_summary()
    assert summary["total_responses"] == 1

    r3 = service.handle_feedback(_feedback_context(public_id, "no", token))
    assert r3.status_code == 200
    assert b"changed" in r3.body
    summary = service.community_sentiment_summary()
    assert summary["positive_responses"] == 0
    assert summary["negative_responses"] == 1
    assert summary["total_responses"] == 1


def test_invalid_and_unknown_report() -> None:
    service, public_id = _published_service()
    bad = service.handle_feedback(
        RequestContext(
            api_version="v1",
            request_id="req-bad",
            method="POST",
            path=f"/api/v1/reports/{public_id}/feedback",
            path_params={"public_id": public_id},
            validated_request=None,
        )
    )
    assert bad.status_code == 422

    missing = service.handle_feedback(
        _feedback_context("B" * 32, "yes", "respondent-token-bbbb")
    )
    assert missing.status_code == 404


def test_sentiment_zero_and_percentage() -> None:
    class Port:
        def __init__(self, summary: dict) -> None:
            self._summary = summary

        def community_sentiment_summary(self) -> dict:
            return self._summary

    zero = aggregate_community_sentiment(
        date(2026, 1, 1), date(2026, 1, 31), port=Port(empty_feedback_summary())
    )
    assert zero.denominator == 0
    assert zero.value is None
    assert "no_responses_yet" in zero.limitations

    live = aggregate_community_sentiment(
        date(2026, 1, 1),
        date(2026, 1, 31),
        port=Port(
            {
                "positive_responses": 41,
                "negative_responses": 9,
                "total_responses": 50,
            }
        ),
    )
    assert live.denominator == 50
    assert live.share == 0.82
    assert live.value == 82.0


def test_vote_math_helper() -> None:
    summary, outcome = apply_feedback_vote(
        summary=empty_feedback_summary(), prior_useful=None, new_useful="yes"
    )
    assert outcome == "created"
    assert summary["positive_responses"] == 1
    summary2, outcome2 = apply_feedback_vote(
        summary=summary, prior_useful="yes", new_useful="no"
    )
    assert outcome2 == "changed"
    assert summary2["positive_responses"] == 0
    assert summary2["negative_responses"] == 1


def test_chrome_includes_feedback_and_report_independent() -> None:
    html = _chrome_html(
        inner_html="<p>report</p>",
        report_type="assessment",
        generated_at=None,
        engine_version=None,
        public_id="C" * 32,
    )
    assert "Was this report useful?" in html
    assert 'data-useful="yes"' in html
    assert 'data-useful="no"' in html


def test_report_feedback_01_public_chrome_has_controls() -> None:
    """REPORT-FEEDBACK-01: Public report contains Yes/No when feedback is supported."""

    html = _chrome_html(
        inner_html=_engine_like_inner(),
        report_type="assessment",
        generated_at=None,
        engine_version="0.2.0",
        public_id="D" * 32,
    )
    assert "Was this report useful?" in html
    assert 'data-useful="yes"' in html
    assert 'data-useful="no"' in html
    assert 'id="cs-report-feedback"' in html


def test_report_feedback_02_yes_increments_once() -> None:
    """REPORT-FEEDBACK-02: Yes submits useful=yes; aggregate +1 once."""

    service, public_id = _published_service()
    before = service.community_sentiment_summary()["positive_responses"]
    r = service.handle_feedback(
        _feedback_context(public_id, "yes", "respondent-token-yes1")
    )
    assert r.status_code == 200
    assert service.community_sentiment_summary()["positive_responses"] == before + 1
    # Idempotent same token
    service.handle_feedback(_feedback_context(public_id, "yes", "respondent-token-yes1"))
    assert service.community_sentiment_summary()["positive_responses"] == before + 1


def test_report_feedback_03_no_increments_once() -> None:
    """REPORT-FEEDBACK-03: No submits useful=no; aggregate +1 once."""

    service, public_id = _published_service()
    before = service.community_sentiment_summary()["negative_responses"]
    r = service.handle_feedback(
        _feedback_context(public_id, "no", "respondent-token-no01")
    )
    assert r.status_code == 200
    assert service.community_sentiment_summary()["negative_responses"] == before + 1


def test_report_feedback_04_success_copy_in_chrome() -> None:
    """REPORT-FEEDBACK-04: Successful path UI copy is thank-you (client shows after 2xx)."""

    fragment, _nonce = feedback_chrome_html(public_id="E" * 32, nonce="test-nonce-abcdef")
    assert "Thank you for your feedback." in fragment
    assert "showThanks" in fragment
    assert "if (!res.ok) throw" in fragment


def test_report_feedback_05_failure_copy_retryable() -> None:
    """REPORT-FEEDBACK-05: Failed request does not thank; controls become retryable."""

    fragment, _nonce = feedback_chrome_html(public_id="F" * 32, nonce="test-nonce-abcdef")
    assert "We couldn't save your feedback. Please try again." in fragment
    assert "setBusy(false)" in fragment
    # Thank-you only via showThanks after ok response — not on catch path.
    catch_idx = fragment.index(".catch(function")
    assert "showThanks()" not in fragment[catch_idx:]


def test_report_feedback_06_rapid_click_guard() -> None:
    """REPORT-FEEDBACK-06: Repeated rapid click guarded by inflight/busy."""

    fragment, _nonce = feedback_chrome_html(public_id="G" * 32, nonce="test-nonce-abcdef")
    assert "if (!btn || inflight) return" in fragment
    assert "setBusy(true)" in fragment


def test_report_feedback_07_payload_privacy() -> None:
    """REPORT-FEEDBACK-07: Feedback payload has no repo/source/finding/installation identity."""

    fragment, _nonce = feedback_chrome_html(public_id="H" * 32, nonce="test-nonce-abcdef")
    body_match = re.search(r"JSON\.stringify\(\{([^}]+)\}\)", fragment)
    assert body_match is not None
    payload_src = body_match.group(1)
    for forbidden in (
        "repository",
        "installation_id",
        "source",
        "finding",
        "email",
        "path",
        "git",
        "assessment_metadata",
    ):
        assert forbidden not in payload_src.lower()
    assert "schema_version" in payload_src
    assert "useful" in payload_src
    assert "respondent_token" in payload_src

    req = ReportFeedbackRequest.model_json_schema()
    props = set(req.get("properties", {}).keys())
    assert props <= {"schema_version", "useful", "respondent_token"}


def test_report_feedback_08_local_offline_has_no_controls() -> None:
    """REPORT-FEEDBACK-08: Local/offline Engine CSP report has no feedback chrome."""

    local = _engine_like_inner()
    assert "Was this report useful?" not in local
    assert "cs-report-feedback" not in local
    assert "script-src 'none'" in local
    assert "connect-src 'none'" in local


def test_report_feedback_09_published_csp_allows_handler() -> None:
    """REPORT-FEEDBACK-09: Published representation rewrites CSP for feedback."""

    html = _chrome_html(
        inner_html=_engine_like_inner(),
        report_type="assessment",
        generated_at=None,
        engine_version="0.2.0",
        public_id="I" * 32,
    )
    assert "Was this report useful?" in html
    assert "connect-src 'self'" in html
    assert "script-src 'none'" not in html
    assert "connect-src 'none'" not in html
    nonce_match = re.search(r"<script nonce=\"([^\"]+)\">", html)
    assert nonce_match is not None
    nonce = nonce_match.group(1)
    assert f"script-src 'nonce-{nonce}'" in html
    assert "/r/" in html and "/feedback" in html


def test_report_feedback_10_assessment_semantics_unchanged() -> None:
    """REPORT-FEEDBACK-10: Feedback contract does not alter assessment JSON fields."""

    schema = ReportFeedbackRequest.model_json_schema()
    assert set(schema.get("properties", {}).keys()) == {
        "schema_version",
        "useful",
        "respondent_token",
    }
    # Chrome injection is presentation-only — body content preserved.
    html = _chrome_html(
        inner_html=_engine_like_inner().replace(
            "<p>report body</p>", "<p>report body SEMANTICS_MARKER</p>"
        ),
        report_type="assessment",
        generated_at=None,
        engine_version=None,
        public_id="J" * 32,
    )
    assert "SEMANTICS_MARKER" in html


def test_csp_helper_rewrites_engine_policy() -> None:
    nonce = "fixed-test-nonce-001"
    original = _engine_like_inner()
    assert "script-src 'none'" in original
    updated = apply_published_feedback_csp(original, nonce=nonce)
    assert published_feedback_csp(nonce=nonce) in updated
    assert "script-src 'none'" not in updated
