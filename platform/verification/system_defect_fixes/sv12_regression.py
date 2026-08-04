"""SV.12 population regression after unsafe-metadata fix."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.engineering_intelligence.catalog import monorepo_root_from_here
from verification.engineering_intelligence_quality.build_report import build_sv12_report
from verification.engineering_intelligence_quality.inputs import (
    load_prepared_assessments_from_sv10,
)
from verification.system_defect_fixes.contract import TARGET_REPOSITORY_COUNT
from verification.system_defect_fixes.models import CheckResult


def build_full_22_pipeline(
    monorepo: Path | None = None,
    *,
    output_dir: Path | None = None,
) -> tuple[Any, list[CheckResult]]:
    """Build the complete SV.12 pipeline and assert 22/22 population."""

    root = (monorepo or monorepo_root_from_here()).resolve()
    out = output_dir or (root / "platform" / "reports" / "verification" / "sv12")
    assessments, _sv11, _meta = load_prepared_assessments_from_sv10(monorepo=root)
    artifacts = build_sv12_report(assessments, monorepo=root, output_dir=out)
    ingest = artifacts.pipeline.ingest_result
    report = artifacts.pipeline.report
    included = len(ingest.included)
    rejected = len(ingest.rejected)
    drilldowns = len(getattr(report, "repository_drilldowns", ()) or ())
    checks = [
        CheckResult(
            name="sv12_dataset_population_22",
            ok=included == TARGET_REPOSITORY_COUNT and rejected == 0,
            detail=f"included={included} rejected={rejected}",
        ),
        CheckResult(
            name="sv12_drilldowns_22",
            ok=drilldowns == TARGET_REPOSITORY_COUNT,
            detail=f"drilldowns={drilldowns}",
        ),
        CheckResult(
            name="sv12_no_unsafe_metadata_rejections",
            ok=all(
                (getattr(r, "exclusion_reason", None) or "") != "unsafe_metadata"
                for r in ingest.rejected
            ),
            detail=(
                "rejected_reasons="
                f"{[getattr(r, 'exclusion_reason', None) for r in ingest.rejected]}"
            ),
        ),
    ]
    return artifacts, checks
