"""Test-only fake Community Cloud credentials (never emitted in reports)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.authentication import (
    CommunityAuthenticationPolicy,
    InMemoryCommunityCredentialVerifier,
)

from verification.community_cloud_api.contract import (
    TEST_CLI_TOKEN,
    TEST_CURSOR_TOKEN,
    TEST_VSCODE_TOKEN,
)


def auth_headers(token: str = TEST_CLI_TOKEN) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def build_test_verifier(
    *,
    policy: CommunityAuthenticationPolicy | None = None,
    shared_scope: bool = False,
) -> InMemoryCommunityCredentialVerifier:
    active = policy or CommunityAuthenticationPolicy.default()
    verifier = InMemoryCommunityCredentialVerifier(policy=active)
    cli_scope = "rlscope-cli-shared" if shared_scope else "rlscope-cli-shared"
    verifier.register(
        TEST_CLI_TOKEN,
        client_id="client-test-cli",
        client_type="codestrata_cli",
        rate_limit_scope_id=cli_scope,
        credential_id="cred-test-cli",
    )
    verifier.register(
        TEST_VSCODE_TOKEN,
        client_id="client-test-vscode",
        client_type="vscode_extension",
        rate_limit_scope_id="rlscope-vscode-shared",
        credential_id="cred-test-vscode",
    )
    verifier.register(
        TEST_CURSOR_TOKEN,
        client_id="client-test-cursor",
        client_type="cursor_extension",
        rate_limit_scope_id="rlscope-cursor-shared",
        credential_id="cred-test-cursor",
    )
    return verifier


def token_for_kind(kind: str) -> str:
    if kind == "extension_events":
        return TEST_VSCODE_TOKEN
    return TEST_CLI_TOKEN
