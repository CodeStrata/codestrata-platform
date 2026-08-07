"""Test-only Community client credential helpers (obviously non-production)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.authentication import (
    CommunityAuthenticationPolicy,
    InMemoryCommunityCredentialVerifier,
)

# Obviously fake — never use as production credentials.
TEST_CLI_TOKEN = "cscc_v1_TEST_ONLY_CLI_TOKEN_AAAA"
TEST_VSCODE_TOKEN = "cscc_v1_TEST_ONLY_VSCODE_TOKEN_BB"
# Retired cursor_extension token constant retained for historical test references only.
TEST_CURSOR_TOKEN = "cscc_v1_TEST_ONLY_CURSOR_TOKEN_CC"


def auth_headers(token: str = TEST_CLI_TOKEN) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def disabled_authentication_policy() -> CommunityAuthenticationPolicy:
    """Explicit test/local disable — never implicit via environment."""

    return CommunityAuthenticationPolicy(enabled=False)


def build_test_verifier(
    *,
    policy: CommunityAuthenticationPolicy | None = None,
) -> InMemoryCommunityCredentialVerifier:
    active = policy or CommunityAuthenticationPolicy.default()
    verifier = InMemoryCommunityCredentialVerifier(policy=active)
    verifier.register(
        TEST_CLI_TOKEN,
        client_id="client-test-cli",
        client_type="codestrata_cli",
        rate_limit_scope_id="rlscope-cli-shared",
        credential_id="cred-test-cli",
    )
    verifier.register(
        TEST_VSCODE_TOKEN,
        client_id="client-test-vscode",
        client_type="vscode_extension",
        rate_limit_scope_id="rlscope-vscode-shared",
        credential_id="cred-test-vscode",
    )
    # Retired cursor_extension credentials are not issuable (Slice 12.4).
    return verifier
