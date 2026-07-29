"""Fetch pinned third-party showcase repositories safely.

Portable for standalone ``codestrata-examples`` clones and for the monorepo
``examples/`` tree. Default workspace root is the examples repository itself
(never the monorepo parent). Monorepo wrappers under ``scripts/`` invoke this
module unchanged.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
ID_RE = re.compile(r"^[a-z][a-z0-9-]{1,62}$")
ALLOWED_HOSTS = frozenset({"github.com"})
FORBIDDEN_REFS = frozenset({"main", "master", "latest", "HEAD", "origin/main", "origin/master"})
SIZE_CATEGORIES = frozenset({"small", "medium", "large"})
RUNTIME_CATEGORIES = frozenset({"fast", "moderate", "slow"})
PROFILES = frozenset({"community", "local", "enterprise", "bedrock", "openai"})


class FetchExampleError(Exception):
    """User-facing fetch failure."""


@dataclass(frozen=True)
class ShowcaseManifest:
    id: str
    name: str
    repository_url: str
    commit_sha: str
    license_spdx: str
    attribution_url: str
    primary_languages: tuple[str, ...]
    frameworks: tuple[str, ...]
    expected_size_category: str
    supported_capabilities: tuple[str, ...]
    recommended_profile: str
    required_tools: tuple[str, ...]
    fetch_destination: str
    runtime_category: str
    known_limitations: tuple[str, ...]
    owner: str | None = None
    description: str | None = None
    allow_submodules: bool = False
    build_instructions: str | None = None
    expected_approx_size_mb: float | None = None
    pinned_on: str | None = None

    @property
    def normalized_url(self) -> str:
        url = self.repository_url.strip()
        if not url.endswith(".git"):
            url = f"{url}.git"
        return url


def examples_root_from_here() -> Path:
    """Locate the examples repository root (directory containing real-world/manifests)."""

    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        manifests = candidate / "real-world" / "manifests"
        if manifests.is_dir():
            return candidate
        manifests = candidate / "examples" / "real-world" / "manifests"
        if manifests.is_dir():
            return candidate / "examples"
    raise FetchExampleError("Unable to locate examples/real-world/manifests")


def repo_root_from_here() -> Path:
    """Backward-compatible alias for :func:`examples_root_from_here`."""

    return examples_root_from_here()


def default_workspace_root(examples_root: Path | None = None) -> Path:
    """Return the workspace root for fetches and reports.

    Always the examples repository itself (standalone clone or monorepo
    ``examples/`` tree). Never the monorepo parent.
    """

    return (examples_root or examples_root_from_here()).resolve()


def manifests_dir(examples_root: Path | None = None) -> Path:
    root = examples_root or repo_root_from_here()
    path = root / "real-world" / "manifests"
    if not path.is_dir():
        raise FetchExampleError(f"Manifest directory missing: {path}")
    return path


def examples_fetch_root(repo_root: Path) -> Path:
    return (repo_root / ".codestrata-examples").resolve()


def _require_yaml() -> Any:
    if yaml is None:
        raise FetchExampleError("PyYAML is required: pip install PyYAML")
    return yaml


def validate_manifest_dict(data: dict[str, Any]) -> ShowcaseManifest:
    """Validate and normalize a manifest mapping."""

    required = [
        "id",
        "name",
        "repository_url",
        "commit_sha",
        "license_spdx",
        "attribution_url",
        "primary_languages",
        "frameworks",
        "expected_size_category",
        "supported_capabilities",
        "recommended_profile",
        "required_tools",
        "fetch_destination",
        "runtime_category",
        "known_limitations",
    ]
    missing = [key for key in required if key not in data or data[key] in (None, "")]
    if missing:
        raise FetchExampleError(f"Manifest missing required fields: {missing}")

    example_id = str(data["id"]).strip()
    if not ID_RE.match(example_id):
        raise FetchExampleError(f"Invalid manifest id: {example_id!r}")

    sha = str(data["commit_sha"]).strip().lower()
    if not FULL_SHA_RE.match(sha):
        raise FetchExampleError(
            f"commit_sha must be a full 40-character hex SHA (got {data['commit_sha']!r})"
        )
    if sha in FORBIDDEN_REFS or str(data["commit_sha"]).strip() in FORBIDDEN_REFS:
        raise FetchExampleError("Floating refs are not allowed for commit_sha")

    size = str(data["expected_size_category"]).strip().lower()
    if size not in SIZE_CATEGORIES:
        raise FetchExampleError(f"expected_size_category must be one of {sorted(SIZE_CATEGORIES)}")

    runtime = str(data["runtime_category"]).strip().lower()
    if runtime not in RUNTIME_CATEGORIES:
        raise FetchExampleError(f"runtime_category must be one of {sorted(RUNTIME_CATEGORIES)}")

    profile = str(data["recommended_profile"]).strip().lower()
    if profile not in PROFILES:
        raise FetchExampleError(f"recommended_profile must be one of {sorted(PROFILES)}")

    dest = str(data["fetch_destination"]).strip()
    if not dest or dest.startswith("/") or ".." in Path(dest).parts or dest != Path(dest).name:
        raise FetchExampleError(
            "fetch_destination must be a single safe directory name under .codestrata-examples/"
        )

    url = str(data["repository_url"]).strip()
    parsed = urlparse(url if "://" in url else f"https://{url}")
    if parsed.scheme not in {"https", "git+https"}:
        raise FetchExampleError("repository_url must use https")
    host = (parsed.hostname or "").lower()
    if host not in ALLOWED_HOSTS:
        raise FetchExampleError(f"Host not allowlisted: {host or parsed.netloc!r}")

    allow_submodules = bool(data.get("allow_submodules", False))
    if allow_submodules:
        raise FetchExampleError(
            "allow_submodules=true is not approved for automated fetch; keep false"
        )

    license_spdx = str(data["license_spdx"]).strip()
    if not license_spdx:
        raise FetchExampleError("license_spdx is required")

    def _str_tuple(key: str) -> tuple[str, ...]:
        value = data[key]
        if not isinstance(value, list) or not value:
            raise FetchExampleError(f"{key} must be a non-empty list")
        return tuple(str(item).strip() for item in value if str(item).strip())

    return ShowcaseManifest(
        id=example_id,
        name=str(data["name"]).strip(),
        repository_url=url,
        commit_sha=sha,
        license_spdx=license_spdx,
        attribution_url=str(data["attribution_url"]).strip(),
        primary_languages=_str_tuple("primary_languages"),
        frameworks=_str_tuple("frameworks"),
        expected_size_category=size,
        supported_capabilities=_str_tuple("supported_capabilities"),
        recommended_profile=profile,
        required_tools=_str_tuple("required_tools"),
        fetch_destination=dest,
        runtime_category=runtime,
        known_limitations=tuple(
            str(item).strip() for item in (data.get("known_limitations") or []) if str(item).strip()
        ),
        owner=(str(data["owner"]).strip() if data.get("owner") else None),
        description=(str(data["description"]).strip() if data.get("description") else None),
        allow_submodules=False,
        build_instructions=(
            str(data["build_instructions"]).strip() if data.get("build_instructions") else None
        ),
        expected_approx_size_mb=(
            float(data["expected_approx_size_mb"])
            if data.get("expected_approx_size_mb") is not None
            else None
        ),
        pinned_on=(str(data["pinned_on"]).strip() if data.get("pinned_on") else None),
    )


def load_manifest(example_id: str, *, examples_root: Path | None = None) -> ShowcaseManifest:
    path = manifests_dir(examples_root) / f"{example_id}.yaml"
    if not path.is_file():
        available = sorted(
            p.stem
            for p in manifests_dir(examples_root).glob("*.yaml")
            if not p.name.startswith("_")
        )
        raise FetchExampleError(
            f"Unknown example id {example_id!r}. Available: {', '.join(available) or '(none)'}"
        )
    payload = _require_yaml().safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise FetchExampleError(f"Manifest must be a mapping: {path}")
    return validate_manifest_dict(payload)


def list_manifest_ids(*, examples_root: Path | None = None) -> list[str]:
    return sorted(
        p.stem
        for p in manifests_dir(examples_root).glob("*.yaml")
        if not p.name.startswith("_")
    )


def _run_git(args: list[str], *, cwd: Path | None = None, timeout: int = 120) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as error:
        raise FetchExampleError("git is required on PATH") from error
    except subprocess.TimeoutExpired as error:
        raise FetchExampleError(f"git timed out: git {' '.join(args)}") from error
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or "").strip()
        raise FetchExampleError(f"git {' '.join(args)} failed: {detail}") from error
    return completed.stdout.strip()


def resolve_destination(
    manifest: ShowcaseManifest,
    *,
    repo_root: Path,
    destination_override: Path | None = None,
) -> Path:
    fetch_root = examples_fetch_root(repo_root)
    if destination_override is not None:
        dest = destination_override.resolve()
        if not str(dest).startswith(str(fetch_root)):
            raise FetchExampleError(
                f"Destination must remain under {fetch_root} (got {dest})"
            )
        return dest
    return fetch_root / manifest.fetch_destination


def write_provenance(dest: Path, *, manifest: ShowcaseManifest, resolved_sha: str) -> Path:
    payload = {
        "example_id": manifest.id,
        "name": manifest.name,
        "repository_url": manifest.normalized_url,
        "requested_commit_sha": manifest.commit_sha,
        "resolved_commit_sha": resolved_sha,
        "license_spdx": manifest.license_spdx,
        "attribution_url": manifest.attribution_url,
        "fetched_at": datetime.now(UTC).isoformat(),
        "codestrata_note": (
            "Third-party source fetched for assessment only; not maintained by CodeStrata."
        ),
    }
    path = dest / ".codestrata-example-provenance.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def fetch_example(
    example_id: str,
    *,
    repo_root: Path,
    examples_root: Path | None = None,
    destination_override: Path | None = None,
    force: bool = False,
    retries: int = 2,
) -> dict[str, Any]:
    """Clone/checkout the pinned commit for ``example_id`` under .codestrata-examples/."""

    manifest = load_manifest(example_id, examples_root=examples_root)
    dest = resolve_destination(
        manifest, repo_root=repo_root, destination_override=destination_override
    )
    fetch_root = examples_fetch_root(repo_root)
    fetch_root.mkdir(parents=True, exist_ok=True)

    if dest.exists() and any(dest.iterdir()) and not force:
        resolved = _run_git(["rev-parse", "HEAD"], cwd=dest)
        if resolved.lower() == manifest.commit_sha:
            provenance = write_provenance(dest, manifest=manifest, resolved_sha=resolved.lower())
            return {
                "example_id": manifest.id,
                "destination": str(dest),
                "commit_sha": resolved.lower(),
                "reused": True,
                "provenance": str(provenance),
            }
        raise FetchExampleError(
            f"Destination exists with unexpected HEAD {resolved}; pass --force to replace"
        )

    if dest.exists() and force:
        shutil.rmtree(dest)

    last_error: Exception | None = None
    for attempt in range(1, max(1, retries) + 1):
        try:
            dest.mkdir(parents=True, exist_ok=False)
            _run_git(["init"], cwd=dest)
            _run_git(["remote", "add", "origin", manifest.normalized_url], cwd=dest)
            _run_git(
                ["fetch", "--depth", "1", "origin", manifest.commit_sha],
                cwd=dest,
                timeout=300,
            )
            _run_git(["checkout", "--force", "FETCH_HEAD"], cwd=dest)
            # Refuse to init submodules.
            if (dest / ".gitmodules").exists():
                raise FetchExampleError(
                    "Repository declares submodules; automated fetch refuses submodule init"
                )
            resolved = _run_git(["rev-parse", "HEAD"], cwd=dest).lower()
            if resolved != manifest.commit_sha:
                # Some servers return a different object for shallow fetch of a commit;
                # require exact match to the pinned SHA.
                raise FetchExampleError(
                    f"Resolved HEAD {resolved} does not match pinned {manifest.commit_sha}"
                )
            provenance = write_provenance(dest, manifest=manifest, resolved_sha=resolved)
            return {
                "example_id": manifest.id,
                "destination": str(dest),
                "commit_sha": resolved,
                "reused": False,
                "attempt": attempt,
                "provenance": str(provenance),
                "manifest": asdict(manifest),
            }
        except Exception as error:  # noqa: BLE001 - retry boundary
            last_error = error
            if dest.exists():
                shutil.rmtree(dest, ignore_errors=True)
            if attempt >= retries:
                break
    assert last_error is not None
    raise FetchExampleError(str(last_error)) from last_error


def cleanup_example(
    example_id: str,
    *,
    repo_root: Path,
    examples_root: Path | None = None,
) -> Path:
    manifest = load_manifest(example_id, examples_root=examples_root)
    dest = resolve_destination(manifest, repo_root=repo_root)
    if dest.exists():
        shutil.rmtree(dest)
    return dest


def reject_arbitrary_url(url: str) -> None:
    """Public helper for tests: URLs outside manifests are rejected."""

    raise FetchExampleError(
        f"Arbitrary repository URLs are not accepted ({url!r}). "
        "Use a declared showcase example id from examples/real-world/manifests/."
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch a pinned CodeStrata real-world showcase repository."
    )
    parser.add_argument("example_id", nargs="?", help="Showcase example id")
    parser.add_argument("--list", action="store_true", help="List available example ids")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help=(
            "Workspace root for .codestrata-examples/ and reports/ "
            "(default: examples repository root containing real-world/)"
        ),
    )
    parser.add_argument("--force", action="store_true", help="Replace existing destination")
    parser.add_argument("--cleanup", action="store_true", help="Delete fetched destination")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        examples_root = examples_root_from_here()
        repo_root = (
            args.repo_root.resolve()
            if args.repo_root is not None
            else default_workspace_root(examples_root)
        )

        if args.list:
            ids = list_manifest_ids(examples_root=examples_root)
            print("\n".join(ids))
            return 0
        if not args.example_id:
            parser.error("example_id is required unless --list is set")
        if args.cleanup:
            dest = cleanup_example(
                args.example_id, repo_root=repo_root, examples_root=examples_root
            )
            payload = {"example_id": args.example_id, "cleaned": str(dest)}
        else:
            payload = fetch_example(
                args.example_id,
                repo_root=repo_root,
                examples_root=examples_root,
                force=args.force,
            )
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    except FetchExampleError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
