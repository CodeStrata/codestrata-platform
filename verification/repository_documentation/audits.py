"""Link and identity audits for active Community documentation."""

from __future__ import annotations

import re
from pathlib import Path

from verification.repository_documentation.contract import FORBIDDEN_ACTIVE_IDENTITY_PATTERNS
from verification.repository_documentation.models import DocEntry

MD_LINK = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
IDENTITY_RES = [re.compile(p) for p in FORBIDDEN_ACTIVE_IDENTITY_PATTERNS]

# Allow historical negation language
ALLOW_IF_CONTEXT = re.compile(
    r"(removed|historical|former|not an active|no longer|archive|epic 12)",
    re.I,
)


def is_active_community_path(rel: str) -> bool:
    if not rel.startswith("docs/"):
        return False
    if rel.startswith(("docs/platform/", "docs/internal/")):
        return False
    if "/.vitepress/" in rel:
        return False
    return rel.endswith(".md")


def scan_identity_violations(monorepo: Path, entries: list[DocEntry]) -> list[str]:
    hits: list[str] = []
    for e in entries:
        if not is_active_community_path(e.path) and e.path not in {
            "README.md",
            "docs/index.md",
        }:
            # Also scan root README and published-adjacent active community paths
            if e.path != "README.md" and not (
                e.classification == "ACTIVE" and e.path.startswith("docs/") and not e.path.startswith(("docs/platform/", "docs/internal/"))
            ):
                continue
        path = monorepo / e.path
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for rx in IDENTITY_RES:
            for match in rx.finditer(text):
                start = max(0, match.start() - 80)
                end = min(len(text), match.end() + 80)
                window = text[start:end]
                if ALLOW_IF_CONTEXT.search(window):
                    continue
                # MCP "Cursor" client examples are IDE tooling, not product identity —
                # only flag when paired with Extension / plugin product language.
                if rx.pattern == r"\bAIMF\b" or "Modernization" in rx.pattern:
                    hits.append(f"{e.path}:aimf_or_legacy")
                elif "Cursor" in match.group(0) or "cursor" in match.group(0).lower():
                    if re.search(r"Cursor Extension|cursor-plugin|CodeStrata Cursor|Cursor extensions", window, re.I):
                        hits.append(f"{e.path}:cursor_product_identity")
        # Explicit published miss pattern
        if re.search(r"VS Code and Cursor extensions", text, re.I):
            hits.append(f"{e.path}:vscode_and_cursor_extensions")
    return sorted(set(hits))


def scan_broken_relative_links(monorepo: Path, entries: list[DocEntry]) -> list[str]:
    broken: list[str] = []
    for e in entries:
        if e.classification not in {"ACTIVE", "OWNER_REVIEW_REQUIRED"}:
            continue
        if not (
            e.path.startswith("docs/")
            or e.path in {"README.md", "CONTRIBUTING.md", "ARCHITECTURE.md", "SECURITY.md", "CODE_OF_CONDUCT.md"}
            or e.path.startswith("platform/docs/repository-cleanup/")
        ):
            continue
        if e.path.startswith(("docs/platform/", "docs/internal/")):
            continue
        path = monorepo / e.path
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        base = path.parent
        for _label, target in MD_LINK.findall(text):
            target = target.strip()
            if not target or target.startswith(("#", "http://", "https://", "mailto:", "tel:")):
                continue
            if target.startswith("mailto:"):
                continue
            # strip anchors
            file_part = target.split("#", 1)[0]
            if not file_part:
                continue
            # VitePress absolute site paths — treat as site routes, not filesystem
            if file_part.startswith("/"):
                # Map common community routes to docs files
                route = file_part.lstrip("/")
                if route.endswith("/"):
                    candidate = monorepo / "docs" / route / "index.md"
                    alt = monorepo / "docs" / (route.rstrip("/") + ".md")
                else:
                    candidate = monorepo / "docs" / (route + ".md")
                    alt = monorepo / "docs" / route / "index.md"
                # Excluded unpublished routes are not broken for published set if linked from excluded pages only
                if e.path.startswith("docs/") and route.startswith("platform"):
                    broken.append(f"{e.path} -> {target} (unpublished_platform_route)")
                    continue
                if candidate.is_file() or alt.is_file():
                    continue
                # Known external-style site roots
                if route in {"", "getting-started"} or route.startswith(
                    (
                        "getting-started",
                        "engine",
                        "assessments",
                        "reports",
                        "extensions",
                        "ai-providers",
                        "reference",
                        "security",
                        "troubleshooting",
                        "faq",
                        "community/examples",
                        "community/contributing",
                    )
                ):
                    if candidate.is_file() or alt.is_file():
                        continue
                    # soft: VitePress may resolve without .md; only fail hard paths we know
                    if not (monorepo / "docs" / route).exists() and not candidate.exists() and not alt.exists():
                        # don't fail every nav path; only flag clearly missing
                        if route.startswith("platform"):
                            broken.append(f"{e.path} -> {target}")
                continue
            resolved = (base / file_part).resolve()
            try:
                resolved.relative_to(monorepo.resolve())
            except ValueError:
                broken.append(f"{e.path} -> {target} (escapes_repo)")
                continue
            if resolved.exists():
                continue
            # VitePress / docs often omit .md
            if not file_part.endswith((".md", ".mdx", ".html")):
                for suffix in (".md", ".mdx"):
                    alt = (base / (file_part + suffix)).resolve()
                    try:
                        alt.relative_to(monorepo.resolve())
                    except ValueError:
                        continue
                    if alt.exists():
                        break
                    idx = (base / file_part / "index.md").resolve()
                    if idx.exists():
                        break
                else:
                    broken.append(f"{e.path} -> {target}")
                continue
            broken.append(f"{e.path} -> {target}")
    return sorted(set(broken))


def find_duplicate_authorities(monorepo: Path) -> list[str]:
    """Flag known duplicate install/privacy/design explanations that are not pointers."""
    dups: list[str] = []
    install = monorepo / "docs/getting-started/install.md"
    engine_install = monorepo / "docs/engine/installation.md"
    if install.is_file() and engine_install.is_file():
        text = engine_install.read_text(encoding="utf-8", errors="ignore")
        if "Canonical page" not in text and "getting-started/install" not in text:
            dups.append("docs/engine/installation.md lacks pointer to canonical install")
        else:
            dups.append("docs/engine/installation.md:pointer_ok")
    # design system: governance vs design-system
    if (monorepo / "design-system/README.md").is_file() and (
        monorepo / "governance/assets/DESIGN-SYSTEM.md"
    ).is_file():
        dups.append("design-system/README.md authoritative; governance/assets/DESIGN-SYSTEM.md historical")
    return sorted(dups)
