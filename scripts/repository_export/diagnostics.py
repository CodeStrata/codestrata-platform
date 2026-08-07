"""CLI diagnostics helpers (no absolute paths in machine-readable output)."""

from __future__ import annotations

import json
import sys
from typing import TextIO

from repository_export.models import ExportDiagnostics
from repository_export.policy import MANIFEST_SCHEMA_NAME, MANIFEST_SCHEMA_VERSION


def print_human_summary(
    diagnostics: ExportDiagnostics,
    *,
    stream: TextIO | None = None,
) -> None:
    out = stream or sys.stdout
    mode = "DRY-RUN" if diagnostics.dry_run else "EXPORT"
    print(f"[{mode}] target={diagnostics.target} status={diagnostics.status}", file=out)
    print(
        f"  files={diagnostics.file_count} "
        f"additions={diagnostics.addition_count} "
        f"modifications={diagnostics.modification_count} "
        f"removals={diagnostics.removal_count} "
        f"unchanged_hint={diagnostics.file_count - diagnostics.addition_count - diagnostics.modification_count} "
        f"conflicts={diagnostics.conflict_count}",
        file=out,
    )
    print(
        f"  manifest={MANIFEST_SCHEMA_NAME}:{MANIFEST_SCHEMA_VERSION} "
        f"dry_run={str(diagnostics.dry_run).lower()}",
        file=out,
    )
    if diagnostics.limitation_codes:
        print(f"  limitations={','.join(diagnostics.limitation_codes)}", file=out)


def print_json_diagnostics(diagnostics: ExportDiagnostics, *, stream: TextIO | None = None) -> None:
    out = stream or sys.stdout
    print(json.dumps(diagnostics.to_dict(), indent=2, sort_keys=True), file=out)
