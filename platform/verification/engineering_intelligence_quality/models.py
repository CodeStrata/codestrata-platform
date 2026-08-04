"""Models for SV.12 quality review."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class EditorialObservation:
    observation_id: str
    section: str
    classification: str
    statement: str
    affected_entity_ids: list[str] = field(default_factory=list)
    repository_scope: list[str] = field(default_factory=list)
    evidence_provenance_status: str = "n/a"
    customer_impact: str = "informational"
    release_impact: str = "informational"
    recommended_handling: str = "no_change"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DefectCandidate:
    classification: str
    statement: str
    section: str
    affected_entity_ids: list[str] = field(default_factory=list)
    repository_scope: list[str] = field(default_factory=list)
    expected: str = ""
    actual: str = ""
    reproducible: bool = True
    release_impact: str = "informational"
    recommended_handling: str = "documentation_only"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AudienceUsefulness:
    audience: str
    classification: str
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SectionReview:
    section: str
    ok: bool
    summary: str
    observations: list[dict[str, Any]] = field(default_factory=list)
    counts: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QualityReviewReport:
    schema_name: str
    schema_version: str
    verification_id: str
    catalog_id: str | None
    repository_count: int
    dataset_id: str | None
    eir_report_id: str | None
    interpretation_policy_bundle_id: str | None
    website_export_id: str | None
    included_repository_ids: list[str] = field(default_factory=list)
    dataset_review: dict[str, Any] = field(default_factory=dict)
    technology_distribution_review: dict[str, Any] = field(default_factory=dict)
    capability_comparison_review: dict[str, Any] = field(default_factory=dict)
    assessment_head_review: dict[str, Any] = field(default_factory=dict)
    recurring_pattern_review: dict[str, Any] = field(default_factory=dict)
    modernization_observation_review: dict[str, Any] = field(default_factory=dict)
    confidence_review: dict[str, Any] = field(default_factory=dict)
    limitation_review: dict[str, Any] = field(default_factory=dict)
    repository_drilldown_review: dict[str, Any] = field(default_factory=dict)
    provenance_review: dict[str, Any] = field(default_factory=dict)
    wording_review: dict[str, Any] = field(default_factory=dict)
    usability_review: dict[str, Any] = field(default_factory=dict)
    commercial_usefulness: list[dict[str, Any]] = field(default_factory=list)
    signal_to_noise: dict[str, Any] = field(default_factory=dict)
    website_safe_review: dict[str, Any] = field(default_factory=dict)
    special_case_review: dict[str, Any] = field(default_factory=dict)
    defect_candidates: list[dict[str, Any]] = field(default_factory=list)
    editorial_observations: list[dict[str, Any]] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    verdict: str = "FAIL"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
