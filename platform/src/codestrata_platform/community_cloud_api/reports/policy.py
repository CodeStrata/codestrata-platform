"""Deterministic Community report publishing policy (Slice 17.16)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


COMMUNITY_REPORT_PUBLISHING_POLICY_ID = "community-report-publishing-policy"
COMMUNITY_REPORT_PUBLISHING_POLICY_VERSION = "1.0"
COMMUNITY_REPORT_PUBLISHING_POLICY_URN = (
    f"{COMMUNITY_REPORT_PUBLISHING_POLICY_ID}:{COMMUNITY_REPORT_PUBLISHING_POLICY_VERSION}"
)

PUBLIC_REPORTS_BASE_URL = "https://reports.codestrata.ai"
PUBLIC_REPORT_PATH_PREFIX = "/r/"

REPORT_TYPE_ASSESSMENT = "assessment"
REPORT_TYPE_EIR = "engineering_intelligence"
VALID_REPORT_TYPES = frozenset({REPORT_TYPE_ASSESSMENT, REPORT_TYPE_EIR})

LOGICAL_REPOSITORY = "repository"
LOGICAL_PORTFOLIO = "portfolio"

SLOT_CURRENT = "current"
SLOT_PREVIOUS = "previous"
MAX_CLOUD_VERSIONS = 2

STATUS_PUBLISHED = "published"
STATUS_REVOKED = "revoked"

ALLOWED_ASSESSMENT_ARTIFACTS = frozenset({"assessment.html", "assessment.json"})
ALLOWED_EIR_ARTIFACTS = frozenset(
    {
        "engineering-intelligence-report.html",
        "engineering-intelligence-report.json",
    }
)

MAX_ARTIFACT_BYTES = 12_000_000
MAX_ARTIFACTS_PER_PUBLISH = 2
UPLOAD_INTENT_TTL_SECONDS = 900
PRESIGN_TTL_SECONDS = 900


@dataclass(frozen=True, slots=True)
class CommunityReportPublishingPolicy:
    """Product policy for explicit cloud report publishing."""

    policy_id: str = COMMUNITY_REPORT_PUBLISHING_POLICY_ID
    policy_version: str = COMMUNITY_REPORT_PUBLISHING_POLICY_URN
    local_report_always_generated: bool = True
    telemetry_opt_in_required_for_cloud_publish: bool = True
    explicit_publish_action_required: bool = True
    automatic_publish_after_assessment: bool = False
    assessment_cloud_versions_per_repository: int = MAX_CLOUD_VERSIONS
    eir_cloud_versions_per_portfolio: int = MAX_CLOUD_VERSIONS
    report_artifact_store_separate_from_data_lake: bool = True
    report_artifact_store_private: bool = True
    raw_s3_urls_public: bool = False
    public_report_domain: str = PUBLIC_REPORTS_BASE_URL
    public_ids_opaque: bool = True
    public_read: bool = True
    publish_authenticated: bool = True
    revoke_authenticated: bool = True
    revocation_supported: bool = True
    start_slice_17_17: bool = False
    cache_max_age_seconds: int = 60

    def __post_init__(self) -> None:
        if self.policy_id != COMMUNITY_REPORT_PUBLISHING_POLICY_ID:
            raise ValueError("unsupported report publishing policy id")
        if self.policy_version != COMMUNITY_REPORT_PUBLISHING_POLICY_URN:
            raise ValueError("unsupported report publishing policy version")
        if not self.local_report_always_generated:
            raise ValueError("local_report_always_generated must be true")
        if not self.telemetry_opt_in_required_for_cloud_publish:
            raise ValueError("telemetry_opt_in_required_for_cloud_publish must be true")
        if not self.explicit_publish_action_required:
            raise ValueError("explicit_publish_action_required must be true")
        if self.automatic_publish_after_assessment:
            raise ValueError("automatic_publish_after_assessment must be false")
        if self.assessment_cloud_versions_per_repository != MAX_CLOUD_VERSIONS:
            raise ValueError("assessment_cloud_versions_per_repository must be 2")
        if self.eir_cloud_versions_per_portfolio != MAX_CLOUD_VERSIONS:
            raise ValueError("eir_cloud_versions_per_portfolio must be 2")
        if not self.report_artifact_store_separate_from_data_lake:
            raise ValueError("report_artifact_store_separate_from_data_lake must be true")
        if not self.report_artifact_store_private:
            raise ValueError("report_artifact_store_private must be true")
        if self.raw_s3_urls_public:
            raise ValueError("raw_s3_urls_public must be false")
        if self.public_report_domain != PUBLIC_REPORTS_BASE_URL:
            raise ValueError("public_report_domain mismatch")
        if not self.public_ids_opaque:
            raise ValueError("public_ids_opaque must be true")
        if not self.publish_authenticated or not self.revoke_authenticated:
            raise ValueError("publish and revoke must remain authenticated")
        if self.start_slice_17_17:
            raise ValueError("start_slice_17_17 must be false")

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "assessment_cloud_versions_per_repository": (
                self.assessment_cloud_versions_per_repository
            ),
            "automatic_publish_after_assessment": self.automatic_publish_after_assessment,
            "cache_max_age_seconds": self.cache_max_age_seconds,
            "eir_cloud_versions_per_portfolio": self.eir_cloud_versions_per_portfolio,
            "explicit_publish_action_required": self.explicit_publish_action_required,
            "local_report_always_generated": self.local_report_always_generated,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "public_ids_opaque": self.public_ids_opaque,
            "public_read": self.public_read,
            "public_report_domain": self.public_report_domain,
            "publish_authenticated": self.publish_authenticated,
            "raw_s3_urls_public": self.raw_s3_urls_public,
            "report_artifact_store_private": self.report_artifact_store_private,
            "report_artifact_store_separate_from_data_lake": (
                self.report_artifact_store_separate_from_data_lake
            ),
            "revoke_authenticated": self.revoke_authenticated,
            "revocation_supported": self.revocation_supported,
            "start_slice_17_17": self.start_slice_17_17,
            "telemetry_opt_in_required_for_cloud_publish": (
                self.telemetry_opt_in_required_for_cloud_publish
            ),
        }


def default_report_publishing_policy() -> CommunityReportPublishingPolicy:
    return CommunityReportPublishingPolicy()


def public_report_url(public_id: str) -> str:
    pid = (public_id or "").strip()
    return f"{PUBLIC_REPORTS_BASE_URL}{PUBLIC_REPORT_PATH_PREFIX}{pid}"


__all__ = [
    "ALLOWED_ASSESSMENT_ARTIFACTS",
    "ALLOWED_EIR_ARTIFACTS",
    "COMMUNITY_REPORT_PUBLISHING_POLICY_ID",
    "COMMUNITY_REPORT_PUBLISHING_POLICY_URN",
    "COMMUNITY_REPORT_PUBLISHING_POLICY_VERSION",
    "CommunityReportPublishingPolicy",
    "LOGICAL_PORTFOLIO",
    "LOGICAL_REPOSITORY",
    "MAX_ARTIFACTS_PER_PUBLISH",
    "MAX_ARTIFACT_BYTES",
    "MAX_CLOUD_VERSIONS",
    "PRESIGN_TTL_SECONDS",
    "PUBLIC_REPORTS_BASE_URL",
    "PUBLIC_REPORT_PATH_PREFIX",
    "REPORT_TYPE_ASSESSMENT",
    "REPORT_TYPE_EIR",
    "SLOT_CURRENT",
    "SLOT_PREVIOUS",
    "STATUS_PUBLISHED",
    "STATUS_REVOKED",
    "UPLOAD_INTENT_TTL_SECONDS",
    "VALID_REPORT_TYPES",
    "default_report_publishing_policy",
    "public_report_url",
]
