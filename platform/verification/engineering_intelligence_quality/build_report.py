"""Build 22-repository EIR + website-safe export via SV.6/SV.8 builders."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from codestrata_platform.intelligence_reporting.application.website_export.builder import (
    WebsiteExportBundle,
    build_website_safe_export,
)
from codestrata_platform.intelligence_reporting.infrastructure.static_export_writer import (
    StaticIntelligenceExportWriter,
)
from verification.engineering_intelligence.assessment_inputs import PreparedAssessment
from verification.engineering_intelligence.ingestion import (
    PipelineArtifacts,
    build_pipeline_from_assessments,
)
from verification.engineering_intelligence_quality.contract import (
    EXPORT_MANIFEST,
    REPORT_HTML,
    REPORT_JSON,
    SV12_OUTPUT_RELATIVE,
)
from verification.engineering_intelligence.catalog import monorepo_root_from_here


@dataclass(frozen=True, slots=True)
class BuiltSv12Report:
    pipeline: PipelineArtifacts
    export: WebsiteExportBundle
    output_dir: Path
    report_payload: dict[str, Any]
    json_text: str
    html_text: str
    manifest_payload: dict[str, Any]


def default_sv12_output_dir(monorepo: Path | None = None) -> Path:
    root = (monorepo or monorepo_root_from_here()).resolve()
    return root / SV12_OUTPUT_RELATIVE


def build_sv12_report(
    assessments: list[PreparedAssessment],
    *,
    output_dir: Path | None = None,
    monorepo: Path | None = None,
    title: str = "SV.12 Engineering Intelligence Quality Review (22 curated repositories)",
) -> BuiltSv12Report:
    if len(assessments) != 22:
        raise ValueError(f"SV.12 requires 22 assessments, got {len(assessments)}")
    out = (output_dir or default_sv12_output_dir(monorepo)).resolve()
    # Never write into platform/demo/
    if out.name == "demo" and out.parent.name == "platform":
        raise ValueError("refusing to overwrite platform/demo/")
    out.mkdir(parents=True, exist_ok=True)

    pipeline = build_pipeline_from_assessments(
        assessments,
        title=title,
    )
    # Retag dataset name for verification (payload already built; title is enough).
    export = build_website_safe_export(pipeline.report)
    StaticIntelligenceExportWriter().write(export, out, overwrite=True)

    import json

    manifest = json.loads(export.manifest_bytes.decode("utf-8"))
    return BuiltSv12Report(
        pipeline=pipeline,
        export=export,
        output_dir=out,
        report_payload=pipeline.report_payload,
        json_text=export.json_bytes.decode("utf-8"),
        html_text=export.html_bytes.decode("utf-8"),
        manifest_payload=manifest,
    )


def assert_export_files(output_dir: Path) -> None:
    for name in (REPORT_JSON, REPORT_HTML, EXPORT_MANIFEST):
        if not (output_dir / name).is_file():
            raise FileNotFoundError(f"missing export artifact: {name}")
