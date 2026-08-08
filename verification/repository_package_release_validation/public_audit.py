"""Public repository professional-readiness audit."""

from __future__ import annotations

import re
from pathlib import Path

from verification.repository_package_release_validation.helpers import add_check
from verification.repository_package_release_validation.models import CheckResult, Defect

INTERNAL_PATTERNS = (
    r"(?i)\bTODO\(owner\)",
    r"(?i)\bFIXME: temporary",
    r"(?i)internal only — delete before release",
    r"(?i)codestrata-platform monorepo path: /Users/",
    r"(?i)scratch notes for implementers only",
)
COMMERCIAL_AS_PUBLIC = (
    r"(?i)commercial platform is included in this community package",
    r"(?i)install rag knowledge graph \(community\)",
)
CURSOR_ACTIVE = (
    r"(?i)install the cursor extension from this repository",
    r"(?m)^# CodeStrata Cursor\b",
)
AIMF_ACTIVE = (
    r"(?i)\bAIMF\b.*(community product|extension package)",
)


def check_public_audit(
    roots: dict[str, Path],
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict = {"repos": {}}

    publicish = [
        ("engine", roots.get("codestrata-engine")),
        ("docs", roots.get("codestrata-docs")),
        ("vscode", roots.get("codestrata-vscode")),
        ("examples", roots.get("codestrata-examples")),
    ]
    # insights/infra are private but still audited for professionalism
    privateish = [
        ("insights", roots.get("codestrata-insights")),
        ("infrastructure", roots.get("codestrata-infrastructure")),
    ]

    for label, root in publicish + privateish:
        if not root or not root.is_dir():
            add_check(checks, defects, f"audit:present:{label}", False, label, "public_audit")
            continue
        hits_internal: list[str] = []
        hits_commercial: list[str] = []
        hits_cursor: list[str] = []
        hits_aimf: list[str] = []
        platform_links: list[str] = []
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in {".md", ".py", ".ts", ".tsx", ".js", ".json", ".yml", ".yaml", ".toml", ".html"}:
                continue
            if any(x in p.parts for x in ("node_modules", ".git", "dist", ".vitepress")):
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            rel = p.relative_to(root).as_posix()
            for pat in INTERNAL_PATTERNS:
                if re.search(pat, text):
                    hits_internal.append(rel)
                    break
            for pat in COMMERCIAL_AS_PUBLIC:
                if re.search(pat, text):
                    hits_commercial.append(rel)
                    break
            for pat in CURSOR_ACTIVE:
                if re.search(pat, text):
                    hits_cursor.append(rel)
                    break
            for pat in AIMF_ACTIVE:
                if re.search(pat, text):
                    hits_aimf.append(rel)
                    break
            if re.search(r"(?i)\]\(\.\./\.\./platform/|platform/docs/|platform\.codestrata\.ai", text):
                # allow retirement notes
                if "retired" not in text.lower() and "internal-only" not in text.lower() and "never exported" not in text.lower():
                    platform_links.append(rel)

        add_check(
            checks,
            defects,
            f"audit:no_internal_notes:{label}",
            not hits_internal,
            ",".join(hits_internal[:5]) or "ok",
            "public_audit",
        )
        add_check(
            checks,
            defects,
            f"audit:no_commercial_as_community:{label}",
            not hits_commercial,
            ",".join(hits_commercial[:5]) or "ok",
            "public_audit",
        )
        add_check(
            checks,
            defects,
            f"audit:no_active_cursor:{label}",
            not hits_cursor,
            ",".join(hits_cursor[:5]) or "ok",
            "public_audit",
        )
        add_check(
            checks,
            defects,
            f"audit:no_active_aimf:{label}",
            not hits_aimf,
            ",".join(hits_aimf[:5]) or "ok",
            "public_audit",
        )
        if label in {"engine", "docs", "vscode", "examples"}:
            add_check(
                checks,
                defects,
                f"audit:no_platform_leak_links:{label}",
                not platform_links,
                ",".join(platform_links[:5]) or "ok",
                "public_audit",
                classification="platform_leakage",
            )
        summary["repos"][label] = {
            "internal": len(hits_internal),
            "commercial": len(hits_commercial),
            "cursor": len(hits_cursor),
            "aimf": len(hits_aimf),
            "platform_links": len(platform_links),
        }

    return checks, defects, summary
