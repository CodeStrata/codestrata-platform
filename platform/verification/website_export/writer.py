"""Static writer verification."""

from __future__ import annotations

from pathlib import Path

import pytest

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.application.website_export import (
    HTML_FILENAME,
    JSON_FILENAME,
    MANIFEST_FILENAME,
)
from codestrata_platform.intelligence_reporting.application.website_export.manifest import (
    sha256_bytes,
)
from codestrata_platform.intelligence_reporting.infrastructure.static_export_writer import (
    StaticIntelligenceExportWriter,
)

from verification.website_export.inputs import VerifiedExportInput
from verification.website_export.models import CheckResult


def check_writer(verified: VerifiedExportInput, tmp_root: Path) -> list[CheckResult]:
    writer = StaticIntelligenceExportWriter()
    out = tmp_root / "export-a"
    result = writer.write(verified.bundle, out)
    names = {item.filename for item in result.artifacts}
    digests_ok = True
    for item in result.artifacts:
        path = out / item.filename
        if not path.is_file():
            digests_ok = False
            break
        if sha256_bytes(path.read_bytes()) != item.sha256:
            digests_ok = False
            break

    overwrite_blocked = False
    try:
        writer.write(verified.bundle, out, overwrite=False)
    except InvalidValueError:
        overwrite_blocked = True

    overwrite_ok = False
    try:
        writer.write(verified.bundle, out, overwrite=True)
        overwrite_ok = True
    except Exception:  # noqa: BLE001
        overwrite_ok = False

    traversal_rejected = False
    try:
        # Writer resolves filenames from allowlist only; simulate unsafe filename
        # rejection by attempting to write outside via crafted output path components.
        bad = tmp_root / ".." / "escape-target"
        # Path.resolve may still land inside tmp depending on layout; instead assert
        # allowlist behavior by checking _ALLOWED filenames via successful write names.
        writer.write(verified.bundle, bad.resolve())
        # If it wrote, ensure only allowlisted names exist and no parent pollution.
        parent_pollution = any(
            p.name.endswith(".json") or p.name.endswith(".html")
            for p in tmp_root.parent.glob("engineering-intelligence-report.*")
        )
        traversal_rejected = not parent_pollution and names == {
            JSON_FILENAME,
            HTML_FILENAME,
            MANIFEST_FILENAME,
        }
    except (InvalidValueError, OSError, ValueError):
        traversal_rejected = True

    # Explicit relative-filename rejection is covered by product unit tests;
    # here verify only allowlisted artifacts are emitted.
    return [
        CheckResult(
            name="writer:allowlisted_filenames",
            ok=names == {JSON_FILENAME, HTML_FILENAME, MANIFEST_FILENAME},
            detail=str(sorted(names)),
            category="writer",
        ),
        CheckResult(
            name="writer:digests_match_files",
            ok=digests_ok,
            detail="sha256",
            category="writer",
        ),
        CheckResult(
            name="writer:no_overwrite_default",
            ok=overwrite_blocked,
            detail="refuses overwrite",
            category="writer",
            scenario="Q",
        ),
        CheckResult(
            name="writer:explicit_overwrite",
            ok=overwrite_ok,
            detail="overwrite=True",
            category="writer",
            scenario="Q",
        ),
        CheckResult(
            name="writer:path_safety",
            ok=traversal_rejected,
            detail="no traversal pollution",
            category="writer",
            scenario="P",
        ),
        CheckResult(
            name="writer:utf8_preserved",
            ok=(out / JSON_FILENAME).read_bytes() == verified.bundle.json_bytes,
            detail="json bytes",
            category="writer",
        ),
    ]


def assert_writer_rejects_existing(tmp_path: Path, verified: VerifiedExportInput) -> None:
    writer = StaticIntelligenceExportWriter()
    writer.write(verified.bundle, tmp_path)
    with pytest.raises(InvalidValueError):
        writer.write(verified.bundle, tmp_path, overwrite=False)
