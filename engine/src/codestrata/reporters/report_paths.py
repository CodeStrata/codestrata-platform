"""Utilities for creating and retaining analysis report run directories.

Slice 17.12: assessment runs live under
``.codestrata-artifacts/assessments/<repo>-<YYYYMMDD-HHMMSS>/`` with
``assessment.html``, ``assessment.json`` (manifest), and ``heads/``.
"""

from __future__ import annotations

import logging
import re
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from codestrata.artifacts.layout import (
    ARTIFACT_ROOT_NAME,
    ASSESSMENTS_DIRNAME,
    AssessmentRunPaths,
    create_assessment_run_paths,
    format_run_timestamp,
    sanitize_repository_slug,
)
from codestrata.artifacts.manifest import ASSESSMENT_HTML_BASENAME, ASSESSMENT_JSON_BASENAME
from codestrata.models import AnalysisResult

logger = logging.getLogger(__name__)

_REPORT_RUN_DIRECTORY_PATTERN = re.compile(r"^\d{8}-\d{6}$")
_ASSESSMENT_RUN_ID_PATTERN = re.compile(r"^[a-z0-9._-]+-\d{8}-\d{6}$")
DEFAULT_RETAINED_RUN_COUNT = 3
DEFAULT_ACTIVE_REPORT_RUNS_TO_KEEP = DEFAULT_RETAINED_RUN_COUNT
_DEFAULT_REPORTS_TO_KEEP = DEFAULT_RETAINED_RUN_COUNT
_UNSAFE_REPOSITORY_CHARS = re.compile(r"[^a-z0-9._-]+")

LEGACY_REPORTS_DIRNAME = "reports"
LEGACY_HTML_BASENAME = "report.html"
LEGACY_JSON_BASENAME = "report.json"

DEFAULT_ASSESS_OUTPUT_DIRECTORY = Path(f"{ARTIFACT_ROOT_NAME}/{ASSESSMENTS_DIRNAME}")


class ReportRetentionError(RuntimeError):
    """Raised when an older report run cannot be pruned safely."""


@dataclass(frozen=True)
class ReportPaths:
    """Paths for all reports generated during one analysis run."""

    directory: Path
    text_report: Path
    json_report: Path
    html_report: Path
    timestamp: str
    repository_name: str
    run_id: str = ""
    heads_directory: Path | None = None

    @property
    def run_directory(self) -> Path:
        return self.directory

    @property
    def run_timestamp(self) -> str:
        return self.timestamp

    @property
    def html_report_path(self) -> Path:
        return self.html_report

    @property
    def json_report_path(self) -> Path:
        return self.json_report

    @property
    def text_report_path(self) -> Path:
        return self.text_report


def sanitize_repository_directory_name(repository_name: str) -> str:
    """Return a filesystem-safe repository directory name."""

    return sanitize_repository_slug(repository_name)


def format_report_run_timestamp(moment: datetime | None = None) -> str:
    """Return a UTC run timestamp formatted as ``YYYYMMDD-HHMMSS``."""

    return format_run_timestamp(moment)


def _resolve_output_root(base_directory: Path) -> Path:
    """Map legacy ``reports`` default to the authoritative assessments root."""

    if base_directory == Path(LEGACY_REPORTS_DIRNAME) or base_directory.as_posix() == LEGACY_REPORTS_DIRNAME:
        return DEFAULT_ASSESS_OUTPUT_DIRECTORY
    return base_directory


def create_report_paths(
    result: AnalysisResult,
    base_directory: Path,
    *,
    timestamp: str | None = None,
    clock: Callable[[], datetime] | None = None,
    create_directory: bool = True,
) -> ReportPaths:
    """Create report paths for one analysis or assessment run.

    Layout (Slice 17.12)::

        <output_root>/<sanitized-repository>-<YYYYMMDD-HHMMSS>/
            assessment.html
            assessment.json
            heads/
            report.txt   # legacy scan only
    """

    if timestamp is not None:
        run_timestamp = timestamp
        if not _REPORT_RUN_DIRECTORY_PATTERN.match(run_timestamp):
            raise ValueError(f"timestamp must match YYYYMMDD-HHMMSS, got {run_timestamp!r}")
    else:
        now = clock() if clock is not None else datetime.now(UTC)
        run_timestamp = format_report_run_timestamp(now)

    output_root = _resolve_output_root(Path(base_directory))
    # Workspace base for artifact tree when using default assessments path.
    workspace: Path | None = None
    if output_root == DEFAULT_ASSESS_OUTPUT_DIRECTORY or output_root.as_posix().endswith(
        f"{ARTIFACT_ROOT_NAME}/{ASSESSMENTS_DIRNAME}"
    ):
        # If relative default, create under cwd; if absolute assessments path, use parent.parent.
        if output_root.is_absolute():
            workspace = output_root.parent.parent
        else:
            workspace = Path.cwd()
        run = create_assessment_run_paths(
            repository_name=result.repository.name,
            base=workspace,
            timestamp=run_timestamp,
            create_directory=create_directory,
        )
        return _from_assessment_run(run)

    # Custom --output: still use flat <root>/<run-id>/ with new basenames.
    repo = sanitize_repository_directory_name(result.repository.name)
    run_id = f"{repo}-{run_timestamp}"
    run_directory = output_root / run_id
    heads = run_directory / "heads"
    if create_directory:
        heads.mkdir(parents=True, exist_ok=True)
    return ReportPaths(
        directory=run_directory,
        text_report=run_directory / "report.txt",
        json_report=run_directory / ASSESSMENT_JSON_BASENAME,
        html_report=run_directory / ASSESSMENT_HTML_BASENAME,
        timestamp=run_timestamp,
        repository_name=repo,
        run_id=run_id,
        heads_directory=heads,
    )


