"""Strategic Portfolio Roadmap read models (on-read projections)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class RoadmapInitiativeCategory(StrEnum):
    MODERNIZATION = "modernization"
    ENGINEERING = "engineering"
    GOVERNANCE = "governance"
    ARCHITECTURE = "architecture"
    PLATFORM_ENGINEERING = "platform_engineering"
    CLOUD = "cloud"
    AI_ADOPTION = "ai_adoption"
    TECHNICAL_DEBT = "technical_debt"
    SECURITY = "security"
    DEPENDENCY = "dependency"
    STANDARDIZATION = "standardization"


class RoadmapEffortBand(StrEnum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    STRATEGIC = "strategic"


class RoadmapWave(StrEnum):
    WAVE_1 = "wave_1"
    WAVE_2 = "wave_2"
    WAVE_3 = "wave_3"
    WAVE_4 = "wave_4"


STRATEGIC_ROADMAP_SCHEMA_VERSION = "strategic-roadmap-v1"
STRATEGIC_ROADMAP_POLICY_VERSION = "strategic-roadmap-policy-v1"


@dataclass(frozen=True, slots=True)
class RoadmapIdentity:
    executive_intelligence_id: str
    organization_id: str
    workspace_id: str
    portfolio_id: str
    portfolio_snapshot_id: str
    portfolio_snapshot_version: int
    executive_version: int
    projection_completed_at: datetime | None
    schema_version: str
    policy_version: str
    source_policy_version: str
    source_schema_version: str


@dataclass(frozen=True, slots=True)
class RoadmapInitiative:
    initiative_id: str
    title: str
    category: RoadmapInitiativeCategory
    description: str
    rationale: str
    affected_repository_ids: tuple[str, ...]
    supporting_finding_ids: tuple[str, ...]
    supporting_recommendation_ids: tuple[str, ...]
    expected_impact: str
    confidence: float
    confidence_band: str
    coverage: float
    limitations: tuple[str, ...]
    priority: int
    effort_band: RoadmapEffortBand
    sequencing_wave: RoadmapWave
    related_initiative_ids: tuple[str, ...]
    depends_on_initiative_ids: tuple[str, ...]
    priority_inputs: tuple[str, ...]
    effort_rule: str
    wave_rule: str


@dataclass(frozen=True, slots=True)
class RoadmapWaveBucket:
    wave: RoadmapWave
    title: str
    description: str
    initiative_ids: tuple[str, ...]
    initiative_count: int


@dataclass(frozen=True, slots=True)
class RoadmapSummary:
    initiative_count: int
    effort_distribution: tuple[tuple[str, int], ...]
    wave_distribution: tuple[tuple[str, int], ...]
    category_distribution: tuple[tuple[str, int], ...]
    portfolio_investment_themes: tuple[str, ...]
    strategic_observations: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StrategicRoadmapModel:
    identity: RoadmapIdentity
    summary: RoadmapSummary
    initiatives: tuple[RoadmapInitiative, ...]
    waves: tuple[RoadmapWaveBucket, ...]
    limitations: tuple[str, ...]
