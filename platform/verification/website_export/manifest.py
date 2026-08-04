"""Manifest verification."""

from __future__ import annotations

import json

from codestrata_platform.intelligence_reporting.application.website_export import (
    HTML_FILENAME,
    JSON_FILENAME,
    MANIFEST_FILENAME,
)
from codestrata_platform.intelligence_reporting.application.website_export.manifest import (
    sha256_bytes,
)

from verification.website_export.inputs import VerifiedExportInput
from verification.website_export.models import CheckResult


def check_manifest(verified: VerifiedExportInput) -> list[CheckResult]:
    payload = json.loads(verified.bundle.manifest_bytes.decode("utf-8"))
    artifacts = {item["filename"]: item for item in payload.get("artifacts", [])}
    json_digest = sha256_bytes(verified.bundle.json_bytes)
    html_digest = sha256_bytes(verified.bundle.html_bytes)
    return [
        CheckResult(
            name="manifest:filename_contract",
            ok=MANIFEST_FILENAME == "export-manifest.json",
            detail=MANIFEST_FILENAME,
            category="manifest",
        ),
        CheckResult(
            name="manifest:export_id",
            ok=payload.get("export_id")
            == verified.bundle.document.export_metadata.export_id,  # type: ignore[union-attr]
            detail=str(payload.get("export_id")),
            category="manifest",
        ),
        CheckResult(
            name="manifest:schema_version",
            ok=payload.get("export_schema_version") == "1.0",
            detail=str(payload.get("export_schema_version")),
            category="manifest",
        ),
        CheckResult(
            name="manifest:artifact_set",
            ok=set(artifacts) == {JSON_FILENAME, HTML_FILENAME},
            detail=str(sorted(artifacts)),
            category="manifest",
        ),
        CheckResult(
            name="manifest:json_digest",
            ok=artifacts[JSON_FILENAME]["sha256"] == json_digest,
            detail="sha256 match",
            category="manifest",
        ),
        CheckResult(
            name="manifest:html_digest",
            ok=artifacts[HTML_FILENAME]["sha256"] == html_digest,
            detail="sha256 match",
            category="manifest",
        ),
        CheckResult(
            name="manifest:no_self_digest",
            ok=MANIFEST_FILENAME not in artifacts,
            detail="no recursive digest",
            category="manifest",
        ),
        CheckResult(
            name="manifest:no_output_directory",
            ok="output_directory" not in payload and "/Users/" not in json.dumps(payload),
            detail="path-free",
            category="manifest",
        ),
        CheckResult(
            name="manifest:source_report_id",
            ok=payload.get("source_report_id") == verified.report.report_id.value,
            detail=str(payload.get("source_report_id")),
            category="manifest",
        ),
        CheckResult(
            name="manifest:digest_changes_with_bytes",
            ok=sha256_bytes(verified.bundle.json_bytes + b" ") != json_digest,
            detail="sensitive",
            category="manifest",
            scenario="S",
        ),
    ]
