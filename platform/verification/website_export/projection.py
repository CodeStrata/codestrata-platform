"""Website-safe projection and export-identity verification."""

from __future__ import annotations

import json

from codestrata_platform.intelligence_reporting.application.website_export import (
    ARTIFACT_TEMPLATE_VERSION,
    WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION,
    WebsiteExportBuildPolicy,
    build_export_id,
    build_website_safe_export,
    project_website_safe_export,
)
from codestrata_platform.intelligence_reporting.application.website_export.validation import (
    validate_website_safe_document,
)

from verification.website_export.inputs import VerifiedExportInput
from verification.website_export.models import CheckResult


def check_export_policy(verified: VerifiedExportInput) -> list[CheckResult]:
    policy = verified.policy
    checks = [
        CheckResult(
            name="policy:schema_1_0",
            ok=policy.export_schema_version == WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION == "1.0",
            detail=policy.export_schema_version,
            category="policy",
        ),
        CheckResult(
            name="policy:external_assets_forbidden",
            ok=policy.allow_external_assets is False,
            detail=str(policy.allow_external_assets),
            category="policy",
        ),
        CheckResult(
            name="policy:token_deterministic",
            ok=bool(policy.policy_token)
            and policy.policy_token == WebsiteExportBuildPolicy.for_report_scope(
                verified.report.report_scope
            ).policy_token,
            detail="token stable",
            category="policy",
        ),
        CheckResult(
            name="policy:public_oss_scope",
            ok=policy.export_scope.value == "public_oss",
            detail=policy.export_scope.value,
            category="policy",
            scenario="A",
        ),
        CheckResult(
            name="policy:artifact_template",
            ok=policy.artifact_template_version == ARTIFACT_TEMPLATE_VERSION,
            detail=policy.artifact_template_version,
            category="policy",
        ),
    ]
    return checks


def check_projection(verified: VerifiedExportInput) -> list[CheckResult]:
    doc = verified.bundle.document
    dataset_id = verified.report.dataset.dataset_id.value
    payload = json.dumps(
        {
            "schema": doc.export_schema_version,
            "export_id": doc.export_metadata.export_id if doc.export_metadata else "",
            "report_id": doc.report_id,
            "source_dataset_id": dataset_id,
            "scope": doc.scope,
            "classification": doc.classification,
            "repo_count": doc.dataset_summary.get("repository_count"),
            "tech": len(doc.technology_distribution),
            "caps": len(doc.capability_comparisons),
            "heads": len(doc.assessment_head_distributions),
            "patterns": len(doc.recurring_patterns),
            "observations": len(doc.modernization_observations),
            "limitations": len(doc.limitations),
            "drilldowns": len(doc.repository_drilldowns),
            "confidence": doc.confidence.level if doc.confidence else None,
            "methodology": doc.methodology is not None,
            "metadata": doc.export_metadata is not None,
        },
        sort_keys=True,
    )
    blob = verified.bundle.json_bytes.decode("utf-8").lower()
    checks = [
        CheckResult(
            name="projection:schema",
            ok=doc.export_schema_version == "1.0",
            detail=doc.export_schema_version,
            category="projection",
        ),
        CheckResult(
            name="projection:source_report_id",
            ok=doc.report_id == verified.report.report_id.value,
            detail=doc.report_id,
            category="projection",
        ),
        CheckResult(
            name="projection:source_dataset_id_tracked",
            ok=bool(dataset_id.startswith("dataset:")),
            detail=dataset_id,
            category="projection",
        ),
        CheckResult(
            name="projection:interp_bundle",
            ok=(
                doc.export_metadata is not None
                and doc.export_metadata.interpretation_policy_bundle_id
                == verified.report.interpretation_policy_bundle_id
            ),
            detail=(
                doc.export_metadata.interpretation_policy_bundle_id
                if doc.export_metadata
                else ""
            ),
            category="projection",
        ),
        CheckResult(
            name="projection:five_drilldowns",
            ok=len(doc.repository_drilldowns) == 5,
            detail=f"count={len(doc.repository_drilldowns)}",
            category="projection",
            scenario="A",
        ),
        CheckResult(
            name="projection:validation_passes",
            ok=_validate_ok(verified),
            detail="validate_website_safe_document",
            category="projection",
        ),
        CheckResult(
            name="projection:no_forbidden_payload_keys",
            ok=all(key not in blob for key in ('"findings"', '"evidence"', "graph_payload")),
            detail="allowlisted projection",
            category="projection",
        ),
        CheckResult(
            name="projection:summary",
            ok=True,
            detail=payload[:240],
            category="projection",
        ),
    ]
    return checks


