"""Export validation — dry-run and materialize temporary exports."""

from __future__ import annotations

import hashlib
import re
import shutil
import sys
import tempfile
from pathlib import Path

from verification.repository_package_release_validation.contract import (
    COMMUNITY_REPOS,
    EXPORT_TARGETS,
)
from verification.repository_package_release_validation.helpers import (
    add_check,
    inventory_fingerprint,
    rel_paths,
)
from verification.repository_package_release_validation.models import CheckResult, Defect


def _ensure_scripts_path(monorepo: Path) -> None:
    scripts = monorepo / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))


def _export(monorepo: Path, target: str, destination: Path, *, dry_run: bool):
    _ensure_scripts_path(monorepo)
    from repository_export_router.router import export_repository

    return export_repository(
        target=target,
        destination=destination,
        dry_run=dry_run,
        source_root=monorepo,
    )


def _is_fixture_or_test_path(rel: str) -> bool:
    lower = rel.lower()
    parts = lower.split("/")
    if "tests" in parts or "test" in parts:
        return True
    if "fixtures" in parts or "fixture" in lower:
        return True
    if lower.startswith("internal/") or "/internal/" in lower:
        return True
    if "security-detector" in lower or "_audit_" in lower or "redaction" in lower:
        return True
    if lower.endswith(".test.ts") or lower.endswith(".test.js"):
        return True
    return False


def _is_detector_signature_context(text: str) -> bool:
    """Signature catalogs and redaction detectors intentionally embed secret markers."""
    lowered = text.lower()
    return any(
        tok in lowered
        for tok in (
            "signature",
            "detector",
            "redaction",
            "pattern",
            "compile(r\"-----begin",
            "compile(r'-----begin",
            "private_key",
            "secret_markers",
            "forbidden_content",
        )
    )


def _scan_forbidden(root: Path) -> list[str]:
    hits: list[str] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        lower = rel.lower()
        if any(x in lower for x in ("/node_modules/", "/.git/", "/__pycache__/", "/.terraform/", "/.wrangler/")):
            continue
        if _is_fixture_or_test_path(rel):
            continue
        if "verification/" in lower or lower.startswith("verification/"):
            # Exported verification packages may include detector contracts; not product leakage.
            continue
        if "platform/src" in lower or "/platform/src/" in f"/{lower}":
            hits.append(rel)
            continue
        if lower.endswith((".py", ".ts", ".tsx", ".js", ".md", ".json", ".yml", ".yaml", ".toml")):
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if _is_detector_signature_context(text) and "-----BEGIN" in text:
                # detector catalogs only
                pass
            elif "-----BEGIN" in text and "PRIVATE KEY-----" in text:
                # require a multi-line key body (not just a marker string)
                if re.search(
                    r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----\s*\n[A-Za-z0-9+/=\n]{64,}",
                    text,
                ):
                    hits.append(f"{rel}:private_key_block")
                    continue
            for line in text.splitlines():
                s = line.strip()
                if s.startswith("#") or s.startswith("//"):
                    continue
                if "from ../platform" in s or "import ../platform" in s or 'from "../platform' in s:
                    hits.append(f"{rel}:sibling_platform")
                    break
                if (s.startswith("from codestrata_platform") or s.startswith("import codestrata_platform")) and "/verification/" not in f"/{lower}/":
                    hits.append(f"{rel}:codestrata_platform")
                    break
    return hits[:50]


def _has_generated_residue(root: Path) -> list[str]:
    bad: list[str] = []
    for name in ("node_modules", "dist", "build", ".vite", "coverage", ".pytest_cache", ".terraform", "__pycache__"):
        for p in root.rglob(name):
            if p.is_dir():
                bad.append(p.relative_to(root).as_posix())
    for p in root.rglob("*.vsix"):
        bad.append(p.relative_to(root).as_posix())
    for p in root.rglob("*~"):
        bad.append(p.relative_to(root).as_posix())
    return bad[:40]


