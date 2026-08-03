"""Website-safe export projection models (separate from internal EIR)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SafeTechnologyRow:
    category: str
    technology: str
    repository_count: int
    denominator: int
    ratio: str | None
    version_states: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SafeCapabilityRow:
    assessment_head_id: str
    repository_alias: str
    activation_status: str
    coverage_status: str
    confidence_level: str
    finding_count: int
    recommendation_count: int
    priority_action_count: int
    highest_severity: str | None = None


@dataclass(frozen=True, slots=True)
class SafeHeadDistributionRow:
    assessment_head_id: str
    repository_count: int
    activated_count: int
    complete_coverage_count: int
    partial_coverage_count: int
    insufficient_evidence_count: int
    unavailable_count: int
    disabled_count: int
    finding_count: int
    recommendation_count: int
    priority_action_count: int
    severity_distribution: tuple[tuple[str, int], ...] = ()
    confidence_distribution: tuple[tuple[str, int], ...] = ()


@dataclass(frozen=True, slots=True)
class SafePatternItem:
    pattern_id: str
    title: str
    statement: str
    assessment_head_ids: tuple[str, ...]
    repository_count: int
    denominator: int
    confidence: str
    repository_aliases: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SafeObservationItem:
    observation_id: str
    title: str
    statement: str
    category: str
    repository_count: int
    denominator: int
    confidence: str
    repository_aliases: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    observation_label: str = "Observation, not a portfolio recommendation."


@dataclass(frozen=True, slots=True)
class SafeConfidenceBlock:
    level: str
    basis: tuple[str, ...]
    repository_sample_count: int
    comparable_repository_count: int
    dataset_coverage_status: str
    weakest_material_source_confidence: str
    limitations: tuple[str, ...] = ()
    disclaimer: str = "Confidence is not an accuracy percentage."


@dataclass(frozen=True, slots=True)
class SafeLimitationItem:
    category: str
    interpretation_severity: str
    statement: str
    affected_scope: tuple[str, ...] = ()
    remediation_or_interpretation: str | None = None


@dataclass(frozen=True, slots=True)
class SafeEntityItem:
    entity_kind: str
    entity_id: str
    label: str | None = None


@dataclass(frozen=True, slots=True)
class SafeDrilldownSection:
    drilldown_id: str
    repository_alias: str
    source_type: str
    technology_summary: tuple[str, ...]
    head_snapshots: tuple[SafeCapabilityRow, ...]
    recurring_pattern_ids: tuple[str, ...]
    modernization_observation_ids: tuple[str, ...]
    finding_refs: tuple[SafeEntityItem, ...]
    recommendation_refs: tuple[SafeEntityItem, ...]
    priority_action_ids: tuple[str, ...]
    roadmap_ids: tuple[str, ...]
    confidence: str
    limitations: tuple[str, ...]
    canonical_assessment_availability: str
    truncation_note: str | None = None


@dataclass(frozen=True, slots=True)
class SafeMethodologyBlock:
    assessment_schema_versions: tuple[str, ...]
    interpretation_policy_bundle_id: str
    export_policy_id: str
    aggregation_policy_id: str
    notes: tuple[str, ...]
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SafeExportMetadata:
    export_id: str
    export_schema_version: str
    source_report_id: str
    source_eir_schema_version: str
    interpretation_policy_bundle_id: str
    export_policy_id: str
    classification: str
    html_template_version: str
    json_projection_version: str
    generated_at: str | None = None


@dataclass(frozen=True, slots=True)
class WebsiteSafeExportDocument:
    """Allowlisted website-safe projection — not the internal EIR."""

    report_id: str
    export_schema_version: str
    report_schema_version: str
    title: str
    scope: str
    classification: str
    dataset_summary: Mapping[str, object] = field(default_factory=dict)
    methodology: SafeMethodologyBlock | None = None
    repository_population: tuple[tuple[str, str], ...] = ()
    technology_distribution: tuple[SafeTechnologyRow, ...] = ()
    capability_comparisons: tuple[SafeCapabilityRow, ...] = ()
    assessment_head_distributions: tuple[SafeHeadDistributionRow, ...] = ()
    recurring_patterns: tuple[SafePatternItem, ...] = ()
    modernization_observations: tuple[SafeObservationItem, ...] = ()
    confidence: SafeConfidenceBlock | None = None
    limitations: tuple[SafeLimitationItem, ...] = ()
    repository_drilldowns: tuple[SafeDrilldownSection, ...] = ()
    export_metadata: SafeExportMetadata | None = None
    orientation: tuple[str, ...] = ()
    empty_section_notes: tuple[str, ...] = ()
    export_limitations: tuple[str, ...] = ()
