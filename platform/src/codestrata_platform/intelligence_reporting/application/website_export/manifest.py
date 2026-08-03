"""Deterministic website export manifest and digests."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExportArtifactRecord:
    filename: str
    content_type: str
    sha256: str
    byte_size: int
    classification: str


@dataclass(frozen=True, slots=True)
class WebsiteExportManifest:
    export_id: str
    export_schema_version: str
    source_report_id: str
    interpretation_policy_bundle_id: str
    export_policy_id: str
    artifacts: tuple[ExportArtifactRecord, ...]
    classification: str
    repository_count: int
    generated_at: str | None = None
    limitations: tuple[str, ...] = ()

    def to_stable_dict(self) -> dict[str, object]:
        return {
            "artifacts": [
                {
                    "byte_size": item.byte_size,
                    "classification": item.classification,
                    "content_type": item.content_type,
                    "filename": item.filename,
                    "sha256": item.sha256,
                }
                for item in self.artifacts
            ],
            "classification": self.classification,
            "export_id": self.export_id,
            "export_policy_id": self.export_policy_id,
            "export_schema_version": self.export_schema_version,
            "generated_at": self.generated_at,
            "interpretation_policy_bundle_id": self.interpretation_policy_bundle_id,
            "limitations": list(self.limitations),
            "repository_count": self.repository_count,
            "source_report_id": self.source_report_id,
        }


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def build_manifest(
    *,
    export_id: str,
    export_schema_version: str,
    source_report_id: str,
    interpretation_policy_bundle_id: str,
    export_policy_id: str,
    classification: str,
    repository_count: int,
    json_bytes: bytes,
    html_bytes: bytes,
    generated_at: str | None = None,
    limitations: tuple[str, ...] = (),
) -> tuple[WebsiteExportManifest, bytes]:
    """Build manifest. Digests cover JSON/HTML only (not the manifest itself)."""

    artifacts = (
        ExportArtifactRecord(
            filename="engineering-intelligence-report.json",
            content_type="application/json",
            sha256=sha256_bytes(json_bytes),
            byte_size=len(json_bytes),
            classification=classification,
        ),
        ExportArtifactRecord(
            filename="engineering-intelligence-report.html",
            content_type="text/html; charset=utf-8",
            sha256=sha256_bytes(html_bytes),
            byte_size=len(html_bytes),
            classification=classification,
        ),
    )
    manifest = WebsiteExportManifest(
        export_id=export_id,
        export_schema_version=export_schema_version,
        source_report_id=source_report_id,
        interpretation_policy_bundle_id=interpretation_policy_bundle_id,
        export_policy_id=export_policy_id,
        artifacts=artifacts,
        classification=classification,
        repository_count=repository_count,
        generated_at=generated_at,
        limitations=limitations,
    )
    manifest_bytes = json.dumps(
        manifest.to_stable_dict(),
        sort_keys=True,
        indent=2,
        ensure_ascii=True,
    ).encode("utf-8") + b"\n"
    return manifest, manifest_bytes
