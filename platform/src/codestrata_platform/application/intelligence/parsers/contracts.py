"""Parser contracts for assessment intelligence artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from codestrata_platform.domain.artifact.enums import ArtifactType


@dataclass(frozen=True, slots=True)
class ParsedEvidenceReference:
    path_reference: str
    line_start: int | None = None
    line_end: int | None = None
    symbol: str | None = None
    component: str | None = None
    evidence_type: str | None = None
    checksum: str | None = None
    redacted_excerpt: str | None = None
    source_artifact_id: str | None = None


@dataclass(frozen=True, slots=True)
class ParsedFinding:
    finding_id: str
    rule_id: str
    title: str
    summary: str
    category: str
    severity: str
    confidence: float
    production_scope: str | None = None
    affected_component: str | None = None
    affected_path_reference: str | None = None
    evidence_references: tuple[ParsedEvidenceReference, ...] = ()
    remediation_reference: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ParsedRecommendation:
    recommendation_id: str
    title: str
    rationale: str
    priority: str
    category: str
    effort: str | None = None
    impact: str | None = None
    dependencies: tuple[str, ...] = ()
    related_finding_ids: tuple[str, ...] = ()
    roadmap_horizon: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ParsedMetric:
    name: str
    kind: str
    value: str
    unit: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ParsedAssessmentIntelligence:
    schema_version: str
    findings: tuple[ParsedFinding, ...] = ()
    metrics: tuple[ParsedMetric, ...] = ()
    recommendations: tuple[ParsedRecommendation, ...] = ()
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ArtifactValidationResult:
    artifact_type: ArtifactType
    schema_version: str
    is_valid: bool
    reason: str | None = None


class AssessmentArtifactParser(Protocol):
    artifact_type: ArtifactType

    def parse(
        self,
        *,
        schema_version: str,
        content: bytes,
        source_artifact_id: str,
    ) -> ParsedAssessmentIntelligence: ...


class ArtifactSchemaDetector(Protocol):
    def detect(self, *, artifact_type: ArtifactType, content: bytes) -> str: ...
