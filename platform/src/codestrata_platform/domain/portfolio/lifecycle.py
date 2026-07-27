"""Portfolio lifecycle and taxonomy enums."""

from __future__ import annotations

from enum import StrEnum


class PortfolioStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class PortfolioSnapshotStatus(StrEnum):
    PENDING = "pending"
    AGGREGATING = "aggregating"
    COMPLETED = "completed"
    FAILED = "failed"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class RepositoryAvailabilityStatus(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class RepositoryCriticality(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MISSION_CRITICAL = "mission_critical"
    UNSPECIFIED = "unspecified"


class TechnologyStandardizationStatus(StrEnum):
    STANDARD = "standard"
    PREFERRED = "preferred"
    COMMON = "common"
    FRAGMENTED = "fragmented"
    ISOLATED = "isolated"
    UNKNOWN = "unknown"


class TechnologyLifecycleSignal(StrEnum):
    CURRENT = "current"
    AGING = "aging"
    OBSOLETE = "obsolete"
    UNKNOWN = "unknown"


class PriorityBand(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ModernizationTheme(StrEnum):
    STANDARDIZE_TECHNOLOGY = "standardize_technology"
    REDUCE_TECHNICAL_DEBT = "reduce_technical_debt"
    REMEDIATE_SECURITY_RISK = "remediate_security_risk"
    IMPROVE_ARCHITECTURE = "improve_architecture"
    UPGRADE_DEPENDENCIES = "upgrade_dependencies"
    IMPROVE_CLOUD_READINESS = "improve_cloud_readiness"
    IMPROVE_OBSERVABILITY = "improve_observability"
    CONSOLIDATE_DUPLICATION = "consolidate_duplication"
    IMPROVE_DOCUMENTATION = "improve_documentation"
    ADDRESS_COMPLIANCE_GAPS = "address_compliance_gaps"


class ModernizationWave(StrEnum):
    WAVE_1 = "wave_1"
    WAVE_2 = "wave_2"
    WAVE_3 = "wave_3"
    DEFERRED = "deferred"
    UNCLASSIFIED = "unclassified"


class AssessmentFreshnessStatus(StrEnum):
    CURRENT = "current"
    AGING = "aging"
    STALE = "stale"
    UNKNOWN = "unknown"


class DependencySignalType(StrEnum):
    EXPLICIT_REPOSITORY_DEPENDENCY = "explicit_repository_dependency"
    SHARED_TECHNOLOGY = "shared_technology"
    SHARED_FRAMEWORK = "shared_framework"
    SHARED_INFRASTRUCTURE = "shared_infrastructure"
    SHARED_RISK = "shared_risk"
    SHARED_RECOMMENDATION = "shared_recommendation"


class PortfolioStalenessReason(StrEnum):
    REPOSITORY_SNAPSHOT_CHANGED = "repository_snapshot_changed"
    REPOSITORY_ADDED = "repository_added"
    REPOSITORY_REMOVED = "repository_removed"
    AGGREGATION_POLICY_CHANGED = "aggregation_policy_changed"