def _validate_ok(verified: VerifiedExportInput) -> bool:
    try:
        validate_website_safe_document(verified.bundle.document, policy=verified.policy)
        return True
    except Exception:  # noqa: BLE001 — verification outcome only
        return False


def check_export_identity(verified: VerifiedExportInput) -> list[CheckResult]:
    meta = verified.bundle.document.export_metadata
    assert meta is not None
    export_id = meta.export_id
    expected = build_export_id(
        source_report_id=verified.bundle.document.report_id,
        interpretation_policy_bundle_id=meta.interpretation_policy_bundle_id,
        export_policy_token=verified.policy.policy_token,
        export_schema_version=verified.policy.export_schema_version,
        artifact_template_version=verified.policy.artifact_template_version,
    )
    again = build_website_safe_export(
        verified.report, policy=verified.policy, generated_at=None
    )
    changed_report = build_export_id(
        source_report_id="eir:000000000000000000000000",
        interpretation_policy_bundle_id=meta.interpretation_policy_bundle_id,
        export_policy_token=verified.policy.policy_token,
        export_schema_version=verified.policy.export_schema_version,
        artifact_template_version=verified.policy.artifact_template_version,
    )
    changed_policy = build_export_id(
        source_report_id=verified.bundle.document.report_id,
        interpretation_policy_bundle_id=meta.interpretation_policy_bundle_id,
        export_policy_token=verified.policy.policy_token + ":mutated",
        export_schema_version=verified.policy.export_schema_version,
        artifact_template_version=verified.policy.artifact_template_version,
    )
    changed_template = build_export_id(
        source_report_id=verified.bundle.document.report_id,
        interpretation_policy_bundle_id=meta.interpretation_policy_bundle_id,
        export_policy_token=verified.policy.policy_token,
        export_schema_version=verified.policy.export_schema_version,
        artifact_template_version="eir-export-artifacts-v999",
    )
    return [
        CheckResult(
            name="identity:format",
            ok=export_id.startswith("eir-export:") and len(export_id) == len("eir-export:") + 24,
            detail=export_id,
            category="identity",
        ),
        CheckResult(
            name="identity:matches_builder",
            ok=export_id == expected,
            detail="build_export_id",
            category="identity",
        ),
        CheckResult(
            name="identity:stable_rerun",
            ok=again.document.export_metadata.export_id == export_id,  # type: ignore[union-attr]
            detail="same inputs",
            category="identity",
        ),
        CheckResult(
            name="identity:changes_with_report",
            ok=changed_report != export_id,
            detail="source report id",
            category="identity",
        ),
        CheckResult(
            name="identity:changes_with_policy_token",
            ok=changed_policy != export_id,
            detail="policy token",
            category="identity",
            scenario="T",
        ),
        CheckResult(
            name="identity:changes_with_template",
            ok=changed_template != export_id,
            detail="artifact template",
            category="identity",
        ),
        CheckResult(
            name="identity:no_path_influence",
            ok="/Users/" not in export_id and "tmp" not in export_id,
            detail="path-free",
            category="identity",
        ),
    ]


def check_reproject_same_document(verified: VerifiedExportInput) -> list[CheckResult]:
    left = project_website_safe_export(verified.report, policy=verified.policy)
    right = project_website_safe_export(verified.report, policy=verified.policy)
    return [
        CheckResult(
            name="projection:reproject_stable_export_id",
            ok=(
                left.export_metadata is not None
                and right.export_metadata is not None
                and left.export_metadata.export_id == right.export_metadata.export_id
            ),
            detail="stable",
            category="projection",
        )
    ]
