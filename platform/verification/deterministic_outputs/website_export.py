"""Website export byte-for-byte determinism."""

from __future__ import annotations

import tempfile
from pathlib import Path

from codestrata_platform.intelligence_reporting.application.website_export.builder import (
    build_website_safe_export,
)
from codestrata_platform.intelligence_reporting.domain.serialization import (
    from_stable_dict,
    report_to_stable_dict,
)
from codestrata_platform.intelligence_reporting.infrastructure.static_export_writer import (
    StaticIntelligenceExportWriter,
)

from verification.deterministic_outputs.fingerprints import sha256_hex
from verification.deterministic_outputs.inputs import load_sv12_export_bytes
from verification.deterministic_outputs.models import CheckResult, DeterminismDefect
from verification.engineering_intelligence.ingestion import build_pipeline_from_assessments
from verification.engineering_intelligence_quality.inputs import (
    load_prepared_assessments_from_sv10,
)


def check_website_export(monorepo) -> tuple[list[CheckResult], list[DeterminismDefect]]:
    checks: list[CheckResult] = []
    defects: list[DeterminismDefect] = []

    assessments, _sv11, _meta = load_prepared_assessments_from_sv10(monorepo=monorepo)
    pipeline = build_pipeline_from_assessments(
        assessments,
        title="SV.15 website export determinism",
    )
    left = build_website_safe_export(pipeline.report, generated_at=None)
    right = build_website_safe_export(pipeline.report, generated_at=None)
    restored = from_stable_dict(report_to_stable_dict(pipeline.report))
    via_restore = build_website_safe_export(restored, generated_at=None)

    checks.append(
        CheckResult(
            name="website_json_bytes_identical",
            ok=left.json_bytes == right.json_bytes == via_restore.json_bytes,
            detail=f"sha256={sha256_hex(left.json_bytes)[:16]}…",
            category="website_export",
        )
    )
    checks.append(
        CheckResult(
            name="website_html_bytes_identical",
            ok=left.html_bytes == right.html_bytes == via_restore.html_bytes,
            detail=f"sha256={sha256_hex(left.html_bytes)[:16]}…",
            category="website_export",
        )
    )
    checks.append(
        CheckResult(
            name="website_manifest_bytes_identical",
            ok=left.manifest_bytes == right.manifest_bytes == via_restore.manifest_bytes,
            detail=f"sha256={sha256_hex(left.manifest_bytes)[:16]}…",
            category="website_export",
        )
    )
    export_id = left.document.export_metadata.export_id  # type: ignore[union-attr]
    checks.append(
        CheckResult(
            name="website_export_id_stable",
            ok=(
                export_id
                == right.document.export_metadata.export_id  # type: ignore[union-attr]
                == via_restore.document.export_metadata.export_id  # type: ignore[union-attr]
            ),
            detail=f"export_id={export_id}",
            category="website_export",
        )
    )

    # Output directory independence.
    writer = StaticIntelligenceExportWriter()
    with tempfile.TemporaryDirectory(prefix="sv15we_a_") as a:
        with tempfile.TemporaryDirectory(prefix="sv15 we spaces_") as b:
            writer.write(left, Path(a), overwrite=True)
            writer.write(right, Path(b), overwrite=True)
            a_json = (Path(a) / "engineering-intelligence-report.json").read_bytes()
            b_json = (Path(b) / "engineering-intelligence-report.json").read_bytes()
            a_html = (Path(a) / "engineering-intelligence-report.html").read_bytes()
            b_html = (Path(b) / "engineering-intelligence-report.html").read_bytes()
            a_man = (Path(a) / "export-manifest.json").read_bytes()
            b_man = (Path(b) / "export-manifest.json").read_bytes()
    dir_ok = a_json == b_json == left.json_bytes and a_html == b_html and a_man == b_man
    checks.append(
        CheckResult(
            name="website_output_dir_independent",
            ok=dir_ok,
            detail="two temp dirs (incl. spaces) byte-identical",
            category="website_export",
        )
    )
    if not dir_ok:
        defects.append(
            DeterminismDefect(
                classification="path_dependency",
                contract="website_safe_export",
                expected="output directory independent bytes",
                actual="byte drift across directories",
            )
        )

    # Preserved SV.12 export still readable (not necessarily equal to rebuilt).
    preserved = load_sv12_export_bytes(monorepo)
    checks.append(
        CheckResult(
            name="website_sv12_export_present",
            ok=all(len(v) > 0 for v in preserved.values()),
            detail="sv12 json/html/manifest present",
            category="website_export",
        )
    )
    return checks, defects
