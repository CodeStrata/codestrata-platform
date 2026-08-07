"""community-infrastructure-repository-policy:1.0 (Slice 12.5)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from verification.infrastructure_repository_contract.contract import (
    DESTINATION_LAYOUT_DECISION,
    POLICY_ID,
    POLICY_VERSION,
    REPOSITORY_NAME,
    REPOSITORY_VISIBILITY,
    SOURCE_AUTHORITY_DECISION,
)


@dataclass(frozen=True, slots=True)
class CommunityInfrastructureRepositoryPolicy:
    policy_id: str = POLICY_ID
    policy_version: str = POLICY_VERSION
    repository_name: str = REPOSITORY_NAME
    visibility: str = REPOSITORY_VISIBILITY
    source_authority: str = SOURCE_AUTHORITY_DECISION
    destination_layout: str = DESTINATION_LAYOUT_DECISION
    export_direction: str = "one_way_main_to_destination_pre_cutover"
    git_operations_allowed: bool = False
    aws_operations_allowed: bool = False
    deployment_allowed: bool = False
    state_export_allowed: bool = False
    credential_export_allowed: bool = False
    deterministic_export_required: bool = True
    opentofu_validation_required: bool = True
    dual_authoring_allowed: bool = False
    source_deletion_before_cutover_allowed: bool = False
    limitations: tuple[str, ...] = (
        "destination_repository_not_yet_created",
        "exporter_not_yet_implemented",
        "opentofu_not_yet_validated_from_exported_destination",
        "shared_root_files_require_implementation_time_refinement",
        "documentation_links_require_export_time_rewriting",
        "source_removal_deferred_until_cutover",
        "ci_implementation_deferred_to_12_9",
        "no_remote_repository_url_configured",
    )

    def __post_init__(self) -> None:
        if self.policy_id != POLICY_ID:
            raise ValueError("unsupported policy id")
        if self.policy_version != POLICY_VERSION:
            raise ValueError("unsupported policy version")
        if self.visibility != "private":
            raise ValueError("infrastructure repository must be private")
        if self.repository_name != REPOSITORY_NAME:
            raise ValueError("unsupported repository name")
        if (
            self.git_operations_allowed
            or self.aws_operations_allowed
            or self.deployment_allowed
            or self.state_export_allowed
            or self.credential_export_allowed
            or self.dual_authoring_allowed
            or self.source_deletion_before_cutover_allowed
        ):
            raise ValueError("policy allows a forbidden operation")
        if not self.deterministic_export_required or not self.opentofu_validation_required:
            raise ValueError("deterministic export and OpenTofu validation required")
        object.__setattr__(self, "limitations", tuple(sorted(set(self.limitations))))

    @property
    def policy_token(self) -> str:
        return f"{self.policy_id}:{self.policy_version}"

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "aws_operations_allowed": self.aws_operations_allowed,
            "credential_export_allowed": self.credential_export_allowed,
            "deployment_allowed": self.deployment_allowed,
            "destination_layout": self.destination_layout,
            "deterministic_export_required": self.deterministic_export_required,
            "dual_authoring_allowed": self.dual_authoring_allowed,
            "export_direction": self.export_direction,
            "git_operations_allowed": self.git_operations_allowed,
            "limitations": list(self.limitations),
            "opentofu_validation_required": self.opentofu_validation_required,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "repository_name": self.repository_name,
            "source_authority": self.source_authority,
            "source_deletion_before_cutover_allowed": self.source_deletion_before_cutover_allowed,
            "state_export_allowed": self.state_export_allowed,
            "visibility": self.visibility,
        }


def default_infrastructure_repository_policy() -> CommunityInfrastructureRepositoryPolicy:
    return CommunityInfrastructureRepositoryPolicy()
