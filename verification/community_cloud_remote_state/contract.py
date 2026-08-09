"""Contract for Slice 17.2."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.community_cloud_remote_state import (
    COMMUNITY_CLOUD_REMOTE_STATE_ID,
    COMMUNITY_CLOUD_REMOTE_STATE_VERSION,
)

SCHEMA_NAME = "community-cloud-remote-state-verification"
SCHEMA_VERSION = "1.0.0"
SV172_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv17-2"
REPORT_JSON = "community-cloud-remote-state-verification.json"
REPORT_MD = "community-cloud-remote-state-verification.md"

POLICY_RELATIVE = "platform/policies/community_cloud_remote_state_policy.json"
POLICY_SCHEMA = "community-cloud-remote-state-policy:1.0"
REGISTER_RELATIVE = "platform/policies/community_cloud_remote_state_register.json"
CONTRACT_RELATIVE = "platform/contracts/community_cloud_remote_state_verification.json"
BOOTSTRAP_ROOT = "infrastructure/bootstrap/remote-state"
BOOTSTRAP_SCRIPT = "infrastructure/scripts/bootstrap-remote-state.sh"
STATE_KEY = "codestrata/community-cloud/production/terraform.tfstate"
EXPECTED_REGION = "us-west-2"
EXPECTED_PROFILE = "codestrata_infra"
EVIDENCE_RELATIVE = "infrastructure/bootstrap/remote-state/.local/bootstrap_evidence.json"


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv172Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = COMMUNITY_CLOUD_REMOTE_STATE_ID
    package_version: str = COMMUNITY_CLOUD_REMOTE_STATE_VERSION
    start_slice_17_2: bool = True
    start_slice_17_3: bool = True
    region: str = EXPECTED_REGION
    use_lockfile: bool = True
    dynamodb_required: bool = False
    tofu_production_apply_allowed: bool = False


def default_contract() -> Sv172Contract:
    return Sv172Contract()
