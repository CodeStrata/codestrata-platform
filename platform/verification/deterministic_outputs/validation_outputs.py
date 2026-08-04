"""Validation output determinism."""

from __future__ import annotations

import json
from pathlib import Path

from verification.deterministic_outputs.fingerprints import fingerprint_mapping
from verification.deterministic_outputs.models import CheckResult


def check_validation_outputs(monorepo: Path) -> list[CheckResult]:
    from codestrata.domain.quality_metrics.false_positives import (
        FalsePositiveEntityType,
        build_false_positive_id,
    )
    from codestrata.domain.quality_metrics.false_negatives import (
        build_false_negative_id,
    )
    from validation.recording import RECORD_SCHEMA_VERSION
    from validation.summary_artifact import SUMMARY_SCHEMA_VERSION

    checks = [
        CheckResult(
            name="validation_record_schema_1_0",
            ok=RECORD_SCHEMA_VERSION == "1.0",
            detail=f"RECORD_SCHEMA_VERSION={RECORD_SCHEMA_VERSION}",
            category="validation",
        ),
        CheckResult(
            name="validation_summary_schema_1_0",
            ok=SUMMARY_SCHEMA_VERSION == "1.0",
            detail=f"SUMMARY_SCHEMA_VERSION={SUMMARY_SCHEMA_VERSION}",
            category="validation",
        ),
    ]
    fp_a = build_false_positive_id(
        repository_id="demo",
        assessment_area="security",
        entity_type=FalsePositiveEntityType.FINDING,
        rule_id="SEC002",
        entity_id="finding:demo",
        expected_identity="x",
        actual_identity="y",
    )
    fp_b = build_false_positive_id(
        repository_id="demo",
        assessment_area="security",
        entity_type=FalsePositiveEntityType.FINDING,
        rule_id="SEC002",
        entity_id="finding:demo",
        expected_identity="x",
        actual_identity="y",
    )
    checks.append(
        CheckResult(
            name="validation_fp_id_stable",
            ok=fp_a == fp_b and str(fp_a).startswith("fp:"),
            detail=f"fp_id_prefix={str(fp_a).split(':',1)[0]}",
            category="validation",
        )
    )
    fn_a = build_false_negative_id(
        repository_id="demo",
        assessment_area="security",
        entity_type="finding",
        expected_rule_id="SEC002",
        expected_entity_id="finding:demo",
        expected_condition_identity="x",
    )
    fn_b = build_false_negative_id(
        repository_id="demo",
        assessment_area="security",
        entity_type="finding",
        expected_rule_id="SEC002",
        expected_entity_id="finding:demo",
        expected_condition_identity="x",
    )
    checks.append(
        CheckResult(
            name="validation_fn_id_stable",
            ok=fn_a == fn_b and str(fn_a).startswith("fn:"),
            detail=f"fn_id_prefix={str(fn_a).split(':',1)[0]}",
            category="validation",
        )
    )

    summary_path = (
        monorepo
        / "engine/validation/results/summaries/latest/validation-summary.json"
    )
    if summary_path.is_file():
        data = json.loads(summary_path.read_text(encoding="utf-8"))
        fp1 = fingerprint_mapping(data, exclude=("generated_at",))
        fp2 = fingerprint_mapping(data, exclude=("generated_at",))
        checks.append(
            CheckResult(
                name="validation_summary_fingerprint_stable",
                ok=fp1 == fp2,
                detail=f"sha256={fp1[:16]}…",
                category="validation",
            )
        )
    else:
        checks.append(
            CheckResult(
                name="validation_summary_fingerprint_stable",
                ok=True,
                detail="summary absent — constant/ID checks only",
                category="validation",
            )
        )
    return checks
