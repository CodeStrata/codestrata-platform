"""Slice 8.5 boundary tests: wiring isolation + low-level partition-vs-policy checks.

Mirrors ``test_assessment_metadata_partition_boundary.py``'s structure for
the ``telemetry`` stream's new module. Generic ``stream_partitions.py``
mechanics (``parse_hive_dimensions``, ``assert_partition_bounds``, ...) are
already exhaustively covered there — this module focuses on what is new for
Slice 8.5: the ``telemetry_partitioning.py`` module's existence/boto3-free
status, wiring isolation for its new symbols, and telemetry-specific
partition-key checks.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from codestrata_platform.community_cloud_api.data_lake.stream_partitions import (
    StreamPartitionError,
    assert_partition_dimensions_allowed,
    assert_partition_key_matches_policy,
    assert_s3_metadata_matches_policy,
)
from codestrata_platform.community_cloud_api.data_lake.streams.telemetry_partitioning import (
    default_telemetry_partition_policy,
)

from ._telemetry_partitioning_test_helpers import telemetry_envelope

REPO_ROOT = Path(__file__).resolve().parents[4]
PLATFORM_SRC = REPO_ROOT / "platform" / "src" / "codestrata_platform"
COMMUNITY_CLOUD_API_PKG = PLATFORM_SRC / "community_cloud_api"
DATA_LAKE_PKG = COMMUNITY_CLOUD_API_PKG / "data_lake"

POLICY = default_telemetry_partition_policy()


def _envelope():
    return telemetry_envelope(event_key="event:telemetry-boundary-key")


def _valid_key(envelope) -> str:
    return (
        f"raw/stream=telemetry/schema_version=1.0/"
        f"year={envelope.accepted_year}/month={envelope.accepted_month}/"
        f"day={envelope.accepted_day}/000000000000000000000000.json"
    )


# --- wiring isolation ---


def test_telemetry_partitioning_module_exists_under_data_lake_streams() -> None:
    assert (DATA_LAKE_PKG / "streams" / "telemetry_partitioning.py").is_file()


def test_telemetry_partitioning_module_has_no_boto3_import() -> None:
    path = DATA_LAKE_PKG / "streams" / "telemetry_partitioning.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "boto3" not in node.module, f"{path}: {node.module}"
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "boto3" not in alias.name, f"{path}: {alias.name}"


def test_production_wiring_files_have_no_reference_to_new_slice_8_5_symbols() -> None:
    targets = (
        COMMUNITY_CLOUD_API_PKG / "app.py",
        COMMUNITY_CLOUD_API_PKG / "registry.py",
        COMMUNITY_CLOUD_API_PKG / "deployment" / "wiring.py",
        COMMUNITY_CLOUD_API_PKG / "deployment" / "settings.py",
    )
    forbidden_tokens = (
        "data_lake",
        "telemetry_partitioning",
        "project_telemetry_storage_object",
        "store_projected_telemetry",
        "default_telemetry_partition_policy",
    )
    offenders: list[str] = []
    for target in targets:
        text = target.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            if token in text:
                offenders.append(f"{target.relative_to(REPO_ROOT)}:{token}")
    assert offenders == []


def test_telemetry_endpoint_service_has_no_reference_to_data_lake() -> None:
    telemetry_pkg = COMMUNITY_CLOUD_API_PKG / "telemetry"
    for module_name in ("routes.py", "service.py", "ports.py"):
        text = (telemetry_pkg / module_name).read_text(encoding="utf-8")
        assert "data_lake" not in text, f"{module_name} references data_lake"


# --- telemetry-specific partition-key checks (via the shared stream_partitions helpers) ---


def test_assert_partition_dimensions_allowed_rejects_client_type_extra_dimension() -> None:
    key = (
        "raw/stream=telemetry/schema_version=1.0/year=2026/month=08/day=04/"
        "client_type=codestrata_cli/x.json"
    )
    with pytest.raises(StreamPartitionError):
        assert_partition_dimensions_allowed(key, POLICY)


def test_assert_partition_key_matches_policy_happy_path() -> None:
    envelope = _envelope()
    key = _valid_key(envelope)
    dims = assert_partition_key_matches_policy(key, POLICY, envelope)
    assert dims["stream"] == "telemetry"


def test_assert_partition_key_matches_policy_rejects_quarantine_prefix() -> None:
    envelope = _envelope()
    key = (
        f"quarantine/reason=unsafe_payload/year={envelope.accepted_year}/"
        f"month={envelope.accepted_month}/day={envelope.accepted_day}/x.json"
    )
    with pytest.raises(StreamPartitionError):
        assert_partition_key_matches_policy(key, POLICY, envelope)


def test_assert_partition_key_matches_policy_rejects_stream_mismatch() -> None:
    envelope = _envelope()
    key = (
        f"raw/stream=assessment_metadata/schema_version=1.0/year={envelope.accepted_year}/"
        f"month={envelope.accepted_month}/day={envelope.accepted_day}/x.json"
    )
    with pytest.raises(StreamPartitionError):
        assert_partition_key_matches_policy(key, POLICY, envelope)


def test_assert_partition_key_matches_policy_rejects_event_type_extra_dimension() -> None:
    envelope = _envelope()
    key = (
        f"raw/stream=telemetry/schema_version=1.0/year={envelope.accepted_year}/"
        f"month={envelope.accepted_month}/day={envelope.accepted_day}/"
        f"event_type=application_started/x.json"
    )
    with pytest.raises(StreamPartitionError):
        assert_partition_key_matches_policy(key, POLICY, envelope)


def test_assert_partition_key_matches_policy_rejects_date_mismatch() -> None:
    envelope = _envelope()
    key = "raw/stream=telemetry/schema_version=1.0/year=2020/month=01/day=01/x.json"
    with pytest.raises(StreamPartitionError):
        assert_partition_key_matches_policy(key, POLICY, envelope)


def test_assert_s3_metadata_matches_policy_accepts_client_type_key() -> None:
    assert_s3_metadata_matches_policy(
        {"codestrata-stream": "telemetry", "codestrata-client-type": "codestrata_cli"},
        POLICY,
    )


def test_assert_s3_metadata_matches_policy_rejects_event_type_key() -> None:
    with pytest.raises(StreamPartitionError):
        assert_s3_metadata_matches_policy(
            {"codestrata-telemetry-event-type": "application_started"}, POLICY
        )


def test_assert_s3_metadata_matches_policy_rejects_unlisted_key() -> None:
    with pytest.raises(StreamPartitionError):
        assert_s3_metadata_matches_policy({"codestrata-not-allowlisted": "x"}, POLICY)
