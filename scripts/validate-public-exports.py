#!/usr/bin/env python3
"""Validate staged public exports from codestrata-platform.

Runs structural checks and, for codestrata-engine, a fresh-venv install + CLI smoke.
Does not push or publish GitHub repositories.
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import subprocess
import sys
import tempfile
import venv
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    print("PyYAML is required: pip install PyYAML", file=sys.stderr)
    raise SystemExit(2) from None

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "public-export-manifest.yaml"
EXPORT_SCRIPT = ROOT / "scripts" / "export-public-repos.py"


def _load_manifest(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid manifest: {path}")
    return data


def _iter_files(base: Path) -> list[Path]:
    return sorted(path for path in base.rglob("*") if path.is_file())


def _rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _match_any(rel: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(rel, pat) for pat in patterns)


_MD_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")


def _validate_markdown_links(
    *,
    name: str,
    dest: Path,
    files: list[Path],
    forbid_link_substrings: list[str],
) -> list[str]:
    """Fail when public Markdown links private monorepo paths or missing files."""

    errors: list[str] = []
    md_files = [path for path in files if path.suffix.lower() == ".md"]
    for path in md_files:
        rel = _rel(path, dest)
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for match in _MD_LINK_RE.finditer(text):
            target = match.group(2).strip()
            if not target or target.startswith(("#", "mailto:")):
                continue
            if " " in target and not target.startswith(("http://", "https://")):
                target = target.split(" ", 1)[0]
            href = target.split("#", 1)[0].split("?", 1)[0]
            if not href:
                continue
            private_hit = False
            for needle in forbid_link_substrings:
                if needle in href:
                    errors.append(f"{name}: private markdown link in {rel}: {href!r}")
                    private_hit = True
                    break
            if private_hit:
                continue
            if href.startswith(("http://", "https://")):
                continue
            # VitePress / docs portal site-absolute paths (resolved at build time).
            if name == "codestrata-docs" and href.startswith("/"):
                continue
            resolved = (path.parent / href).resolve()
            try:
                resolved.relative_to(dest.resolve())
            except ValueError:
                errors.append(f"{name}: markdown link escapes export in {rel}: {href!r}")
                continue
            if resolved.exists():
                continue
            # VitePress-style extensionless links: ./install → install.md / index.md
            candidates = [
                Path(str(resolved) + ".md"),
                resolved / "index.md",
            ]
            if href.endswith("/"):
                candidates.append((path.parent / href / "index.md").resolve())
            if not any(candidate.exists() for candidate in candidates):
                errors.append(f"{name}: broken markdown link in {rel}: {href!r}")
    return errors


GENERATED_EXPORT_MARKERS = frozenset(
    {
        ".codestrata-export-snapshot.json",
    }
)


def _validate_allowlist(
    *,
    name: str,
    export: dict[str, Any],
    defaults: dict[str, Any],
    rels: list[str],
) -> list[str]:
    """Ensure every staged file matches the export allowlist (include − exclude)."""

    errors: list[str] = []
    include = list(export.get("include") or ["**"])
    exclude = list(export.get("exclude") or [])
    default_exclude = list(defaults.get("exclude_globs") or [])
    extra_prefixes = [
        str(item.get("to", "")).replace("\\", "/").rstrip("/") + "/"
        for item in (export.get("extra_includes") or [])
        if item.get("to")
    ]
    for rel in rels:
        if Path(rel).name in GENERATED_EXPORT_MARKERS:
            continue
        if any(rel == p.rstrip("/") or rel.startswith(p) for p in extra_prefixes if p != "/"):
            continue
        if _match_any(rel, exclude) or _match_any(rel, default_exclude):
            errors.append(f"{name}: excluded path was exported: {rel}")
            continue
        if include and not _match_any(rel, include):
            errors.append(f"{name}: non-allowlisted path exported: {rel}")
    never = list(
        (defaults.get("documentation_boundary") or {}).get("never_export_source_roots") or []
    )
    source_root = str(export.get("source_root") or "")
    if source_root in never:
        errors.append(f"{name}: forbidden source_root {source_root!r}")
    return errors


def _run(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> None:
    print(f"  $ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def validate_export(
    *,
    root: Path,
    staging_root: Path,
    export: dict[str, Any],
    defaults: dict[str, Any],
    skip_install: bool,
) -> list[str]:
    errors: list[str] = []
    name = str(export["name"])
    dest = staging_root / name
    if not dest.is_dir():
        return [f"{name}: missing staging directory {dest}"]

    validation = dict(export.get("validation") or {})
    files = _iter_files(dest)
    rels = [_rel(path, dest) for path in files]

    for required in validation.get("require_files") or []:
        if not (dest / required).is_file():
            errors.append(f"{name}: missing required file {required}")

    for pattern in validation.get("forbid_globs") or []:
        hits = [rel for rel in rels if fnmatch.fnmatch(rel, pattern)]
        if hits:
            errors.append(f"{name}: forbidden path exported ({pattern}): {hits[:5]}")

    for needle in defaults.get("forbid_path_substrings") or []:
        if needle == "platform/":
            # codestrata-docs may publish a public Platform overview under platform/.
            if name == "codestrata-docs":
                hits = [
                    rel
                    for rel in rels
                    if rel.startswith("platform/src")
                    or "platform/docs/" in rel
                    or rel.endswith("platform/pyproject.toml")
                ]
            else:
                hits = [rel for rel in rels if "platform/" in rel or rel.startswith("platform")]
            if hits:
                errors.append(f"{name}: platform path leaked: {hits[:5]}")
            continue
        if needle == ".env":
            hits = [
                rel
                for rel in rels
                if Path(rel).name == ".env" or Path(rel).name.startswith(".env.")
            ]
            # Allow documented example env templates.
            hits = [rel for rel in hits if Path(rel).name != ".env.example"]
            if hits:
                errors.append(f"{name}: env file leaked: {hits[:5]}")
            continue
        hits = [rel for rel in rels if needle in rel]
        if hits:
            errors.append(f"{name}: forbidden substring {needle!r}: {hits[:5]}")

    errors.extend(
        _validate_allowlist(
            name=name,
            export=export,
            defaults=defaults,
            rels=rels,
        )
    )

    patterns = [re.compile(p) for p in defaults.get("forbid_content_patterns") or []]
    skip_secret_scan_globs = [
        "**/tests/**",
        "**/signatures.py",
        "**/security_analyzer.py",
        "**/test_*.py",
    ]
    for path in files:
        rel = _rel(path, dest)
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico"}:
            continue
        if _match_any(rel, skip_secret_scan_globs):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in patterns:
            if pattern.search(text):
                errors.append(f"{name}: secret-like content in {rel} ({pattern.pattern})")
                break

    errors.extend(
        _validate_markdown_links(
            name=name,
            dest=dest,
            files=files,
            forbid_link_substrings=list(defaults.get("forbid_markdown_link_substrings") or []),
        )
    )

    allow_only = list(validation.get("allow_only_globs") or [])
    if allow_only:
        unexpected = [rel for rel in rels if not _match_any(rel, allow_only)]
        if unexpected:
            errors.append(f"{name}: unexpected placeholder files: {unexpected[:10]}")

    lang_samples = list(validation.get("require_language_samples") or [])
    if lang_samples:
        mapping = {
            "javascript": "sample-js-app",
            "python": "sample-python-app",
            "java": "sample-java-app",
            "php": "sample-php-app",
            "csharp": "sample-csharp-app",
        }
        for lang in lang_samples:
            folder = mapping.get(lang)
            if not folder or not (dest / folder).is_dir():
                errors.append(f"{name}: missing language sample for {lang}")
            report = (
                dest
                / "sample-reports"
                / ("javascript" if lang == "javascript" else lang)
                / "report.html"
            )
            if lang == "csharp":
                report = dest / "sample-reports" / "csharp" / "report.html"
            if not report.is_file():
                errors.append(f"{name}: missing sample report for {lang}: {report.name}")

    # Engine-specific fresh install + smoke
    if name == "codestrata-engine" and not skip_install:
        errors.extend(_validate_engine_install(dest))

    # Focused engine tests when present (already-installed editable in smoke venv is separate)
    for command in validation.get("commands") or []:
        # Skip install/assess commands here; handled by fresh venv helper
        if command.startswith("python -m pip") or command.startswith("codestrata "):
            continue
        if skip_install and "pytest" in command:
            continue
        if "pytest" in command and name == "codestrata-engine":
            # Run focused tests against staged tree with monorepo venv if available
            try:
                env = os.environ.copy()
                env["PYTHONPATH"] = str(dest / "src")
                _run(
                    [sys.executable, "-m", "pytest", "-q", "tests/config/test_settings.py"],
                    cwd=dest,
                    env=env,
                )
            except subprocess.CalledProcessError as error:
                errors.append(f"{name}: focused pytest failed ({error.returncode})")

    print(f"[VALIDATE] {name}: {'OK' if not errors else 'FAIL'} ({len(files)} files)")
    return errors


def _validate_engine_install(dest: Path) -> list[str]:
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="cs-engine-export-") as tmp:
        venv_dir = Path(tmp) / "venv"
        venv.EnvBuilder(with_pip=True).create(venv_dir)
        pip = venv_dir / ("Scripts" if os.name == "nt" else "bin") / "pip"
        python = venv_dir / ("Scripts" if os.name == "nt" else "bin") / "python"
        codestrata = venv_dir / ("Scripts" if os.name == "nt" else "bin") / "codestrata"
        try:
            _run([str(pip), "install", "-q", "--upgrade", "pip"], cwd=dest)
            _run([str(pip), "install", "-q", "."], cwd=dest)
            _run([str(codestrata), "version"], cwd=dest)
            report_dir = Path(tmp) / "reports"
            _run(
                [
                    str(codestrata),
                    "assess",
                    "--repo",
                    "test-fixtures/sample-js-app",
                    "--output",
                    str(report_dir),
                    "--no-ai",
                ],
                cwd=dest,
            )
            html_hits = list(report_dir.rglob("report.html"))
            if not html_hits:
                errors.append("codestrata-engine: assess did not produce report.html")
            else:
                html = html_hits[0].read_text(encoding="utf-8", errors="ignore")
                if "Community Edition" not in html:
                    errors.append("codestrata-engine: HTML missing Community Edition branding")
            # CLI help smoke
            _run([str(codestrata), "--help"], cwd=dest)
            _run([str(python), "-c", "import codestrata; print(codestrata.__version__)"], cwd=dest)
        except subprocess.CalledProcessError as error:
            errors.append(f"codestrata-engine: install/smoke failed ({error.returncode})")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--staging", type=Path, default=None)
    parser.add_argument("--repo", action="append", dest="repos")
    parser.add_argument(
        "--skip-export",
        action="store_true",
        help="Validate existing staging only (do not re-export).",
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Skip fresh-venv engine install smoke (structural checks only).",
    )
    parser.add_argument("--dry-run-export", action="store_true")
    args = parser.parse_args(argv)

    manifest = _load_manifest(args.manifest)
    staging = args.staging or (ROOT / str(manifest.get("staging_directory", ".export-staging")))
    defaults = dict(manifest.get("defaults") or {})

    exports = list(manifest["exports"])
    if args.repos:
        wanted = set(args.repos)
        exports = [
            item
            for item in exports
            if item["name"] in wanted
            or item.get("destination_repository") in wanted
            or item.get("public_repository") in wanted
        ]

    if not args.skip_export:
        cmd = [sys.executable, str(EXPORT_SCRIPT), "--manifest", str(args.manifest)]
        # Full staging wipe only when validating the complete export set.
        # Selective --repo must preserve sibling staged repositories.
        if not args.repos:
            cmd.append("--clean")
        if args.dry_run_export:
            cmd.append("--dry-run")
        for repo in args.repos or []:
            cmd.extend(["--repo", repo])
        print("[VALIDATE] refreshing export staging…")
        subprocess.run(cmd, cwd=ROOT, check=True)
        if args.dry_run_export:
            print("[VALIDATE] dry-run export only; skipping content validation")
            return 0

    all_errors: list[str] = []
    for export in exports:
        all_errors.extend(
            validate_export(
                root=ROOT,
                staging_root=staging,
                export=export,
                defaults=defaults,
                skip_install=args.skip_install,
            )
        )

    if all_errors:
        print("\nValidation failures:")
        for error in all_errors:
            print(f"  - {error}")
        return 1
    print("\nAll public export validations passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
