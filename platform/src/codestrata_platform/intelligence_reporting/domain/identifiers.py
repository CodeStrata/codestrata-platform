"""Deterministic commercial intelligence report / dataset / pattern IDs."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.shared.ids import PlatformId


def _sha24(material: str) -> str:
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]


def _stable_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True, slots=True)
class EngineeringIntelligenceReportId:
    value: str

    def __post_init__(self) -> None:
        text = PlatformId(self.value).value
        if not text.startswith("eir:"):
            raise InvalidValueError(
                "Engineering Intelligence Report id must use eir: prefix",
                reason_code="invalid_eir_id_prefix",
            )
        object.__setattr__(self, "value", text)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class DatasetId:
    value: str

    def __post_init__(self) -> None:
        text = PlatformId(self.value).value
        if not text.startswith("dataset:"):
            raise InvalidValueError(
                "Dataset id must use dataset: prefix",
                reason_code="invalid_dataset_id_prefix",
            )
        object.__setattr__(self, "value", text)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class PatternId:
    value: str

    def __post_init__(self) -> None:
        text = PlatformId(self.value).value
        if not text.startswith("pattern:"):
            raise InvalidValueError(
                "Pattern id must use pattern: prefix",
                reason_code="invalid_pattern_id_prefix",
            )
        object.__setattr__(self, "value", text)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ObservationId:
    value: str

    def __post_init__(self) -> None:
        text = PlatformId(self.value).value
        if not text.startswith("obs:"):
            raise InvalidValueError(
                "Observation id must use obs: prefix",
                reason_code="invalid_observation_id_prefix",
            )
        object.__setattr__(self, "value", text)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class DrilldownId:
    value: str

    def __post_init__(self) -> None:
        text = PlatformId(self.value).value
        if not text.startswith("drilldown:"):
            raise InvalidValueError(
                "Drilldown id must use drilldown: prefix",
                reason_code="invalid_drilldown_id_prefix",
            )
        object.__setattr__(self, "value", text)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class LimitationId:
    value: str

    def __post_init__(self) -> None:
        text = PlatformId(self.value).value
        if not text.startswith("limitation:"):
            raise InvalidValueError(
                "Limitation id must use limitation: prefix",
                reason_code="invalid_limitation_id_prefix",
            )
        object.__setattr__(self, "value", text)

    def __str__(self) -> str:
        return self.value


def build_dataset_id(
    *,
    repository_assessment_refs: Sequence[Mapping[str, str]],
    selection_policy_version: str,
) -> DatasetId:
    """Build dataset:{sha256[:24]} from sorted assessment references + policy."""

    rows = sorted(
        (
            {
                "repository_id": str(item.get("repository_id", "")).strip(),
                "assessment_id": str(item.get("assessment_id", "")).strip(),
                "assessment_run_id": str(item.get("assessment_run_id", "")).strip(),
                "pinned_revision": str(item.get("pinned_revision", "")).strip(),
                "assessment_schema_version": str(
                    item.get("assessment_schema_version", "")
                ).strip(),
                "inclusion_status": str(item.get("inclusion_status", "")).strip(),
            }
            for item in repository_assessment_refs
        ),
        key=lambda row: (
            row["repository_id"],
            row["assessment_id"],
            row["assessment_run_id"],
        ),
    )
    material = _stable_json(
        {
            "selection_policy_version": selection_policy_version.strip(),
            "repository_assessments": rows,
        }
    )
    return DatasetId(f"dataset:{_sha24(material)}")


def build_report_id(
    *,
    dataset_id: str,
    schema_version: str,
    report_scope: str,
    assessment_run_identities: Sequence[str],
    report_policy_version: str,
    interpretation_policy_bundle_id: str = "",
) -> EngineeringIntelligenceReportId:
    """Build eir:{sha256[:24]} from stable report inputs (no timestamps/paths).

    ``interpretation_policy_bundle_id`` is additive for Slice 6.8. Empty/absent
    values preserve pre-6.8 report identity material so older payloads remain
    deserializable. When present, the bundle ID is part of report identity.
    """

    runs = sorted({item.strip() for item in assessment_run_identities if item.strip()})
    payload: dict[str, object] = {
        "dataset_id": dataset_id.strip(),
        "schema_version": schema_version.strip(),
        "report_scope": report_scope.strip(),
        "assessment_run_identities": runs,
        "report_policy_version": report_policy_version.strip(),
    }
    bundle = interpretation_policy_bundle_id.strip()
    if bundle:
        payload["interpretation_policy_bundle_id"] = bundle
    material = _stable_json(payload)
    return EngineeringIntelligenceReportId(f"eir:{_sha24(material)}")


def build_pattern_id(
    *,
    pattern_type: str,
    normalized_subject: str,
    rule_ids: Sequence[str],
    assessment_head_ids: Sequence[str],
    repository_ids: Sequence[str],
    policy_version: str,
) -> PatternId:
    material = _stable_json(
        {
            "pattern_type": pattern_type.strip(),
            "normalized_subject": normalized_subject.strip(),
            "rule_ids": sorted({item.strip() for item in rule_ids if item.strip()}),
            "assessment_head_ids": sorted(
                {item.strip() for item in assessment_head_ids if item.strip()}
            ),
            "repository_ids": sorted(
                {item.strip() for item in repository_ids if item.strip()}
            ),
            "policy_version": policy_version.strip(),
        }
    )
    return PatternId(f"pattern:{_sha24(material)}")


def build_observation_id(
    *,
    category: str,
    normalized_subject: str,
    repository_ids: Sequence[str],
    recommendation_ids: Sequence[str],
    priority_action_ids: Sequence[str],
    policy_version: str,
) -> ObservationId:
    material = _stable_json(
        {
            "category": category.strip(),
            "normalized_subject": normalized_subject.strip(),
            "repository_ids": sorted(
                {item.strip() for item in repository_ids if item.strip()}
            ),
            "recommendation_ids": sorted(
                {item.strip() for item in recommendation_ids if item.strip()}
            ),
            "priority_action_ids": sorted(
                {item.strip() for item in priority_action_ids if item.strip()}
            ),
            "policy_version": policy_version.strip(),
        }
    )
    return ObservationId(f"obs:{_sha24(material)}")


def build_drilldown_id(
    *,
    repository_id: str,
    assessment_id: str,
    assessment_run_id: str = "",
    dataset_id: str = "",
    canonical_report_digest: str = "",
    policy_token: str = "",
) -> DrilldownId:
    """Build drilldown:{sha256[:24]}.

    Slice 6.1 material is repository_id + assessment_id. Slice 6.9 adds optional
    run/dataset/digest/policy fields when non-empty so older payloads remain
    deserializable while report builders can bind full identity.
    """

    payload: dict[str, object] = {
        "repository_id": repository_id.strip(),
        "assessment_id": assessment_id.strip(),
    }
    run = assessment_run_id.strip()
    dataset = dataset_id.strip()
    digest = canonical_report_digest.strip()
    policy = policy_token.strip()
    if run:
        payload["assessment_run_id"] = run
    if dataset:
        payload["dataset_id"] = dataset
    if digest:
        payload["canonical_report_digest"] = digest
    if policy:
        payload["policy_token"] = policy
    material = _stable_json(payload)
    return DrilldownId(f"drilldown:{_sha24(material)}")


def build_limitation_id(
    *,
    category: str,
    statement: str,
    affected_repository_ids: Sequence[str] = (),
) -> LimitationId:
    material = _stable_json(
        {
            "category": category.strip(),
            "statement": statement.strip(),
            "affected_repository_ids": sorted(
                {item.strip() for item in affected_repository_ids if item.strip()}
            ),
        }
    )
    return LimitationId(f"limitation:{_sha24(material)}")
