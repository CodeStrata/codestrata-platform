"""Privacy-safe voluntary report usefulness feedback (Slice 19.4).

Stores only explicit Yes/No aggregates. No source code, repository identity,
findings, email, IP product analytics, or free text.
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import Field, field_validator

from codestrata_platform.community_cloud_api.validation.models import (
    CommunityApiRequestModel,
)

FEEDBACK_SUMMARY_KEY = "metadata/feedback/community_summary.json"
FEEDBACK_VOTE_PREFIX = "metadata/feedback/votes/"

_USEFUL_VALUES = frozenset({"yes", "no"})
_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{16,128}$")


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def empty_feedback_summary() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "positive_responses": 0,
        "negative_responses": 0,
        "total_responses": 0,
        "updated_at": None,
    }


def feedback_vote_key(*, public_id: str, respondent_token: str) -> str:
    digest = hashlib.sha256(
        f"{public_id}:{respondent_token}".encode("utf-8")
    ).hexdigest()
    return f"{FEEDBACK_VOTE_PREFIX}{digest}.json"


def respondent_hash(*, public_id: str, respondent_token: str) -> str:
    return hashlib.sha256(
        f"{public_id}:{respondent_token}".encode("utf-8")
    ).hexdigest()


class ReportFeedbackRequest(CommunityApiRequestModel):
    """Public voluntary Yes/No feedback for a published report."""

    schema_version: Literal["1.0"] = "1.0"
    useful: str
    respondent_token: str = Field(min_length=16, max_length=128)

    @field_validator("useful")
    @classmethod
    def _useful(cls, value: str) -> str:
        text = (value or "").strip().lower()
        if text not in _USEFUL_VALUES:
            raise ValueError("useful must be yes or no")
        return text

    @field_validator("respondent_token")
    @classmethod
    def _token(cls, value: str) -> str:
        text = (value or "").strip()
        if not _TOKEN_RE.fullmatch(text):
            raise ValueError("invalid respondent_token")
        return text


def apply_feedback_vote(
    *,
    summary: dict[str, Any],
    prior_useful: str | None,
    new_useful: str,
) -> tuple[dict[str, Any], str]:
    """Upsert one effective response. Returns (summary, outcome).

    Outcomes: created | unchanged | changed
    """

    next_summary = empty_feedback_summary()
    next_summary.update(
        {
            "positive_responses": int(summary.get("positive_responses") or 0),
            "negative_responses": int(summary.get("negative_responses") or 0),
        }
    )
    if prior_useful == new_useful:
        next_summary["total_responses"] = (
            next_summary["positive_responses"] + next_summary["negative_responses"]
        )
        next_summary["updated_at"] = summary.get("updated_at")
        return next_summary, "unchanged"

    if prior_useful == "yes":
        next_summary["positive_responses"] = max(
            0, next_summary["positive_responses"] - 1
        )
    elif prior_useful == "no":
        next_summary["negative_responses"] = max(
            0, next_summary["negative_responses"] - 1
        )

    if new_useful == "yes":
        next_summary["positive_responses"] += 1
    else:
        next_summary["negative_responses"] += 1

    next_summary["total_responses"] = (
        next_summary["positive_responses"] + next_summary["negative_responses"]
    )
    next_summary["updated_at"] = _now()
    outcome = "created" if prior_useful is None else "changed"
    return next_summary, outcome


def positive_percentage(*, positive: int, total: int) -> float | None:
    if total <= 0:
        return None
    return (positive / total) * 100.0


__all__ = [
    "FEEDBACK_SUMMARY_KEY",
    "FEEDBACK_VOTE_PREFIX",
    "ReportFeedbackRequest",
    "apply_feedback_vote",
    "empty_feedback_summary",
    "feedback_vote_key",
    "positive_percentage",
    "respondent_hash",
]
