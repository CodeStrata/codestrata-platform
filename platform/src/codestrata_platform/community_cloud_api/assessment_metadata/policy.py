"""Community Cloud assessment metadata policy (Slice 7.8)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.assessment_metadata.enums import (
    AssessmentDurationBucket,
    AssessmentExecutionResult,
    AssessmentFailureCategory,
    AssessmentHead,
    AssessmentHeadConfidenceLevel,
    AssessmentMode,
    AssessmentStatus,
    CountBucket,
    FindingAggregateCategory,
    FindingAggregateSeverity,
    PackageEcosystem,
    PrimaryLanguage,
    RepositoryShape,
)
from codestrata_platform.community_cloud_api.telemetry.enums import TelemetryClientName

# Baseline remains 1.0 (old clients / registry default). Latest additive is 1.1.
COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION = "1.0"
COMMUNITY_ASSESSMENT_METADATA_LATEST_SCHEMA_VERSION = "1.1"
COMMUNITY_ASSESSMENT_METADATA_SUPPORTED_SCHEMA_VERSIONS: frozenset[str] = frozenset(
    {
        COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION,
        COMMUNITY_ASSESSMENT_METADATA_LATEST_SCHEMA_VERSION,
    }
)
COMMUNITY_ASSESSMENT_METADATA_POLICY_ID = "community-assessment-metadata-policy"
# Policy URN stays on 1.0 — additive 1.1 fields expand the same privacy policy.
COMMUNITY_ASSESSMENT_METADATA_POLICY_VERSION = "1.0"
COMMUNITY_ASSESSMENT_METADATA_POLICY_URN = (
    f"{COMMUNITY_ASSESSMENT_METADATA_POLICY_ID}:"
    f"{COMMUNITY_ASSESSMENT_METADATA_POLICY_VERSION}"
)

# Informational Engine report schema versions accepted by this metadata contract.
ALLOWED_ASSESSMENT_SCHEMA_VERSIONS: tuple[str, ...] = ("1.2",)

FORBIDDEN_FIELD_NAMES: tuple[str, ...] = (
    "account_id",
    "branch",
    "command",
    "command_args",
    "commit",
    "commit_sha",
    "cost",
    "dependencies",
    "email",
    "error_message",
    "evidence",
    "exception",
    "file_names",
    "findings",
    "frameworks",
    "model",
    "module_names",
    "organization",
    "origin",
    "package_names",
    "path",
    "priority_actions",
    "prompt",
    "provider",
    "recommendations",
    "remote",
    "repository_id",
    "repository_name",
    "repository_url",
    "response",
    "roadmap",
    "root_path",
    "snippet",
    "snippets",
    "source",
    "source_code",
    "source_files",
    "stack_trace",
    "technologies",
    "token_count",
    "user",
    "username",
    "working_directory",
    "workspace",
    # Epic 20.4 / 20.7 privacy canaries (additive names).
    "graph",
    "report_id",
    "report_url",
)


@dataclass(frozen=True, slots=True)
class CommunityAssessmentMetadataPolicy:
    """Deterministic privacy-first assessment metadata policy."""

    policy_id: str = COMMUNITY_ASSESSMENT_METADATA_POLICY_ID
    policy_version: str = COMMUNITY_ASSESSMENT_METADATA_POLICY_VERSION
    schema_version: str = COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION
    supported_schema_versions: tuple[str, ...] = tuple(
        sorted(COMMUNITY_ASSESSMENT_METADATA_SUPPORTED_SCHEMA_VERSIONS)
    )
    allowed_clients: tuple[str, ...] = tuple(
        sorted(item.value for item in TelemetryClientName)
    )
    allowed_assessment_statuses: tuple[str, ...] = tuple(
        sorted(item.value for item in AssessmentStatus)
    )
    allowed_assessment_modes: tuple[str, ...] = tuple(
        sorted(item.value for item in AssessmentMode)
    )
    allowed_heads: tuple[str, ...] = tuple(sorted(item.value for item in AssessmentHead))
    allowed_repository_shapes: tuple[str, ...] = tuple(
        sorted(item.value for item in RepositoryShape)
    )
    allowed_primary_languages: tuple[str, ...] = tuple(
        sorted(item.value for item in PrimaryLanguage)
    )
    allowed_package_ecosystems: tuple[str, ...] = tuple(
        sorted(item.value for item in PackageEcosystem)
    )
    allowed_assessment_schema_versions: tuple[str, ...] = ALLOWED_ASSESSMENT_SCHEMA_VERSIONS
    allowed_finding_severities: tuple[str, ...] = tuple(
        sorted(item.value for item in FindingAggregateSeverity)
    )
    allowed_finding_categories: tuple[str, ...] = tuple(
        sorted(item.value for item in FindingAggregateCategory)
    )
    allowed_confidence_levels: tuple[str, ...] = tuple(
        sorted(item.value for item in AssessmentHeadConfidenceLevel)
    )
    allowed_failure_categories: tuple[str, ...] = tuple(
        sorted(item.value for item in AssessmentFailureCategory)
    )
    count_bucket_vocabulary: tuple[str, ...] = tuple(
        sorted(item.value for item in CountBucket)
    )
    duration_bucket_vocabulary: tuple[str, ...] = tuple(
        sorted(item.value for item in AssessmentDurationBucket)
    )
    execution_result_vocabulary: tuple[str, ...] = tuple(
        sorted(item.value for item in AssessmentExecutionResult)
    )
    maximum_head_count: int = len(AssessmentHead)
    maximum_language_label_length: int = 32
    maximum_count: int = 1_000_000
    maximum_artifact_count: int = 100
    maximum_finding_aggregates: int = 500
    maximum_head_confidence_rows: int = len(AssessmentHead)
    maximum_rule_id_length: int = 128
    allow_installation_id: bool = True
    forbidden_field_names: tuple[str, ...] = FORBIDDEN_FIELD_NAMES
    limitations: tuple[str, ...] = (
        "no_production_event_store",
        "no_exactly_once_guarantee",
        "sink_and_identity_record_not_atomic",
        "unauthenticated_endpoint",
        "no_rate_limiting",
        "aggregate_metadata_only",
        "no_report_or_finding_upload",
        "assessment_schema_version_allowlist_1_2",
        "supports_schema_1_0_and_1_1",
        "baseline_schema_remains_1_0",
        "no_client_emission_wiring",
    )

    def __post_init__(self) -> None:
        if self.policy_id != COMMUNITY_ASSESSMENT_METADATA_POLICY_ID:
            raise ValueError("unsupported assessment metadata policy id")
        if self.policy_version != COMMUNITY_ASSESSMENT_METADATA_POLICY_VERSION:
            raise ValueError("unsupported assessment metadata policy version")
        supported = frozenset(self.supported_schema_versions)
        if supported != COMMUNITY_ASSESSMENT_METADATA_SUPPORTED_SCHEMA_VERSIONS:
            raise ValueError("unsupported assessment metadata supported schema set")
        if self.schema_version not in supported:
            raise ValueError("unsupported assessment metadata schema version in policy")
        if self.maximum_head_count < 1 or self.maximum_count < 1:
            raise ValueError("invalid assessment metadata bounds")
        object.__setattr__(
            self, "supported_schema_versions", tuple(sorted(self.supported_schema_versions))
        )
        object.__setattr__(self, "allowed_clients", tuple(sorted(self.allowed_clients)))
        object.__setattr__(
            self, "allowed_assessment_statuses", tuple(sorted(self.allowed_assessment_statuses))
        )
        object.__setattr__(
            self, "allowed_assessment_modes", tuple(sorted(self.allowed_assessment_modes))
        )
        object.__setattr__(self, "allowed_heads", tuple(sorted(self.allowed_heads)))
        object.__setattr__(
            self, "allowed_repository_shapes", tuple(sorted(self.allowed_repository_shapes))
        )
        object.__setattr__(
            self, "allowed_primary_languages", tuple(sorted(self.allowed_primary_languages))
        )
        object.__setattr__(
            self,
            "allowed_package_ecosystems",
            tuple(sorted(self.allowed_package_ecosystems)),
        )
        object.__setattr__(
            self,
            "allowed_assessment_schema_versions",
            tuple(sorted(self.allowed_assessment_schema_versions)),
        )
        object.__setattr__(
            self, "forbidden_field_names", tuple(sorted(set(self.forbidden_field_names)))
        )
        object.__setattr__(self, "limitations", tuple(sorted(self.limitations)))

    @property
    def policy_token(self) -> str:
        return f"{self.policy_id}:{self.policy_version}"

    @classmethod
    def default(cls) -> CommunityAssessmentMetadataPolicy:
        return cls()

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "allow_installation_id": self.allow_installation_id,
            "allowed_assessment_modes": list(self.allowed_assessment_modes),
            "allowed_assessment_schema_versions": list(
                self.allowed_assessment_schema_versions
            ),
            "allowed_assessment_statuses": list(self.allowed_assessment_statuses),
            "allowed_clients": list(self.allowed_clients),
            "allowed_confidence_levels": list(self.allowed_confidence_levels),
            "allowed_failure_categories": list(self.allowed_failure_categories),
            "allowed_finding_categories": list(self.allowed_finding_categories),
            "allowed_finding_severities": list(self.allowed_finding_severities),
            "allowed_heads": list(self.allowed_heads),
            "allowed_package_ecosystems": list(self.allowed_package_ecosystems),
            "allowed_primary_languages": list(self.allowed_primary_languages),
            "allowed_repository_shapes": list(self.allowed_repository_shapes),
            "count_bucket_vocabulary": list(self.count_bucket_vocabulary),
            "duration_bucket_vocabulary": list(self.duration_bucket_vocabulary),
            "execution_result_vocabulary": list(self.execution_result_vocabulary),
            "forbidden_field_names": list(self.forbidden_field_names),
            "limitations": list(self.limitations),
            "maximum_artifact_count": self.maximum_artifact_count,
            "maximum_count": self.maximum_count,
            "maximum_finding_aggregates": self.maximum_finding_aggregates,
            "maximum_head_confidence_rows": self.maximum_head_confidence_rows,
            "maximum_head_count": self.maximum_head_count,
            "maximum_language_label_length": self.maximum_language_label_length,
            "maximum_rule_id_length": self.maximum_rule_id_length,
            "policy_id": self.policy_id,
            "policy_token": self.policy_token,
            "policy_version": self.policy_version,
            "schema_version": self.schema_version,
            "supported_schema_versions": list(self.supported_schema_versions),
        }


def default_assessment_metadata_policy() -> CommunityAssessmentMetadataPolicy:
    return CommunityAssessmentMetadataPolicy.default()
