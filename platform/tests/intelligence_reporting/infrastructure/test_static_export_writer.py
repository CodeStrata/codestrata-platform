"""Static export writer and manifest digest tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.application.website_export import (
    ExportScope,
    RepositoryIdentityPolicy,
    WebsiteExportBuildPolicy,
    build_website_safe_export,
)
from codestrata_platform.intelligence_reporting.application.website_export.manifest import (
    sha256_bytes,
)
from codestrata_platform.intelligence_reporting.infrastructure.static_export_writer import (
    InMemoryStaticExportWriter,
    StaticIntelligenceExportWriter,
)
from tests.intelligence_reporting.application.website_export.conftest import prepare_export


def _export_bundle():
    return prepare_export(
        export_policy=WebsiteExportBuildPolicy(
            export_scope=ExportScope.ANONYMIZED_EXTERNAL,
            repository_identity_policy=RepositoryIdentityPolicy.ANONYMIZE_ALWAYS,
        )
    )[4]


def test_manifest_digests_and_no_output_paths() -> None:
    bundle = _export_bundle()
    payload = json.loads(bundle.manifest_bytes.decode("utf-8"))
    assert "output" not in json.dumps(payload).lower() or "output_directory" not in payload
    assert "/" not in payload.get("export_id", "")
    names = {item["filename"] for item in payload["artifacts"]}
    assert names == {
        "engineering-intelligence-report.json",
        "engineering-intelligence-report.html",
    }
    by_name = {item["filename"]: item for item in payload["artifacts"]}
    assert by_name["engineering-intelligence-report.json"]["sha256"] == sha256_bytes(
        bundle.json_bytes
    )
    assert by_name["engineering-intelligence-report.html"]["sha256"] == sha256_bytes(
        bundle.html_bytes
    )
    # Manifest does not digest itself in the artifact list (no recursive digest).
    assert "export-manifest.json" not in names


def test_writer_atomic_allowlisted_files(tmp_path: Path) -> None:
    bundle = _export_bundle()
    result = StaticIntelligenceExportWriter().write(bundle, tmp_path)
    assert {item.filename for item in result.artifacts} == {
        "engineering-intelligence-report.json",
        "engineering-intelligence-report.html",
        "export-manifest.json",
    }
    for item in result.artifacts:
        path = tmp_path / item.filename
        assert path.is_file()
        assert path.stat().st_size == item.byte_size
        assert sha256_bytes(path.read_bytes()) == item.sha256


def test_writer_refuses_overwrite(tmp_path: Path) -> None:
    bundle = _export_bundle()
    writer = StaticIntelligenceExportWriter()
    writer.write(bundle, tmp_path)
    with pytest.raises(InvalidValueError, match="overwrite"):
        writer.write(bundle, tmp_path, overwrite=False)


def test_in_memory_writer() -> None:
    bundle = _export_bundle()
    files = InMemoryStaticExportWriter().write(bundle)
    assert files["engineering-intelligence-report.json"] == bundle.json_bytes
    assert files["engineering-intelligence-report.html"] == bundle.html_bytes


def test_determinism_same_bytes() -> None:
    _, _, _, report, bundle, policy = prepare_export(
        export_policy=WebsiteExportBuildPolicy(
            export_scope=ExportScope.ANONYMIZED_EXTERNAL,
            repository_identity_policy=RepositoryIdentityPolicy.ANONYMIZE_ALWAYS,
        )
    )
    again = build_website_safe_export(report, policy=policy)
    assert again.json_bytes == bundle.json_bytes
    assert again.html_bytes == bundle.html_bytes
    assert again.manifest_bytes == bundle.manifest_bytes
    assert again.document.export_metadata is not None
    assert bundle.document.export_metadata is not None
    assert again.document.export_metadata.export_id == (
        bundle.document.export_metadata.export_id
    )
