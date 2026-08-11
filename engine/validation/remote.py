"""Remote repository checkout helpers for optional network validation runs."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from validation.models import ValidationRepository

# Bounded waits so GitHub engine-tests cannot hang on a silent git clone.
# Shallow clones of the active remotes normally finish in seconds; 90s covers
# a slow runner without approaching the 45-minute job budget.
NETWORK_GIT_TIMEOUT_SECONDS = 90.0
LOCAL_GIT_TIMEOUT_SECONDS = 30.0


class RemoteRepositoryError(RuntimeError):
    """Raised when a remote repository cannot be prepared."""


def prepare_remote_repository(
    definition: ValidationRepository,
    *,
    clone_root: Path,
) -> Path:
    """Shallow-clone a pinned remote repository and verify the checkout.

    Does not embed credentials. Fails clearly when network/git is unavailable.
    """

    if not definition.remote_url or not definition.pinned_ref:
        raise RemoteRepositoryError("remote repository requires remote_url and pinned_ref")

    if shutil.which("git") is None:
        raise RemoteRepositoryError("git is not available on PATH")

    dest = clone_root / definition.repository_id
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    clone_cmd = [
        "git",
        "clone",
        "--depth",
        "1",
        "--branch",
        definition.pinned_ref,
        definition.remote_url,
        str(dest),
    ]
    # Tags/commits may not work with --branch; fall back to fetch+checkout.
    # Timeouts are not retried — they already mean the remote is unavailable.
    try:
        _run(clone_cmd, network_sensitive=True)
    except RemoteRepositoryError as exc:
        if _is_timeout_error(exc):
            raise
        dest_partial = dest
        if dest_partial.exists():
            shutil.rmtree(dest_partial)
        _run(
            ["git", "clone", "--depth", "1", definition.remote_url, str(dest)],
            network_sensitive=True,
        )
        _run(
            ["git", "-C", str(dest), "fetch", "--depth", "1", "origin", definition.pinned_ref],
            network_sensitive=True,
        )
        _run(
            ["git", "-C", str(dest), "checkout", "--force", definition.pinned_ref],
            network_sensitive=True,
        )

    head = _run(["git", "-C", str(dest), "rev-parse", "HEAD"]).stdout.strip().lower()
    if definition.expected_commit:
        expected = definition.expected_commit.lower()
        if not (head == expected or head.startswith(expected) or expected.startswith(head)):
            raise RemoteRepositoryError(
                f"checked-out commit {head} does not match expected_commit {expected}"
            )
    return dest


def _run(
    command: list[str],
    *,
    network_sensitive: bool = False,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    limit = timeout
    if limit is None:
        limit = (
            NETWORK_GIT_TIMEOUT_SECONDS
            if network_sensitive
            else LOCAL_GIT_TIMEOUT_SECONDS
        )
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=limit,
        )
    except subprocess.TimeoutExpired as exc:
        raise RemoteRepositoryError(
            f"command timed out after {limit:.0f}s: {' '.join(command)}. "
            "Network appears unavailable or the remote is unreachable."
        ) from exc
    except OSError as exc:
        hint = " (network may be unavailable)" if network_sensitive else ""
        raise RemoteRepositoryError(f"failed to execute {command[0]}{hint}: {exc}") from exc
    if completed.returncode != 0:
        stderr = (completed.stderr or completed.stdout or "").strip()
        hint = ""
        if network_sensitive and _looks_network_failure(stderr):
            hint = " Network appears unavailable or the remote is unreachable."
        raise RemoteRepositoryError(
            f"command failed ({completed.returncode}): {' '.join(command)}. {stderr}{hint}"
        )
    return completed


def _is_timeout_error(exc: RemoteRepositoryError) -> bool:
    return "timed out" in str(exc).lower()


def _looks_network_failure(message: str) -> bool:
    lowered = message.lower()
    needles = (
        "could not resolve host",
        "failed to connect",
        "network is unreachable",
        "timed out",
        "connection refused",
        "unable to access",
    )
    return any(needle in lowered for needle in needles)
