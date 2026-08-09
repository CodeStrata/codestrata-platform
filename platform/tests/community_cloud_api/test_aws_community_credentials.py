"""Unit tests for AWS Secrets Manager Community credential verifier (Slice 17.7)."""

from __future__ import annotations

import json

from codestrata_platform.community_cloud_api.authentication.aws_credentials import (
    AwsCommunityCredentialVerifier,
    parse_community_credentials_secret,
)
from codestrata_platform.community_cloud_api.authentication.credentials import (
    CommunityClientCredential,
    fingerprint_credential,
)
from codestrata_platform.community_cloud_api.authentication.policy import (
    default_authentication_policy,
)
from codestrata_platform.community_cloud_api.insights_auth.secrets import FakeSecretsPort

from .auth_test_support import TEST_CLI_TOKEN


def _secret_json_for_token(token: str) -> str:
    policy = default_authentication_policy()
    fp = fingerprint_credential(token, policy=policy)
    payload = {
        "credentials": [
            {
                "credential_fingerprint": fp,
                "client_id": "client-prod-cli",
                "client_type": "codestrata_cli",
                "credential_id": "cred-prod-cli",
                "rate_limit_scope_id": "rlscope-prod-cli",
                "status": "active",
                "allowed_route_groups": ["ingestion"],
                "credential_version": "1",
            }
        ]
    }
    return json.dumps(payload, sort_keys=True)


def test_parse_rejects_raw_token_in_secret() -> None:
    bad = json.dumps(
        {
            "credentials": [
                {
                    "credential_fingerprint": TEST_CLI_TOKEN,
                    "client_id": "x",
                    "client_type": "codestrata_cli",
                    "credential_id": "y",
                    "rate_limit_scope_id": "z",
                    "status": "active",
                    "allowed_route_groups": ["ingestion"],
                    "credential_version": "1",
                }
            ]
        }
    )
    assert parse_community_credentials_secret(bad) is None


def test_aws_verifier_active_match() -> None:
    secret_id = "codestrata/community/client-credentials"
    secrets = FakeSecretsPort({secret_id: _secret_json_for_token(TEST_CLI_TOKEN)})
    verifier = AwsCommunityCredentialVerifier(secrets=secrets, secret_id=secret_id)
    result = verifier.verify(CommunityClientCredential(_token=TEST_CLI_TOKEN))
    assert result.status == "active"
    assert result.record is not None
    assert result.record.client_type == "codestrata_cli"


def test_aws_verifier_unknown_token() -> None:
    secret_id = "codestrata/community/client-credentials"
    secrets = FakeSecretsPort({secret_id: _secret_json_for_token(TEST_CLI_TOKEN)})
    verifier = AwsCommunityCredentialVerifier(secrets=secrets, secret_id=secret_id)
    result = verifier.verify(
        CommunityClientCredential(_token="cscc_v1_UNKNOWN_TOKEN_VALUE_ZZZZ")
    )
    assert result.status == "unknown"


def test_aws_verifier_fail_closed_on_missing_secret() -> None:
    secrets = FakeSecretsPort({})
    verifier = AwsCommunityCredentialVerifier(
        secrets=secrets, secret_id="codestrata/community/client-credentials"
    )
    result = verifier.verify(CommunityClientCredential(_token=TEST_CLI_TOKEN))
    assert result.status == "unavailable"


def test_aws_verifier_fail_closed_on_malformed_secret() -> None:
    secret_id = "codestrata/community/client-credentials"
    secrets = FakeSecretsPort({secret_id: "{not-json"})
    verifier = AwsCommunityCredentialVerifier(secrets=secrets, secret_id=secret_id)
    result = verifier.verify(CommunityClientCredential(_token=TEST_CLI_TOKEN))
    assert result.status == "unavailable"
