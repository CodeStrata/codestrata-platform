"""Slice 19.4 — public report Yes/No feedback + community sentiment."""

from __future__ import annotations

from datetime import date

from codestrata_platform.community_cloud_api.insights.external_metrics import (
    aggregate_community_sentiment,
)
from codestrata_platform.community_cloud_api.models import RequestContext
from codestrata_platform.community_cloud_api.reports.feedback import (
    ReportFeedbackRequest,
    apply_feedback_vote,
    empty_feedback_summary,
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
