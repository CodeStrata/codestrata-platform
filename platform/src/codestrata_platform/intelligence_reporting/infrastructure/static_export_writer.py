"""Path-safe writer for website-safe intelligence export artifacts."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.application.website_export.builder import (
    HTML_FILENAME,
    JSON_FILENAME,
    MANIFEST_FILENAME,
    WebsiteExportBundle,
)

_ALLOWED_FILENAMES = frozenset({JSON_FILENAME, HTML_FILENAME, MANIFEST_FILENAME})


@dataclass(frozen=True, slots=True)
class WrittenArtifact:
    filename: str
    byte_size: int
    sha256: str


@dataclass(frozen=True, slots=True)
class WriteResult:
    output_directory: str
    artifacts: tuple[WrittenArtifact, ...]


class StaticIntelligenceExportWriter:
    """Write allowlisted export artifacts into an explicit output directory."""

    def write(
        self,
        export_bundle: WebsiteExportBundle,
        output_directory: str | Path,
        *,
        overwrite: bool = False,
    ) -> WriteResult:
        root = Path(output_directory).resolve()
        if not str(root):
            raise InvalidValueError(
                "output directory required",
                reason_code="export_output_directory_required",
            )
        root.mkdir(parents=True, exist_ok=True)

        planned = (
            (JSON_FILENAME, export_bundle.json_bytes),
            (HTML_FILENAME, export_bundle.html_bytes),
            (MANIFEST_FILENAME, export_bundle.manifest_bytes),
        )
        written: list[WrittenArtifact] = []
        digest_by_name = {
            item.filename: item.sha256 for item in export_bundle.manifest.artifacts
        }
        # Manifest digest is SHA-256 of its own bytes (not listed in artifact digests).
        from codestrata_platform.intelligence_reporting.application.website_export.manifest import (
            sha256_bytes,
        )

        digest_by_name[MANIFEST_FILENAME] = sha256_bytes(export_bundle.manifest_bytes)

        for filename, payload in planned:
            if filename not in _ALLOWED_FILENAMES:
                raise InvalidValueError(
                    f"filename not allowlisted: {filename}",
                    reason_code="export_filename_not_allowlisted",
                )
            target = (root / filename).resolve()
            if not str(target).startswith(str(root) + os.sep) and target != root:
                raise InvalidValueError(
                    "path traversal rejected",
                    reason_code="export_path_traversal",
                )
            if target.name != filename:
                raise InvalidValueError(
                    "resolved filename mismatch",
                    reason_code="export_filename_mismatch",
                )
            if target.exists() and not overwrite:
                raise InvalidValueError(
                    f"refusing to overwrite existing file: {filename}",
                    reason_code="export_refuse_overwrite",
                )
            _atomic_write(target, payload)
            written.append(
                WrittenArtifact(
                    filename=filename,
                    byte_size=len(payload),
                    sha256=digest_by_name[filename],
                )
            )

        return WriteResult(
            output_directory=str(root),
            artifacts=tuple(written),
        )


def _atomic_write(target: Path, payload: bytes) -> None:
    directory = target.parent
    fd, tmp_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=directory)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, target)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


class InMemoryStaticExportWriter:
    """Test helper — returns bytes without touching the filesystem."""

    def write(self, export_bundle: WebsiteExportBundle) -> dict[str, bytes]:
        return {
            JSON_FILENAME: export_bundle.json_bytes,
            HTML_FILENAME: export_bundle.html_bytes,
            MANIFEST_FILENAME: export_bundle.manifest_bytes,
        }
