"""Privacy-first assessment metadata ingestion (Slice 7.8)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.assessment_metadata.enums import (
    ASSESSMENT_METADATA_EVENT_TYPE,
    AssessmentDurationBucket,
    AssessmentExecutionResult,
    AssessmentHead,
    AssessmentMetadataIngestionStatus,
    AssessmentMetadataSinkStatus,
    AssessmentMode,
    AssessmentStatus,
    CountBucket,
    PrimaryLanguage,
    RepositoryShape,
)
from codestrata_platform.community_cloud_api.assessment_metadata.models import (
    AssessmentArtifactMetadata,
    AssessmentExecutionMetadata,
    AssessmentMetadataBlock,
    AssessmentMetadataRequest,
    RepositoryMetadata,
)
from codestrata_platform.community_cloud_api.assessment_metadata.policy import (
    COMMUNITY_ASSESSMENT_METADATA_POLICY_URN,
    COMMUNITY_ASSESSMENT_METADATA_POLICY_VERSION,
    COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION,
    CommunityAssessmentMetadataPolicy,
    default_assessment_metadata_policy,
)
from codestrata_platform.community_cloud_api.assessment_metadata.ports import (
    AssessmentMetadataSink,
    AssessmentMetadataSinkResult,
    InMemoryAssessmentMetadataSink,
    UnavailableAssessmentMetadataSink,
    ValidatedAssessmentMetadataEvent,
)
from codestrata_platform.community_cloud_api.assessment_metadata.responses import (
    AssessmentMetadataResponse,
)
from codestrata_platform.community_cloud_api.assessment_metadata.routes import (
    ASSESSMENT_METADATA_PATH,
    ASSESSMENT_METADATA_ROUTE_NAME,
    register_assessment_metadata_routes,
)
from codestrata_platform.community_cloud_api.assessment_metadata.service import (
    IngestAssessmentMetadata,
)

__all__ = [
    "ASSESSMENT_METADATA_EVENT_TYPE",
    "ASSESSMENT_METADATA_PATH",
    "ASSESSMENT_METADATA_ROUTE_NAME",
    "COMMUNITY_ASSESSMENT_METADATA_POLICY_URN",
    "COMMUNITY_ASSESSMENT_METADATA_POLICY_VERSION",
    "COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION",
    "AssessmentArtifactMetadata",
    "AssessmentDurationBucket",
    "AssessmentExecutionMetadata",
    "AssessmentExecutionResult",
    "AssessmentHead",
    "AssessmentMetadataBlock",
    "AssessmentMetadataIngestionStatus",
    "AssessmentMetadataRequest",
    "AssessmentMetadataResponse",
    "AssessmentMetadataSink",
    "AssessmentMetadataSinkResult",
    "AssessmentMetadataSinkStatus",
    "AssessmentMode",
    "AssessmentStatus",
    "CommunityAssessmentMetadataPolicy",
    "CountBucket",
    "InMemoryAssessmentMetadataSink",
    "IngestAssessmentMetadata",
    "PrimaryLanguage",
    "RepositoryMetadata",
    "RepositoryShape",
    "UnavailableAssessmentMetadataSink",
    "ValidatedAssessmentMetadataEvent",
    "default_assessment_metadata_policy",
    "register_assessment_metadata_routes",
]
