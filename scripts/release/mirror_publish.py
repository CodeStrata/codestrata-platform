"""Guarded publishing of staged export mirrors to GitHub destinations.

This module never creates GitHub repositories, never force-pushes by default,
and never tags or creates releases. Real pushes require explicit CLI flags.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from release.extraction import tree_fingerprint
from release.inventory import (
    destination_full_name,
    destination_owner,
    destination_repository,
    export_visibility,
)

SNAPSHOT_NAME = ".codestrata-export-snapshot.json"
DEFAULT_BRANCH = "main"


class PublishError(RuntimeError):
    """Raised when a publish preflight or execution guard fails."""


@dataclass
class PublishPlan:
    export_name: str
    owner: str
    repository: str
    full_name: str
    visibility: str
    staging_dir: Path
    source_commit: str
    action: str  # bootstrap | update | dry-run-*
    remote_url: str
    notes: list[str] = field(default_factory=list)


def git_output(args: list[str], *, cwd: Path | None = None) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise PublishError(
            f"git {' '.join(args)} failed: {(completed.stderr or completed.stdout).strip()}"
        )
    return completed.stdout.strip()


def source_is_clean(root: Path) -> bool:
    completed = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(root),
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise PublishError("unable to inspect source git status")
    return completed.stdout.strip() == ""


def current_source_commit(root: Path) -> str:
    return git_output(["rev-parse", "HEAD"], cwd=root)


def load_snapshot(staging_dir: Path) -> dict[str, Any]:
    path = staging_dir / SNAPSHOT_NAME
    if not path.is_file():
        raise PublishError(f"missing staging snapshot: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise PublishError(f"invalid snapshot payload: {path}")
    return data


def verify_snapshot_matches_source(
    staging_dir: Path,
    *,
    source_commit: str,
) -> dict[str, Any]:
    snapshot = load_snapshot(staging_dir)
    recorded = snapshot.get("source_commit")
    if not recorded:
        raise PublishError(
            f"{staging_dir.name}: snapshot missing source_commit; re-export required"
        )
    if str(recorded) != source_commit:
        raise PublishError(
            f"{staging_dir.name}: snapshot source_commit {recorded} "
            f"does not match current HEAD {source_commit}"
        )
    # Recompute content fingerprint excluding the snapshot file.
    fingerprint = {
        key: value for key, value in tree_fingerprint(staging_dir).items() if key != SNAPSHOT_NAME
    }
    digest = (
        __import__("hashlib")
        .sha256(json.dumps(fingerprint, sort_keys=True).encode("utf-8"))
        .hexdigest()
    )
    expected = snapshot.get("content_fingerprint")
    if expected and digest != expected:
        raise PublishError(
            f"{staging_dir.name}: staging content fingerprint mismatch (re-export required)"
        )
    return snapshot


def select_exports(
    manifest: dict[str, Any],
    *,
    repos: list[str] | None,
    publish_all: bool,
) -> list[dict[str, Any]]:
    exports = list(manifest.get("exports") or [])
    if publish_all and repos:
        raise PublishError("use either --all or --repo, not both")
    if not publish_all and not repos:
        raise PublishError("select repositories with --repo NAME (repeatable) or pass --all")
    if publish_all:
        return exports

    wanted = set(repos or [])
    selected: list[dict[str, Any]] = []
    matched: set[str] = set()
    for item in exports:
        aliases = {
            str(item["name"]),
            destination_repository(item),
            destination_full_name(item),
        }
        if wanted & aliases:
            selected.append(item)
            matched |= aliases
    missing = wanted - matched
    if missing:
        raise PublishError(f"unknown export(s): {sorted(missing)}")
    return selected


def iter_publishable_files(staging_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(staging_dir.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        if path.name == SNAPSHOT_NAME:
            continue
        if ".git" in path.parts:
            continue
        files.append(path)
    return files


def copy_staging_into_worktree(staging_dir: Path, worktree: Path) -> None:
    """Replace worktree content (except .git) with staged export files."""

    for child in list(worktree.iterdir()):
        if child.name == ".git":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    for src in iter_publishable_files(staging_dir):
        rel = src.relative_to(staging_dir)
        dest = worktree / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)


def remote_exists(owner: str, repository: str) -> bool:
    url = f"git@github.com:{owner}/{repository}.git"
    completed = subprocess.run(
        ["git", "ls-remote", url, "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    # Empty repo may return code 0 with empty stdout; missing repo returns non-zero.
    if completed.returncode != 0:
        return False
    return True


def remote_is_empty(owner: str, repository: str) -> bool:
    url = f"git@github.com:{owner}/{repository}.git"
    completed = subprocess.run(
        ["git", "ls-remote", url],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise PublishError(f"remote missing or inaccessible: {owner}/{repository}")
    return completed.stdout.strip() == ""


def fetch_github_visibility(
    owner: str,
    repository: str,
    *,
    opener: Callable[[urllib.request.Request], Any] | None = None,
) -> str | None:
    """Return ``public`` or ``private`` when GitHub visibility can be verified."""

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    request = urllib.request.Request(
        f"https://api.github.com/repos/{owner}/{repository}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "codestrata-mirror-publish",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    open_fn = opener or urllib.request.urlopen
    try:
        with open_fn(request, timeout=30) as response:  # type: ignore[arg-type]
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        if error.code in {401, 403, 404}:
            return None
        raise PublishError(
            f"GitHub visibility lookup failed for {owner}/{repository}: HTTP {error.code}"
        ) from error
    except Exception:  # noqa: BLE001
        return None

    if bool(payload.get("private")):
        return "private"
    visibility = str(payload.get("visibility") or "public").lower()
    if visibility not in {"public", "private"}:
        return None
    return visibility


def verify_visibility(
    *,
    owner: str,
    repository: str,
    expected: str,
    lookup: Callable[[str, str], str | None] | None = None,
) -> str:
    actual = (lookup or fetch_github_visibility)(owner, repository)
    if expected == "private":
        if actual is None:
            raise PublishError(
                f"{owner}/{repository}: cannot verify private visibility "
                "(set GITHUB_TOKEN/GH_TOKEN or use authenticated gh access)"
            )
        if actual != "private":
            raise PublishError(f"{owner}/{repository}: expected private, GitHub reports {actual}")
        return actual
    # public
    if actual is None:
        raise PublishError(f"{owner}/{repository}: cannot verify public visibility")
    if actual != "public":
        raise PublishError(f"{owner}/{repository}: expected public, GitHub reports {actual}")
    return actual


def build_plan(
    *,
    root: Path,
    export: dict[str, Any],
    staging_root: Path,
    source_commit: str,
    dry_run: bool,
    remote_exists_fn: Callable[[str, str], bool] | None = None,
    remote_empty_fn: Callable[[str, str], bool] | None = None,
    visibility_lookup: Callable[[str, str], str | None] | None = None,
) -> PublishPlan:
    name = str(export["name"])
    owner = destination_owner(export)
    repository = destination_repository(export)
    visibility = export_visibility(export)
    staging_dir = staging_root / name
    if not staging_dir.is_dir():
        raise PublishError(f"missing staging directory: {staging_dir}")

    verify_snapshot_matches_source(staging_dir, source_commit=source_commit)
    verify_visibility(
        owner=owner,
        repository=repository,
        expected=visibility,
        lookup=visibility_lookup,
    )

    exists_fn = remote_exists_fn or remote_exists
    empty_fn = remote_empty_fn or remote_is_empty
    if not exists_fn(owner, repository):
        raise PublishError(
            f"remote repository missing: {owner}/{repository}. "
            "Create it manually with the correct visibility, then retry."
        )

    empty = empty_fn(owner, repository)
    action = "bootstrap" if empty else "update"
    if dry_run:
        action = f"dry-run-{action}"

    return PublishPlan(
        export_name=name,
        owner=owner,
        repository=repository,
        full_name=f"{owner}/{repository}",
        visibility=visibility,
        staging_dir=staging_dir,
        source_commit=source_commit,
        action=action,
        remote_url=f"git@github.com:{owner}/{repository}.git",
        notes=[
            f"branch={DEFAULT_BRANCH}",
            "force_push=forbidden",
            f"exclude={SNAPSHOT_NAME}",
        ],
    )


def _commit_message(plan: PublishPlan) -> str:
    kind = "Bootstrap" if "bootstrap" in plan.action else "Update"
    return f"{kind} CodeStrata mirror from codestrata-platform@{plan.source_commit[:12]}"


def execute_bootstrap(plan: PublishPlan, *, work_root: Path) -> None:
    worktree = work_root / plan.export_name
    if worktree.exists():
        shutil.rmtree(worktree)
    worktree.mkdir(parents=True)
    git_output(["init", "-b", DEFAULT_BRANCH], cwd=worktree)
    git_output(["remote", "add", "origin", plan.remote_url], cwd=worktree)
    copy_staging_into_worktree(plan.staging_dir, worktree)
    git_output(["add", "-A"], cwd=worktree)
    # Ensure snapshot never staged even if present.
    snapshot = worktree / SNAPSHOT_NAME
    if snapshot.exists():
        snapshot.unlink()
        git_output(["add", "-A"], cwd=worktree)
    status = git_output(["status", "--porcelain"], cwd=worktree)
    if not status:
        raise PublishError(f"{plan.full_name}: nothing to commit for bootstrap")
    git_output(["commit", "-m", _commit_message(plan)], cwd=worktree)
    git_output(["push", "-u", "origin", DEFAULT_BRANCH], cwd=worktree)


def execute_update(plan: PublishPlan, *, work_root: Path) -> None:
    worktree = work_root / plan.export_name
    if worktree.exists():
        shutil.rmtree(worktree)
    git_output(
        [
            "clone",
            "--branch",
            DEFAULT_BRANCH,
            "--single-branch",
            plan.remote_url,
            str(worktree),
        ]
    )
    copy_staging_into_worktree(plan.staging_dir, worktree)
    snapshot = worktree / SNAPSHOT_NAME
    if snapshot.exists():
        snapshot.unlink()
    git_output(["add", "-A"], cwd=worktree)
    status = git_output(["status", "--porcelain"], cwd=worktree)
    if not status:
        plan.notes.append("no-op: remote already matches staged content")
        return
    git_output(["commit", "-m", _commit_message(plan)], cwd=worktree)
    # Refuse non-fast-forward: plain push, never --force.
    completed = subprocess.run(
        ["git", "push", "origin", DEFAULT_BRANCH],
        cwd=str(worktree),
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise PublishError(
            f"{plan.full_name}: push rejected (refusing force-push). "
            f"{(completed.stderr or completed.stdout).strip()}"
        )


def execute_plan(plan: PublishPlan, *, work_root: Path, dry_run: bool) -> None:
    if dry_run:
        return
    if plan.action == "bootstrap":
        execute_bootstrap(plan, work_root=work_root)
        return
    if plan.action == "update":
        execute_update(plan, work_root=work_root)
        return
    raise PublishError(f"unknown action: {plan.action}")
