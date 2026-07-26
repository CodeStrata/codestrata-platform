"""Local file-system implementation of the repository scanner."""

from collections.abc import Iterable
from pathlib import Path

from codestrata.models import Repository
from codestrata.security.filesystem import iter_repository_files


class LocalRepositoryScanner:
    """Scans a repository located on the local file system."""

    DEFAULT_EXCLUDED_DIRECTORIES = frozenset(
        {
            ".codestrata",
            ".git",
            ".idea",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            ".tox",
            ".venv",
            ".vscode",
            "__pycache__",
            "build",
            "dist",
            "node_modules",
            "reports",
            "target",
        }
    )

    # Align with AnalysisRuntimeSettings.max_source_files default.
    DEFAULT_MAX_FILES = 2000

    def __init__(
        self,
        excluded_directories: Iterable[str] | None = None,
        *,
        max_files: int | None = DEFAULT_MAX_FILES,
    ) -> None:
        additional_exclusions = set(excluded_directories or [])

        self._excluded_directories = set(self.DEFAULT_EXCLUDED_DIRECTORIES) | additional_exclusions
        self._max_files = max_files

    def scan(self, repository_path: Path) -> Repository:
        """Scan a local repository and return repository metadata."""

        resolved_path = repository_path.expanduser().resolve()

        self._validate_repository_path(resolved_path)

        files = self._collect_files(resolved_path)

        return Repository(
            name=resolved_path.name,
            path=resolved_path,
            files=files,
            total_files=len(files),
        )

    def _validate_repository_path(self, repository_path: Path) -> None:
        """Validate that the repository path exists and is a directory."""

        if not repository_path.exists():
            raise FileNotFoundError(f"Repository path does not exist: {repository_path}")

        if not repository_path.is_dir():
            raise NotADirectoryError(f"Repository path is not a directory: {repository_path}")

        if repository_path.is_symlink():
            raise ValueError(
                f"Repository path must not be a symlink: {repository_path}"
            )

    def _collect_files(self, repository_path: Path) -> list[str]:
        """Collect repository files without following symlink escapes."""

        return iter_repository_files(
            repository_path,
            excluded_directories=self._excluded_directories,
            max_files=self._max_files,
        )
