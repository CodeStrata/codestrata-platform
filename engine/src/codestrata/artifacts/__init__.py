"""Authoritative local runtime artifact layout (Slice 17.12).

All Engine-generated assessment, intelligence, validation, and temporary
runtime outputs belong under ``.codestrata-artifacts/``.
"""

from __future__ import annotations

from codestrata.artifacts.heads import (
    ASSESSMENT_HEAD_SPECS,
    head_basename_for_legacy_filename,
    heads_directory,
    resolve_head_path,
)
from codestrata.artifacts.layout import (
    ARTIFACT_ROOT_NAME,
    AssessmentRunPaths,
    artifact_root,
    ensure_artifact_tree,
    intelligence_run_directory,
    manifests_directory,
    temporary_directory,
    validation_logs_directory,
    validation_repositories_directory,
    validation_suite_directory,
)
from codestrata.artifacts.manifest import (
    ASSESSMENT_HTML_BASENAME,
    ASSESSMENT_JSON_BASENAME,
    ARTIFACT_MANIFEST_BASENAME,
    build_assessment_manifest,
    build_artifact_index_manifest,
    write_assessment_manifest,
    write_artifact_index_manifest,
)
from codestrata.artifacts.migration import (
    LEGACY_REPORTS_DIRECTORY_NAME,
    migrate_legacy_report_tree,
)

__all__ = [
    "ARTIFACT_MANIFEST_BASENAME",
    "ARTIFACT_ROOT_NAME",
    "ASSESSMENT_HEAD_SPECS",
    "ASSESSMENT_HTML_BASENAME",
    "ASSESSMENT_JSON_BASENAME",
    "AssessmentRunPaths",
    "LEGACY_REPORTS_DIRECTORY_NAME",
    "artifact_root",
    "build_assessment_manifest",
    "build_artifact_index_manifest",
    "ensure_artifact_tree",
    "head_basename_for_legacy_filename",
    "heads_directory",
    "intelligence_run_directory",
    "manifests_directory",
    "migrate_legacy_report_tree",
    "resolve_head_path",
    "temporary_directory",
    "validation_logs_directory",
    "validation_repositories_directory",
    "validation_suite_directory",
    "write_assessment_manifest",
    "write_artifact_index_manifest",
]
