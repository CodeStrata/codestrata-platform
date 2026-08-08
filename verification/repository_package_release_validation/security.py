"""Security validation of exported trees."""

from __future__ import annotations

import re
from pathlib import Path

from verification.repository_package_release_validation.helpers import add_check
from verification.repository_package_release_validation.models import CheckResult, Defect

# High-confidence real secret material (not detector fixtures / test payloads).
SECRET_PATTERNS = (
    r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----\n(?:(?!-----END).){64,}",
    r"(?i)aws_secret_access_key\s*[=:]\s*['\"]?[A-Za-z0-9/+=]{40,}",
    r"(?i)ghp_[A-Za-z0-9]{36,}",
    r"(?i)xox[baprs]-[A-Za-z0-9-]{20,}",
)
PATH_PATTERNS = (
    r"/Users/[A-Za-z0-9._-]+/",
    r"/home/[A-Za-z0-9._-]+/",
)


def _skip_path(rel: str) -> bool:
    lower = rel.lower()
    parts = lower.split("/")
    if any(x in parts for x in ("tests", "test", "fixtures", "node_modules", ".git", "dist", ".terraform", "verification")):
        return True
    if lower.startswith("internal/") or "/internal/" in lower:
        return True
    if "security-detector" in lower or "_audit_" in lower or "redaction" in lower:
        return True
    if "sbom" in lower and lower.endswith(".json"):
        # SBOM metadata may contain tooling URLs; path leak checked separately after scrub
        return False
    return False


def check_security(
    roots: dict[str, Path],
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict = {"scanned_repos": []}

    for key, root in roots.items():
        if key in {"community", "docs_focus"}:
            continue
        if not root or not root.is_dir():
            continue
        secret_hits: list[str] = []
        path_hits: list[str] = []
        env_hits: list[str] = []
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(root).as_posix()
            if _skip_path(rel):
                continue
            if p.name in {".env", "credentials.json", "secrets.tfvars"} and not str(p.name).endswith(".example"):
                env_hits.append(rel)
            if p.suffix.lower() not in {
                ".md",
                ".py",
                ".ts",
                ".tsx",
                ".js",
                ".json",
                ".yml",
                ".yaml",
                ".toml",
                ".tf",
                ".sh",
                ".env",
                ".txt",
                ".html",
                ".css",
            }:
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            # Skip detector signature catalogs
            if any(tok in text.lower() for tok in ("signature", "detector", "redaction")) and "-----BEGIN" in text:
                if not re.search(
                    r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----\s*\n[A-Za-z0-9+/=\n]{64,}",
                    text,
                ):
                    continue
            for pat in SECRET_PATTERNS:
                if re.search(pat, text, re.DOTALL):
                    secret_hits.append(rel)
                    break
            for pat in PATH_PATTERNS:
                if re.search(pat, text):
                    path_hits.append(rel)
                    break
        add_check(
            checks,
            defects,
            f"security:no_secrets:{key}",
            not secret_hits,
            ",".join(secret_hits[:5]) or "ok",
            "security",
            classification="secret_leak",
        )
        add_check(
            checks,
            defects,
            f"security:no_absolute_paths:{key}",
            not path_hits,
            ",".join(path_hits[:5]) or "ok",
            "security",
            classification="path_leak",
        )
        add_check(
            checks,
            defects,
            f"security:no_env_files:{key}",
            not env_hits,
            ",".join(env_hits[:5]) or "ok",
            "security",
        )
        summary["scanned_repos"].append(
            {
                "repo": key,
                "secret_hits": len(secret_hits),
                "path_hits": len(path_hits),
                "env_hits": len(env_hits),
            }
        )

    return checks, defects, summary
