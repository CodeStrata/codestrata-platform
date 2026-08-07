"""Community retired-client policy (Slice 12.4).

Separates active Community product clients from retired historical client
values. Schema 1.0 request models may still deserialize historical
``cursor_extension`` records (Approach A); current ingestion policy, active
envelope construction, and active storage projection reject retired clients.

This policy is independently versioned and does not bump Community Cloud
endpoint schemas or Data Lake envelope schemas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

COMMUNITY_RETIRED_CLIENT_POLICY_ID = "community-retired-client-policy"
COMMUNITY_RETIRED_CLIENT_POLICY_VERSION = "1.0"
COMMUNITY_RETIRED_CLIENT_POLICY_URN = (
    f"{COMMUNITY_RETIRED_CLIENT_POLICY_ID}:{COMMUNITY_RETIRED_CLIENT_POLICY_VERSION}"
)

RETIRED_CLIENT_CURSOR_EXTENSION = "cursor_extension"

# Bounded reason codes — never echo raw client values in diagnostics.
REASON_RETIRED_CLIENT = "retired_client"
REASON_UNSUPPORTED_ACTIVE_CLIENT = "unsupported_active_client"
REASON_HISTORICAL_CLIENT_RECORD = "historical_client_record"
REASON_CLIENT_CONTRACT_MISMATCH = "client_contract_mismatch"

RETIREMENT_STATUS_RETIRED = "retired"


@dataclass(frozen=True, slots=True)
class CommunityRetiredClientPolicy:
    """Deterministic retirement posture for formerly accepted clients."""

    policy_id: str = COMMUNITY_RETIRED_CLIENT_POLICY_ID
    policy_version: str = COMMUNITY_RETIRED_CLIENT_POLICY_VERSION
    retired_client: str = RETIRED_CLIENT_CURSOR_EXTENSION
    retirement_status: str = RETIREMENT_STATUS_RETIRED
    active_emission_allowed: bool = False
    current_ingestion_allowed: bool = False
    historical_deserialization_allowed: bool = True
    historical_storage_validation_allowed: bool = True
    rewrite_required: bool = False
    migration_required: bool = False
    limitations: tuple[str, ...] = (
        "no_active_cursor_emitter",
        "no_current_api_acceptance",
        "no_active_envelope_construction",
        "no_active_storage_projection",
        "no_stored_event_rewrite",
        "no_s3_migration",
        "schema_1_0_historical_deserialize_retained",
        "production_ingestion_remain_fail_closed",
    )

    def __post_init__(self) -> None:
        if self.policy_id != COMMUNITY_RETIRED_CLIENT_POLICY_ID:
            raise ValueError("unsupported retired-client policy id")
        if self.policy_version != COMMUNITY_RETIRED_CLIENT_POLICY_VERSION:
            raise ValueError("unsupported retired-client policy version")
        if self.retired_client != RETIRED_CLIENT_CURSOR_EXTENSION:
            raise ValueError("unsupported retired client")
        if self.retirement_status != RETIREMENT_STATUS_RETIRED:
            raise ValueError("unsupported retirement status")
        if self.active_emission_allowed or self.current_ingestion_allowed:
            raise ValueError("retired client must not allow active emission or ingestion")
        if self.rewrite_required or self.migration_required:
            raise ValueError("retirement must not require rewrite or migration")
        object.__setattr__(self, "limitations", tuple(sorted(set(self.limitations))))

    @property
    def policy_token(self) -> str:
        return f"{self.policy_id}:{self.policy_version}"

    def is_retired_client(self, client_type: str) -> bool:
        return (client_type or "").strip() == self.retired_client

    def allows_historical_deserialize(self, client_type: str) -> bool:
        return self.historical_deserialization_allowed and self.is_retired_client(client_type)

    def allows_historical_storage_validation(self, client_type: str) -> bool:
        return self.historical_storage_validation_allowed and self.is_retired_client(client_type)

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "active_emission_allowed": self.active_emission_allowed,
            "current_ingestion_allowed": self.current_ingestion_allowed,
            "historical_deserialization_allowed": self.historical_deserialization_allowed,
            "historical_storage_validation_allowed": self.historical_storage_validation_allowed,
            "limitations": list(self.limitations),
            "migration_required": self.migration_required,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "retirement_status": self.retirement_status,
            "rewrite_required": self.rewrite_required,
            # Intentionally omit raw retired_client value from public dumps.
        }


def default_retired_client_policy() -> CommunityRetiredClientPolicy:
    return CommunityRetiredClientPolicy()