def check_exports(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict, dict[str, Path], list[str]]:
    """Return checks, defects, summary, materialized export roots, fingerprints."""
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict = {"targets": {}, "community_repos": []}
    roots: dict[str, Path] = {}
    fingerprints: list[str] = []

    router = monorepo / "scripts/export_repository.py"
    add_check(checks, defects, "export:router_exists", router.is_file(), "export_repository.py", "export")

    # Dry-run each target (destination must not be created / written)
    for target in EXPORT_TARGETS:
        with tempfile.TemporaryDirectory(prefix=f"sv169-dry-{target}-") as tmp:
            dest = Path(tmp) / "dest"
            ok = True
            err = ""
            try:
                result = _export(monorepo, target, dest, dry_run=True)
                if getattr(result, "status", "ok") != "ok":
                    ok = False
                    err = f"status={getattr(result, 'status', '?')}"
                if dest.exists():
                    ok = False
                    err = "dry_run_created_destination"
            except Exception as exc:  # noqa: BLE001
                ok = False
                err = type(exc).__name__
            add_check(
                checks,
                defects,
                f"export:dry_run:{target}",
                ok,
                err or "dry_run_ok",
                "export",
            )
            summary["targets"][target] = {"dry_run": "ok" if ok else err}

    # Materialize exports for validation (cleaned by caller via returned paths under temp base)
    base = Path(tempfile.mkdtemp(prefix="sv169-exports-"))
    fingerprints.append(str(base.name))  # only basename later stripped from report

    # Community
    community_dest = base / "community"
    try:
        _export(monorepo, "community", community_dest, dry_run=False)
        community_ok = True
        community_err = "ok"
    except Exception as exc:  # noqa: BLE001
        community_ok = False
        community_err = type(exc).__name__
    add_check(checks, defects, "export:materialize:community", community_ok, community_err, "export")
    if community_ok:
        roots["community"] = community_dest
        for repo in COMMUNITY_REPOS:
            present = (community_dest / repo).is_dir()
            add_check(checks, defects, f"export:community_repo:{repo}", present, repo, "export")
            summary["community_repos"].append({"name": repo, "present": str(present)})
            if present:
                roots[repo] = community_dest / repo
                # exclusions
                forbidden = _scan_forbidden(community_dest / repo)
                add_check(
                    checks,
                    defects,
                    f"export:exclusions:{repo}",
                    not forbidden,
                    ",".join(forbidden[:5]) or "clean",
                    "export",
                    classification="platform_leakage",
                )
                residue = _has_generated_residue(community_dest / repo)
                add_check(
                    checks,
                    defects,
                    f"export:no_generated:{repo}",
                    not residue,
                    ",".join(residue[:5]) or "clean",
                    "export",
                )
                # no verification package unless intentional (docs may not include monorepo verification/)
                ver = community_dest / repo / "verification"
                # engine may export engine verification? check
                if repo in {"codestrata-docs", "codestrata-vscode", "codestrata-examples"}:
                    add_check(
                        checks,
                        defects,
                        f"export:no_monorepo_verification:{repo}",
                        not ver.is_dir() or not (ver / "repository_inventory").exists(),
                        "no monorepo epic verification",
                        "export",
                    )
                fp = inventory_fingerprint(rel_paths(community_dest / repo))
                fingerprints.append(f"{repo}:{hashlib.sha256(fp.encode()).hexdigest()}")

        # Ensure no cursor / platform / infrastructure / insights top-level in community staging
        for bad in ("codestrata-cursor", "codestrata-platform", "codestrata-infrastructure", "codestrata-insights", "cursor-plugin"):
            add_check(
                checks,
                defects,
                f"export:community_absent:{bad}",
                not (community_dest / bad).exists(),
                bad,
                "export",
            )

    # Infrastructure
    infra_dest = base / "infrastructure-repo"
    try:
        _export(monorepo, "infrastructure", infra_dest, dry_run=False)
        infra_ok = True
        infra_err = "ok"
    except Exception as exc:  # noqa: BLE001
        infra_ok = False
        infra_err = type(exc).__name__
    add_check(checks, defects, "export:materialize:infrastructure", infra_ok, infra_err, "export")
    if infra_ok:
        roots["infrastructure"] = infra_dest
        roots["codestrata-infrastructure"] = infra_dest
        forbidden = _scan_forbidden(infra_dest)
        add_check(checks, defects, "export:exclusions:infrastructure", not forbidden, ",".join(forbidden[:5]) or "clean", "export")
        # Must not contain engine/platform/vscode source trees
        for bad in ("engine", "platform", "vscode-plugin", "cursor-plugin", "insights"):
            add_check(
                checks,
                defects,
                f"export:infra_absent:{bad}",
                not (infra_dest / bad).is_dir(),
                bad,
                "export",
            )
        residue = _has_generated_residue(infra_dest)
        add_check(checks, defects, "export:no_generated:infrastructure", not residue, ",".join(residue[:5]) or "clean", "export")
        fp = inventory_fingerprint(rel_paths(infra_dest))
        fingerprints.append(f"infrastructure:{hashlib.sha256(fp.encode()).hexdigest()}")
        summary["targets"]["infrastructure"]["materialized"] = "ok"

    # Insights
    insights_dest = base / "insights-repo"
    try:
        _export(monorepo, "insights", insights_dest, dry_run=False)
        insights_ok = True
        insights_err = "ok"
    except Exception as exc:  # noqa: BLE001
        insights_ok = False
        insights_err = type(exc).__name__
    add_check(checks, defects, "export:materialize:insights", insights_ok, insights_err, "export")
    if insights_ok:
        roots["insights"] = insights_dest
        roots["codestrata-insights"] = insights_dest
        forbidden = _scan_forbidden(insights_dest)
        add_check(checks, defects, "export:exclusions:insights", not forbidden, ",".join(forbidden[:5]) or "clean", "export")
        # no platform python
        add_check(
            checks,
            defects,
            "export:insights_no_platform_py",
            not (insights_dest / "platform").exists(),
            "no platform tree",
            "export",
        )
        residue = _has_generated_residue(insights_dest)
        add_check(checks, defects, "export:no_generated:insights", not residue, ",".join(residue[:5]) or "clean", "export")
        fp = inventory_fingerprint(rel_paths(insights_dest))
        fingerprints.append(f"insights:{hashlib.sha256(fp.encode()).hexdigest()}")
        summary["targets"]["insights"] = summary["targets"].get("insights", {})
        summary["targets"]["insights"]["materialized"] = "ok"

    summary["_cleanup_base"] = str(base)  # runner will strip before report; used for cleanup
    return checks, defects, summary, roots, fingerprints


def cleanup_export_base(summary: dict) -> None:
    base = summary.pop("_cleanup_base", None)
    if base:
        shutil.rmtree(base, ignore_errors=True)
