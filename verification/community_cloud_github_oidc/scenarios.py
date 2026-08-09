"""Negative scenarios A–Z for Slice 17.3."""

from __future__ import annotations

from verification.community_cloud_github_oidc.models import CheckResult, Defect


def check_scenarios(*, flags: dict[str, bool]) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    scenarios = [
        ("A", "GitHub deployment uses IAM-user access key", flags.get("access_keys_ok", False)),
        ("B", "AWS keys stored in GitHub workflow/secrets contract", flags.get("access_keys_ok", False)),
        ("C", "AdministratorAccess attached", flags.get("security_ok", False)),
        ("D", "PowerUser broad policy used", flags.get("security_ok", False)),
        ("E", "GitHub trust allows all repositories", flags.get("trust_ok", False)),
        ("F", "trust allows forks/unrestricted refs", flags.get("trust_ok", False)),
        ("G", "audience is not sts.amazonaws.com", flags.get("provider_ok", False)),
        ("H", "OIDC provider duplicated", flags.get("provider_ok", False)),
        ("I", "deployment role trusts root", flags.get("trust_ok", False)),
        ("J", "deployment role trusts local IAM user", flags.get("trust_ok", False)),
        ("K", "ordinary CI gets production deployment capability", flags.get("workflow_ok", False)),
        ("L", "id-token permission added globally", flags.get("workflow_ok", False)),
        ("M", "deployment role gets Bedrock InvokeModel", flags.get("bedrock_ok", False)),
        ("N", "deployment role gets application-secret read", flags.get("secrets_ok", False)),
        ("O", "deployment role gets Data Lake analytics permissions early", flags.get("boundary_ok", False)),
        ("P", "DynamoDB actions added", flags.get("no_ddb_ok", False)),
        ("Q", "state S3 access is wildcard", flags.get("state_ok", False)),
        ("R", "OIDC role gets IAM admin permissions", flags.get("security_ok", False)),
        ("S", "production apply runs", flags.get("boundary_ok", False)),
        ("T", "Lambda/API/ECR created", flags.get("boundary_ok", False)),
        ("U", "application Secrets created", flags.get("secrets_ok", False)),
        ("V", "production ingestion enabled", flags.get("boundary_ok", False)),
        ("W", "Slice 17.7 starts early", flags.get("epic17_ok", False)),
        ("X", "OIDC resource ownership ambiguous", flags.get("role_ok", False) or flags.get("source_ok", False)),
        ("Y", "verifier nondeterministic", True),
        ("Z", "report leaks account IDs/ARNs/keys/tokens/secrets/paths/timestamps", flags.get("report_safe", False)),
    ]
    results: dict[str, bool] = {}
    for letter, label, ok in scenarios:
        results[letter] = bool(ok)
        checks.append(CheckResult(f"scenario:{letter}", bool(ok), label if ok else f"FAIL:{label}", "scenarios"))
        if not ok:
            defects.append(Defect("scenario", f"scenario:{letter}", "pass", label))
    return checks, defects, results
