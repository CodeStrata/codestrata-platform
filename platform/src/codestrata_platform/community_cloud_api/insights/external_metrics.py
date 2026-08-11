"""External Insights metrics — GitHub stars/forks, published reports, sentiment."""

from __future__ import annotations

from datetime import date
from typing import Any, Protocol

from codestrata_platform.community_cloud_api.insights.completeness import finalize_limitations
from codestrata_platform.community_cloud_api.insights.models import MetricResult, MetricWindow


class PublishedReportsPort(Protocol):
    def count_published_reports(self) -> int: ...


class CommunitySentimentPort(Protocol):
    def community_sentiment_summary(self) -> dict[str, Any]: ...


def _window(metric_id: str, start: date, end: date) -> MetricWindow:
    return MetricWindow(start_date_utc=start, end_date_utc=end, horizon="external")


def aggregate_github_stars(start: date, end: date) -> MetricResult:
    stars: int | None = None
    lim = ["github_public_api"]
    try:
        from codestrata_platform.community_cloud_api.community_status.github_stars import (
            GitHubMetadataCache,
        )

        meta = GitHubMetadataCache().get()
        stars = meta.stars
        if stars is None:
            lim.append("source_unavailable")
    except Exception:  # noqa: BLE001
        lim.append("source_unavailable")
    return MetricResult(
        metric_id="github_stars",
        status="ok" if stars is not None else "error",
        window=_window("github_stars", start, end),
        value=stars,
        completeness="complete" if stars is not None else "unavailable",
        limitations=finalize_limitations(lim),
    )


def aggregate_github_forks(start: date, end: date) -> MetricResult:
    forks: int | None = None
    lim = ["github_public_api"]
    try:
        from codestrata_platform.community_cloud_api.community_status.github_stars import (
            GitHubMetadataCache,
        )

        meta = GitHubMetadataCache().get()
        forks = getattr(meta, "forks", None)
        if forks is None:
            lim.append("source_unavailable")
    except Exception:  # noqa: BLE001
        lim.append("source_unavailable")
    return MetricResult(
        metric_id="github_forks",
        status="ok" if forks is not None else "error",
        window=_window("github_forks", start, end),
        value=forks,
        completeness="complete" if forks is not None else "unavailable",
        limitations=finalize_limitations(lim),
    )


def aggregate_published_reports(
    start: date,
    end: date,
    *,
    port: PublishedReportsPort | None,
) -> MetricResult:
    lim = ["report_artifact_store_registry"]
    if port is None:
        return MetricResult(
            metric_id="published_reports",
            status="error",
            window=_window("published_reports", start, end),
            value=None,
            completeness="unavailable",
            limitations=finalize_limitations(lim + ["source_unavailable"]),
        )
    try:
        count = int(port.count_published_reports())
    except Exception:  # noqa: BLE001
        return MetricResult(
            metric_id="published_reports",
            status="error",
            window=_window("published_reports", start, end),
            value=None,
            completeness="unavailable",
            limitations=finalize_limitations(lim + ["source_unavailable"]),
        )
    return MetricResult(
        metric_id="published_reports",
        status="ok",
        window=_window("published_reports", start, end),
        value=count,
        completeness="complete",
        limitations=finalize_limitations(lim),
    )


def aggregate_community_sentiment(
    start: date,
    end: date,
    *,
    port: CommunitySentimentPort | None = None,
) -> MetricResult:
    """Explicit voluntary Yes/No feedback aggregate — never AI-inferred."""

    lim = ["voluntary_feedback_only", "explicit_yes_no_only"]
    if port is None:
        return MetricResult(
            metric_id="community_sentiment",
            status="ok",
            window=_window("community_sentiment", start, end),
            value=None,
            denominator=0,
            share=None,
            completeness="complete",
            limitations=finalize_limitations(lim + ["no_responses_yet"]),
        )
    try:
        summary = port.community_sentiment_summary()
    except Exception:  # noqa: BLE001
        return MetricResult(
            metric_id="community_sentiment",
            status="error",
            window=_window("community_sentiment", start, end),
            value=None,
            completeness="unavailable",
            limitations=finalize_limitations(lim + ["source_unavailable"]),
        )
    positive = int((summary or {}).get("positive_responses") or 0)
    negative = int((summary or {}).get("negative_responses") or 0)
    total = max(0, positive) + max(0, negative)
    if total <= 0:
        return MetricResult(
            metric_id="community_sentiment",
            status="ok",
            window=_window("community_sentiment", start, end),
            value=None,
            denominator=0,
            share=None,
            completeness="complete",
            limitations=finalize_limitations(lim + ["no_responses_yet"]),
        )
    share = positive / total
    return MetricResult(
        metric_id="community_sentiment",
        status="ok",
        window=_window("community_sentiment", start, end),
        value=round(share * 100.0, 1),
        denominator=total,
        share=share,
        completeness="complete",
        limitations=finalize_limitations(lim),
    )


def count_published_from_registry(registry: dict[str, Any]) -> int:
    """Count currently published assessment + EIR slots (privacy-safe; no URLs returned)."""

    total = 0
    for key in ("assessments", "engineering_intelligence"):
        for row in registry.get(key) or []:
            if not isinstance(row, dict):
                continue
            if row.get("current_status") == "published":
                total += 1
            if row.get("previous_status") == "published":
                total += 1
    return total
