from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from codestrata.domain.evidence.framework.models import (
    Coverage,
    CoverageState,
    EvidenceActivity,
    EvidenceEnvelope,
    EvidencePlan,
    RepositorySubject,
)


def _coverage(*, complete: bool = True) -> Coverage:
    return Coverage(
        state=CoverageState.COMPLETE if complete else CoverageState.PARTIAL,
        population="selected files",
        planned=2,
        examined=2 if complete else 1,
        successful=True,
        supports_absence_conclusion=complete,
    )


def test_evidence_identity_is_stable_across_collection_times() -> None:
    values = []
    for collected_at in (
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 2, tzinfo=UTC) + timedelta(seconds=3),
    ):
        values.append(
            EvidenceEnvelope.create(
                kind="repository.inventory",
                run_id="run-different",
                activity_id="inventory",
                collector_id="collector",
                collector_version="1.0.0",
                repository_id="repo",
                revision="abc123",
                method="inspection",
                production_mode="observed",
                coverage=_coverage(),
                payload={"files": 2},
                collected_at=collected_at,
            )
        )
    assert values[0].evidence_id == values[1].evidence_id
    assert values[0].payload_sha256 == values[1].payload_sha256


def test_payload_change_changes_identity() -> None:
    common = {
        "kind": "repository.inventory",
        "run_id": "run",
        "activity_id": "inventory",
        "collector_id": "collector",
        "collector_version": "1.0.0",
        "repository_id": "repo",
        "revision": "abc123",
        "method": "inspection",
        "production_mode": "observed",
        "coverage": _coverage(),
    }
    first = EvidenceEnvelope.create(**common, payload={"files": 1})
    second = EvidenceEnvelope.create(**common, payload={"files": 2})
    assert first.evidence_id != second.evidence_id
    assert first.payload_sha256 != second.payload_sha256


def test_absence_observation_requires_complete_successful_search() -> None:
    with pytest.raises(ValidationError, match="negative observations require"):
        EvidenceEnvelope.create(
            kind="source.pattern.search",
            run_id="run",
            activity_id="patterns",
            collector_id="collector",
            collector_version="1.0.0",
            repository_id="repo",
            revision="abc123",
            method="search",
            production_mode="observed",
            coverage=_coverage(complete=False),
            payload={"assertion": "absent"},
        )


def test_plan_rejects_unknown_fields_and_duplicate_activities() -> None:
    payload = {
        "plan_id": "plan",
        "goal": "Understand testing evidence",
        "subject": {"repository_id": "repo", "path": "/tmp/repo"},
        "activities": [
            {"activity_id": "same", "collector_id": "one"},
            {"activity_id": "same", "collector_id": "two"},
        ],
        "surprise": True,
    }
    with pytest.raises(ValidationError) as caught:
        EvidencePlan.model_validate(payload)
    paths = {".".join(str(part) for part in item["loc"]) for item in caught.value.errors()}
    assert "surprise" in paths


def test_plan_json_and_yaml_compatible_shape() -> None:
    plan = EvidencePlan(
        plan_id="plan",
        goal="Understand repository evidence",
        subject=RepositorySubject(repository_id="repo", path="/tmp/repo"),
        activities=(
            EvidenceActivity(activity_id="inventory", collector_id="inventory"),
        ),
    )
    restored = EvidencePlan.model_validate(plan.model_dump(mode="json"))
    assert restored == plan
