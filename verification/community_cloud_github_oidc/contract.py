"""Contract for Slice 17.3."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.community_cloud_github_oidc import (
    COMMUNITY_CLOUD_GITHUB_OIDC_ID,
    COMMUNITY_CLOUD_GITHUB_OIDC_VERSION,
)

SCHEMA_NAME = "community-cloud-github-oidc-verification"
SCHEMA_VERSION = "1.0.0"
SV173_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv17-3"
REPORT_JSON = "community-cloud-github-oidc-verification.json"
REPORT_MD = "community-cloud-github-oidc-verification.md"

POLICY_RELATIVE = "platform/policies/community_cloud_github_oidc_policy.json"
POLICY_SCHEMA = "community-cloud-github-oidc-policy:1.0"
REGISTER_RELATIVE = "platform/policies/codestrata_github_aws_identity_register.json"
CONTRACT_RELATIVE = "platform/contracts/community_cloud_github_oidc_verification.json"
BOOTSTRAP_ROOT = "infrastructure/bootstrap/github-oidc"
BOOTSTRAP_SCRIPT = "infrastructure/scripts/bootstrap-github-oidc.sh"
DOCS_RELATIVE = "infrastructure/docs/github-aws-oidc.md"
WORKFLOW_RELATIVE = ".github/workflows/aws-identity-check.yml"
CI_RELATIVE = ".github/workflows/ci.yml"
EVIDENCE_RELATIVE = "infrastructure/bootstrap/github-oidc/.local/bootstrap_evidence.json"
STATE_REGISTER_RELATIVE = "platform/policies/community_cloud_remote_state_register.json"

EXPECTED_REGION = "us-west-2"
EXPECTED_PROFILE = "codestrata_infra"
EXPECTED_REPO = "CodeStrata/codestrata-platform"
EXPECTED_ENV = "production"
EXPECTED_ROLE = "codestrata-github-actions-production"
EXPECTED_POLICY = "CodeStrataGitHubRemoteStateAccess"
EXPECTED_PROVIDER = "token.actions.githubusercontent.com"
EXPECTED_AUDIENCE = "sts.amazonaws.com"
EXPECTED_SUBJECT = f"repo:{EXPECTED_REPO}:environment:{EXPECTED_ENV}"


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv173Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = COMMUNITY_CLOUD_GITHUB_OIDC_ID
    package_version: str = COMMUNITY_CLOUD_GITHUB_OIDC_VERSION
    start_slice_17_3: bool = True
    start_slice_17_4: bool = True
    start_slice_17_5: bool = True
    start_slice_17_6: bool = True
    start_slice_17_7: bool = True
    start_slice_17_8: bool = False
    long_lived_keys_allowed: bool = False
    tofu_production_apply_allowed: bool = False
    region: str = EXPECTED_REGION


def default_contract() -> Sv173Contract:
    return Sv173Contract()
