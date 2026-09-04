"""Safe, local acquisition of public GitHub repositories for Evidence Studio."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from codestrata.security.redaction import redact_secrets

_OWNER_PATTERN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?")
_REPOSITORY_PATTERN = re.compile(r"[A-Za-z0-9_.-]{1,100}")
_REF_PATTERN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._/-]{0,198}[A-Za-z0-9])?")
_REVISION_PATTERN = re.compile(r"[0-9a-fA-F]{40,64}")


@dataclass(frozen=True)
class GitHubRepositoryLocation:
    owner: str
    repository: str
    canonical_url: str

    @property
    def display_name(self) -> str:
        return f"{self.owner}/{self.repository}"


@dataclass(frozen=True)
class AcquiredRepository:
    path: Path
    source_url: str
    display_name: str
    revision: str
    requested_ref: str | None
    cached: bool


def parse_public_github_url(value: str) -> GitHubRepositoryLocation:
    """Accept only credential-free HTTPS repository URLs on github.com."""

    candidate = value.strip()
    parsed = urlparse(candidate)
    if (
        parsed.scheme.lower() != "https"
        or parsed.hostname is None
        or parsed.hostname.lower() != "github.com"
        or parsed.port not in {None, 443}
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.params
    ):
        raise ValueError(
            "Enter a credential-free public GitHub URL such as "
            "https://github.com/owner/repository."
        )
    parts = parsed.path.strip("/").split("/")
    if len(parts) != 2:
        raise ValueError("GitHub URL must identify exactly one owner and repository.")
    owner, repository = parts
    if repository.endswith(".git"):
        repository = repository[:-4]
    if not _OWNER_PATTERN.fullmatch(owner) or not _REPOSITORY_PATTERN.fullmatch(
        repository
    ):
        raise ValueError("GitHub owner or repository name is not valid.")
    if repository in {".", ".."} or repository.startswith("."):
        raise ValueError("GitHub repository name is not valid.")
    return GitHubRepositoryLocation(
        owner=owner,
        repository=repository,
        canonical_url=f"https://github.com/{owner}/{repository}.git",
    )


def validate_git_ref(value: str | None) -> str | None:
    """Validate a branch or tag before passing it as one git argument."""

    if value is None or not value.strip():
        return None
    candidate = value.strip()
    if (
        not _REF_PATTERN.fullmatch(candidate)
        or ".." in candidate
        or "//" in candidate
        or "@{" in candidate
        or candidate.endswith(("/", ".", ".lock"))
    ):
        raise ValueError("Branch or tag contains unsupported characters.")
    return candidate


def default_repository_cache_root() -> Path:
    """Return a per-user cache without adding another runtime dependency."""

    configured = os.environ.get("CODESTRATA_REPOSITORY_CACHE")
    if configured:
        return Path(configured).expanduser()
    xdg_cache = os.environ.get("XDG_CACHE_HOME")
    if xdg_cache:
        return Path(xdg_cache).expanduser() / "codestrata" / "repositories"
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "CodeStrata" / "repositories"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "CodeStrata" / "repositories"
    return Path.home() / ".cache" / "codestrata" / "repositories"


class GitHubRepositoryAcquirer:
    """Create an immutable shallow checkout in CodeStrata's managed cache."""

    def __init__(
        self,
        *,
        cache_root: Path | None = None,
        timeout_seconds: int = 300,
        max_checkout_bytes: int = 1_000_000_000,
    ) -> None:
        self.cache_root = (cache_root or default_repository_cache_root()).resolve()
        self.timeout_seconds = timeout_seconds
        self.max_checkout_bytes = max_checkout_bytes

    def acquire(self, url: str, requested_ref: str | None = None) -> AcquiredRepository:
        location = parse_public_github_url(url)
        git_ref = validate_git_ref(requested_ref)
        self.cache_root.mkdir(parents=True, exist_ok=True)
        self.cache_root.chmod(0o700)

        environment = os.environ.copy()
        environment.update(
            {
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_LFS_SKIP_SMUDGE": "1",
                "GIT_TERMINAL_PROMPT": "0",
            }
        )
        with tempfile.TemporaryDirectory(
            prefix=".codestrata-clone-", dir=self.cache_root
        ) as temporary:
            checkout = Path(temporary) / "checkout"
            command = [
                "git",
                "-c",
                "credential.helper=",
                "-c",
                f"core.hooksPath={os.devnull}",
                "-c",
                "filter.lfs.smudge=",
                "-c",
                "filter.lfs.required=false",
                "clone",
                "--depth=1",
                "--single-branch",
                "--no-tags",
            ]
            if git_ref:
                command.extend(("--branch", git_ref))
            command.extend(("--", location.canonical_url, str(checkout)))
            try:
                completed = subprocess.run(
                    command,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    env=environment,
                )
            except FileNotFoundError as error:
                raise ValueError("Git is required to acquire a GitHub repository.") from error
            except subprocess.TimeoutExpired as error:
                raise ValueError(
                    f"GitHub clone exceeded the {self.timeout_seconds}-second limit."
                ) from error
            if completed.returncode != 0:
                detail = redact_secrets(completed.stderr[-800:].strip())
                raise ValueError(f"GitHub clone failed: {detail or 'git returned an error'}")

            revision = self._revision(checkout, environment)
            checkout_size = self._checkout_size(checkout)
            if checkout_size > self.max_checkout_bytes:
                raise ValueError(
                    "Cloned repository exceeds the configured local checkout size limit."
                )
            destination = (
                self.cache_root
                / location.owner
                / location.repository
                / revision.lower()
            )
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.parent.chmod(0o700)
            cached = destination.exists()
            if cached:
                if self._revision(destination, environment).lower() != revision.lower():
                    raise ValueError("Existing CodeStrata cache entry failed validation.")
            else:
                checkout.replace(destination)
                destination.chmod(0o700)

        return AcquiredRepository(
            path=destination,
            source_url=location.canonical_url.removesuffix(".git"),
            display_name=location.display_name,
            revision=revision.lower(),
            requested_ref=git_ref,
            cached=cached,
        )

    def _revision(self, repository: Path, environment: dict[str, str]) -> str:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
            env=environment,
        )
        revision = completed.stdout.strip()
        if completed.returncode != 0 or not _REVISION_PATTERN.fullmatch(revision):
            raise ValueError("Cloned repository did not produce a valid Git revision.")
        return revision

    @staticmethod
    def _checkout_size(repository: Path) -> int:
        total = 0
        for path in repository.rglob("*"):
            if path.is_symlink() or not path.is_file():
                continue
            try:
                total += path.stat().st_size
            except OSError:
                continue
        return total
