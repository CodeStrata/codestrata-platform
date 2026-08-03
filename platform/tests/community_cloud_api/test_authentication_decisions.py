"""Authentication decision serialization tests."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.authentication.decisions import (
    DECISION_AUTHENTICATED,
    DECISION_INVALID,
    AuthenticationDecision,
)
from codestrata_platform.community_cloud_api.authentication.models import (
    AuthenticatedCommunityClient,
)


def test_decision_serialization_excludes_secrets() -> None:
    principal = AuthenticatedCommunityClient(
        client_id="client-opaque",
        client_type="codestrata_cli",
        credential_id="cred-1",
        credential_version="1",
        status="active",
        rate_limit_scope_id="scope-1",
    )
    decision = AuthenticationDecision(
        status=DECISION_AUTHENTICATED,
        authenticated=True,
        principal=principal,
        safe_client_reference="client-abcdef123456",
        reason="authenticated",
        policy_id="community-authentication-policy",
        verifier_status="active",
    )
    payload = decision.to_stable_dict()
    assert "client-opaque" not in str(payload)
    assert "scope-1" not in str(payload)
    assert payload["safe_client_reference"] == "client-abcdef123456"
    assert payload["client_type"] == "codestrata_cli"

    failed = AuthenticationDecision(
        status=DECISION_INVALID,
        authenticated=False,
        principal=None,
        safe_client_reference=None,
        reason="invalid_client_credential",
        policy_id="community-authentication-policy",
        verifier_status="unknown",
    )
    assert "cred:" not in str(failed.to_stable_dict())