def _from_assessment_run(run: AssessmentRunPaths) -> ReportPaths:
    return ReportPaths(
        directory=run.directory,
        text_report=run.text_report,
        json_report=run.assessment_json,
        html_report=run.assessment_html,
        timestamp=run.timestamp,
        repository_name=run.repository_name,
        run_id=run.run_id,
        heads_directory=run.heads_directory,
    )


def is_completed_report_run(run_directory: Path) -> bool:
    """Return True when a run directory contains required report artifacts."""

    if run_directory.is_symlink() or not run_directory.is_dir():
        return False
    modern = (run_directory / ASSESSMENT_HTML_BASENAME).is_file() and (
        run_directory / ASSESSMENT_JSON_BASENAME
    ).is_file()
    legacy = (run_directory / LEGACY_HTML_BASENAME).is_file() and (
        run_directory / LEGACY_JSON_BASENAME
    ).is_file()
    return modern or legacy


def list_active_report_run_directories(repository_directory: Path) -> list[Path]:
    """Return run directories under a parent, newest first.

    Supports:
    - legacy ``reports/<repo>/<stamp>/``
    - Slice 17.12 ``.codestrata-artifacts/assessments/<repo>-<stamp>/`` when
      ``repository_directory`` is the assessments root (filter by slug prefix) or
      a legacy repo folder.
    """

    if not repository_directory.exists():
        return []

    candidates: list[Path] = []
    for path in repository_directory.iterdir():
        if path.is_symlink() or not path.is_dir():
            continue
        if _REPORT_RUN_DIRECTORY_PATTERN.match(path.name):
            candidates.append(path)
        elif _ASSESSMENT_RUN_ID_PATTERN.match(path.name):
            candidates.append(path)
    return sorted(candidates, key=lambda path: path.name, reverse=True)


def list_completed_report_run_directories(repository_directory: Path) -> list[Path]:
    """Return completed run directories, newest first."""

    return [
        path
        for path in list_active_report_run_directories(repository_directory)
        if is_completed_report_run(path)
    ]


def list_completed_assessment_runs(
    assessments_root: Path,
    *,
    repository_slug: str | None = None,
) -> list[Path]:
    """List completed assessment runs under the assessments root."""

    runs = list_completed_report_run_directories(assessments_root)
    if repository_slug is None:
        return runs
    slug = sanitize_repository_slug(repository_slug)
    prefix = f"{slug}-"
    return [path for path in runs if path.name.startswith(prefix)]


def _is_safe_run_directory(repository_directory: Path, run_directory: Path) -> bool:
    try:
        repository_root = repository_directory.resolve(strict=False)
        candidate = run_directory.resolve(strict=False)
    except OSError:
        return False
    if candidate == repository_root:
        return False
    if candidate.parent != repository_root:
        return False
    if run_directory.is_symlink():
        return False
    return bool(
        _REPORT_RUN_DIRECTORY_PATTERN.match(run_directory.name)
        or _ASSESSMENT_RUN_ID_PATTERN.match(run_directory.name)
    )


def retain_recent_reports(
    repository_directory: Path,
    keep: int = DEFAULT_RETAINED_RUN_COUNT,
    *,
    repository_slug: str | None = None,
) -> list[Path]:
    """Keep only the newest completed report-run directories.

    When ``repository_slug`` is set and ``repository_directory`` is the
    assessments root, only runs for that slug are considered.
    """

    if keep < 1:
        raise ValueError("keep must be at least 1")

    if not repository_directory.exists():
        return []

    if repository_slug is not None:
        completed = list_completed_assessment_runs(
            repository_directory, repository_slug=repository_slug
        )
    else:
        completed = list_completed_report_run_directories(repository_directory)

    to_delete = completed[keep:]
    deleted: list[Path] = []
    for outdated_directory in to_delete:
        if not _is_safe_run_directory(repository_directory, outdated_directory):
            logger.warning(
                "Skipping unsafe report run path during retention: %s",
                outdated_directory,
            )
            continue
        try:
            shutil.rmtree(outdated_directory)
        except OSError as error:
            raise ReportRetentionError(
                f"Failed to delete aged report run {outdated_directory.name!r}: {error}"
            ) from error
        logger.info("Removed aged report run %s", outdated_directory.name)
        deleted.append(outdated_directory)
    return deleted


def prune_excess_report_runs(
    repository_directory: Path,
    *,
    keep: int = DEFAULT_RETAINED_RUN_COUNT,
    repository_slug: str | None = None,
) -> list[Path]:
    """Alias for :func:`retain_recent_reports` used by assessment cleanup."""

    return retain_recent_reports(
        repository_directory, keep=keep, repository_slug=repository_slug
    )
