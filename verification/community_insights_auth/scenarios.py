"""Negative scenarios A–Z for Slice 15.9 auth."""

from __future__ import annotations

AUTH_SCENARIOS: tuple[tuple[str, str], ...] = tuple(
    (chr(ord("A") + i), msg)
    for i, msg in enumerate(
        [
            "Password value in frontend source",
            "Password value in Terraform defaults",
            "Session token stored in localStorage",
            "Session signing secret exposed to browser",
            "Wildcard CORS with credentials enabled",
            "Raw event endpoints exposed via auth routes",
            "Slice 15.10 started",
            "Production deployment enabled in policy",
            "Secret values committed to Git",
            "Individual user accounts enabled",
            "Cognito OAuth or social login enabled",
            "Session signing reuses dashboard password",
            "Aggregation layer verifies dashboard password",
            "Auth service embeds metric aggregation semantics",
            "AWS SDK added to Insights frontend",
            "Secrets Manager called from browser",
            "Verification run creates commit or deploy",
            "Verifier report is nondeterministic",
            "Report leaks secrets passwords or user paths",
            "Session cookie missing HttpOnly flag",
            "Session cookie missing Secure flag",
            "Session cookie missing SameSite Strict",
            "Overview API accessible without authentication",
            "Frontend secret storage enabled in policy",
            "Terraform enable_module true for auth infra",
            "IAM grants PutSecretValue to auth runtime",
        ]
    )
)
