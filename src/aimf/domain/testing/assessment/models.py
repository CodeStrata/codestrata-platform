"""Test assessment domain models (Phase 4.6.1).

Analytically empty foundation section. No inventories, hotspots, synthesis,
conclusions, recommendations, or report projection fields.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aimf.domain.graph.validation import as_tuple, optional_nonblank, require_nonblank
from aimf.domain.testing.assessment.enums import (
    TestAssessmentStatus,
    TestCoverageAreaStatus,
    TestCoverageMaturity,
    TestLimitationCategory,
    TestTraceabilityRelation,
)
from aimf.domain.testing.assessment.identifiers import (
    SCHEMA_NAME,
    SECTION_ID,
    SECTION_SCHEMA_VERSION,
)


class TestExecutionSummary(BaseModel):
    """Bounded technical execution summary for the Test section."""

    __test__ = False

    model_config = ConfigDict(frozen=True, extra="forbid")

    testing_rules_planned: int = Field(default=0, ge=0)
    rules_executed: int = Field(default=0, ge=0)
    rules_matched: int = Field(default=0, ge=0)
    rules_not_matched: int = Field(default=0, ge=0)
    rules_not_applicable: int = Field(default=0, ge=0)
    rules_failed: int = Field(default=0, ge=0)
    visible_finding_count: int = Field(default=0, ge=0)
    total_finding_count: int = Field(default=0, ge=0)
    findings_by_rule: dict[str, int] = Field(default_factory=dict)
    pack_id: str = ""
    pack_version: str = ""
    pack_enabled: bool = False

    @field_validator("findings_by_rule", mode="before")
    @classmethod
    def normalize_counts(cls, value: object) -> dict[str, int]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError("findings_by_rule must be a dictionary")
        return {
            str(key): int(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }


class TestCoverageArea(BaseModel):
    __test__ = False

    model_config = ConfigDict(frozen=True, extra="forbid")

    area_id: str
    status: TestCoverageAreaStatus = TestCoverageAreaStatus.UNKNOWN
    numerator: int | None = Field(default=None, ge=0)
    denominator: int | None = Field(default=None, ge=0)
    ratio: float | None = Field(default=None, ge=0.0, le=1.0)
    maturity: TestCoverageMaturity = TestCoverageMaturity.UNKNOWN
    limitations: tuple[str, ...] = ()
    provenance: str = "testing_assessment"

    @field_validator("area_id", "provenance", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="coverage area field")

    @field_validator("limitations", mode="before")
    @classmethod
    def normalize_limitations(cls, value: object) -> tuple[str, ...]:
        return tuple(str(item).strip() for item in as_tuple(value) if str(item).strip())


class TestCoverageSummary(BaseModel):
    __test__ = False

    model_config = ConfigDict(frozen=True, extra="forbid")

    areas: tuple[TestCoverageArea, ...] = ()

    @field_validator("areas", mode="before")
    @classmethod
    def normalize_areas(cls, value: object) -> tuple[object, ...]:
        return as_tuple(value)


class TestLimitation(BaseModel):
    __test__ = False

    model_config = ConfigDict(frozen=True, extra="forbid")

    limitation_id: str
    category: TestLimitationCategory
    summary: str
    affected_capability: str
    importance: str = "contextual"
    provenance: str = "testing_assessment"
    remediation_guidance: str | None = None

    @field_validator(
        "limitation_id",
        "summary",
        "affected_capability",
        "importance",
        "provenance",
        mode="before",
    )
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="limitation field")

    @field_validator("remediation_guidance", mode="before")
    @classmethod
    def normalize_optional(cls, value: object) -> str | None:
        if value is None:
            return None
        return optional_nonblank(str(value), label="remediation_guidance")


class TestTraceabilityEdge(BaseModel):
    __test__ = False

    model_config = ConfigDict(frozen=True, extra="forbid")

    edge_id: str
    relation: TestTraceabilityRelation
    source_id: str
    target_id: str

    @field_validator("edge_id", "source_id", "target_id", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="traceability field")


class TestTraceabilityIndex(BaseModel):
    __test__ = False

    model_config = ConfigDict(frozen=True, extra="forbid")

    edges: tuple[TestTraceabilityEdge, ...] = ()

    @field_validator("edges", mode="before")
    @classmethod
    def normalize_edges(cls, value: object) -> tuple[object, ...]:
        return as_tuple(value)

    @property
    def edge_count(self) -> int:
        return len(self.edges)


class TestAssessmentSection(BaseModel):
    """First-class Test section of a CodeStrata assessment (schema 1.0.0).

    Analytically empty foundation. No inventories, hotspots, synthesis, or
    report projection.
    """

    __test__ = False

    model_config = ConfigDict(frozen=True, extra="forbid")

    section_id: str = SECTION_ID
    schema_name: str = SCHEMA_NAME
    section_version: str = SECTION_SCHEMA_VERSION
    assessment_id: str
    status: TestAssessmentStatus
    capability: str = "testing"
    repository_id: str
    testing_pack_id: str | None = None
    testing_pack_version: str | None = None
    evidence_pipeline: str = "not_configured"
    graph_fingerprint: str = ""
    evidence_fingerprint: str = ""
    configuration_fingerprint: str = ""
    execution_summary: TestExecutionSummary = Field(
        default_factory=TestExecutionSummary
    )
    coverage: TestCoverageSummary = Field(default_factory=TestCoverageSummary)
    finding_ids: tuple[str, ...] = ()
    all_finding_ids: tuple[str, ...] = ()
    findings: tuple[str, ...] = ()
    limitations: tuple[TestLimitation, ...] = ()
    diagnostics: tuple[str, ...] = ()
    traceability: TestTraceabilityIndex = Field(default_factory=TestTraceabilityIndex)
    enterprise_context_used: bool = False
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator(
        "section_id",
        "schema_name",
        "section_version",
        "assessment_id",
        "capability",
        "repository_id",
        mode="before",
    )
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="testing section field")

    @field_validator("testing_pack_id", "testing_pack_version", mode="before")
    @classmethod
    def normalize_optional_pack(cls, value: object) -> str | None:
        if value is None:
            return None
        return optional_nonblank(str(value), label="pack field")

    @field_validator(
        "finding_ids",
        "all_finding_ids",
        "findings",
        "diagnostics",
        mode="before",
    )
    @classmethod
    def normalize_id_sequences(cls, value: object) -> tuple[str, ...]:
        return tuple(str(item).strip() for item in as_tuple(value) if str(item).strip())

    @field_validator("limitations", mode="before")
    @classmethod
    def normalize_object_sequences(cls, value: object) -> tuple[object, ...]:
        return as_tuple(value)

    @field_validator("metadata", mode="before")
    @classmethod
    def normalize_metadata(cls, value: object) -> dict[str, str]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError("metadata must be a dictionary")
        return {str(key): str(item) for key, item in sorted(value.items())}
