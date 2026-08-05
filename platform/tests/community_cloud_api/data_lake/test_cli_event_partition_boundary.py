"""Slice 8.6 boundary tests: wiring isolation + low-level partition-vs-policy checks.

Mirrors ``test_telemetry_partition_boundary.py``'s structure for the
``cli_event`` stream's new module. Generic ``stream_partitions.py``
mechanics (``parse_hive_dimensions``, ``assert_partition_bounds``, ...) are
already exhaustively covered by
``test_assessment_metadata_partition_boundary.py`` — this module focuses on
what is new for Slice 8.6: the ``cli_event_partitioning.py`` module's
existence/boto3-free status, wiring isolation for its new symbols
(including in ``app.py``, the CLI emitter, and the telemetry runtime), and
CLI-event-specific partition-key checks.
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
from codestrata_platform.community_cloud_api.data_lake.streams.cli_event_partitioning import (
    default_cli_event_partition_policy,
)

from ._cli_event_partitioning_test_helpers import cli_event_envelope

REPO_ROOT = Path(__file__).resolve().parents[4]
PLATFORM_SRC = REPO_ROOT / "platform" / "src" / "codestrata_platform"
COMMUNITY_CLOUD_API_PKG = PLATFORM_SRC / "community_cloud_api"
DATA_LAKE_PKG = COMMUNITY_CLOUD_API_PKG / "data_lake"
ENGINE_SRC = REPO_ROOT / "engine" / "src" / "codestrata"

POLICY = default_cli_event_partition_policy()


def _envelope():
    return cli_event_envelope(event_key="event:cli-event-boundary-key")


def _valid_key(envelope) -> str:
    return (
        f"raw/stream=cli_event/schema_version=1.0/"
        f"year={envelope.accepted_year}/month={envelope.accepted_month}/"
        f"day={envelope.accepted_day}/000000000000000000000000.json"
    )


# --- wiring isolation ---


def test_cli_event_partitioning_module_exists_under_data_lake_streams() -> None:
    assert (DATA_LAKE_PKG / "streams" / "cli_event_partitioning.py").is_file()


def test_cli_event_partitioning_module_has_no_boto3_import() -> None:
    path = DATA_LAKE_PKG / "streams" / "cli_event_partitioning.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "boto3" not in node.module, f"{path}: {node.module}"
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "boto3" not in alias.name, f"{path}: {alias.name}"


def test_production_wiring_files_have_no_reference_to_new_slice_8_6_symbols() -> None:
    targets = (
        COMMUNITY_CLOUD_API_PKG / "app.py",
        COMMUNITY_CLOUD_API_PKG / "registry.py",
        COMMUNITY_CLOUD_API_PKG / "deployment" / "wiring.py",
        COMMUNITY_CLOUD_API_PKG / "deployment" / "settings.py",
    )
    forbidden_tokens = (
        "data_lake",
        "cli_event_partitioning",
        "project_cli_event_storage_object",
        "store_projected_cli_event",
        "default_cli_event_partition_policy",
    )
    offenders: list[str] = []
    for target in targets:
        text = target.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            if token in text:
                offenders.append(f"{target.relative_to(REPO_ROOT)}:{token}")
    assert offenders == []


def test_cli_event_endpoint_service_has_no_reference_to_data_lake() -> None:
    cli_events_pkg = COMMUNITY_CLOUD_API_PKG / "cli_events"
    for module_name in ("routes.py", "service.py", "ports.py"):
        text = (cli_events_pkg / module_name).read_text(encoding="utf-8")
        assert "data_lake" not in text, f"{module_name} references data_lake"


def test_telemetry_runtime_has_no_reference_to_cli_event_partitioning() -> None:
    telemetry_pkg = COMMUNITY_CLOUD_API_PKG / "telemetry"
    for module_name in ("routes.py", "service.py", "ports.py"):
        text = (telemetry_pkg / module_name).read_text(encoding="utf-8")
        assert "cli_event_partitioning" not in text
        assert "project_cli_event_storage_object" not in text


def test_engine_package_has_no_reference_to_cli_event_partitioning() -> None:
    if not ENGINE_SRC.is_dir():  # pragma: no cover - defensive, engine always present
        return
    offenders: list[str] = []
    for path in ENGINE_SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "cli_event_partitioning" in text or "project_cli_event_storage_object" in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == []


def test_s3_store_still_exposes_no_forbidden_adapter_methods() -> None:
    from codestrata_platform.community_cloud_api.data_lake.infrastructure.s3_store import (
        CommunityDataLakeS3Store,
    )

    for forbidden in ("delete_object", "delete", "update", "list_objects", "list", "copy_object"):
        assert not hasattr(CommunityDataLakeS3Store, forbidden)
    assert hasattr(CommunityDataLakeS3Store, "put_immutable_event")
    assert hasattr(CommunityDataLakeS3Store, "put_immutable_storage_object")
    assert hasattr(CommunityDataLakeS3Store, "quarantine_event")


# --- cli-event-specific partition-key checks (via the shared stream_partitions helpers) ---


def test_assert_partition_dimensions_allowed_rejects_operation_extra_dimension() -> None:
    key = (
        "raw/stream=cli_event/schema_version=1.0/year=2026/month=08/day=04/"
        "operation=assess/x.json"
    )
    with pytest.raises(StreamPartitionError):
        assert_partition_dimensions_allowed(key, POLICY)


def test_assert_partition_dimensions_allowed_rejects_client_type_extra_dimension() -> None:
    key = (
        "raw/stream=cli_event/schema_version=1.0/year=2026/month=08/day=04/"
        "client_type=codestrata_cli/x.json"
    )
    with pytest.raises(StreamPartitionError):
        assert_partition_dimensions_allowed(key, POLICY)


def test_assert_partition_key_matches_policy_happy_path() -> None:
    envelope = _envelope()
    key = _valid_key(envelope)
    dims = assert_partition_key_matches_policy(key, POLICY, envelope)
    assert dims["stream"] == "cli_event"


def test_assert_partition_key_matches_policy_rejects_quarantine_prefix() -> None:
    envelope = _envelope()
    key = (
        f"quarantine/reason=unsafe_payload/year={envelope.accepted_year}/"
        f"month={envelope.accepted_month}/day={envelope.accepted_day}/x.json"
    )
    with pytest.raises(StreamPartitionError):
        assert_partition_key_matches_policy(key, POLICY, envelope)


def test_assert_partition_key_matches_policy_rejects_telemetry_stream_mismatch() -> None:
    envelope = _envelope()
    key = (
        f"raw/stream=telemetry/schema_version=1.0/year={envelope.accepted_year}/"
        f"month={envelope.accepted_month}/day={envelope.accepted_day}/x.json"
    )
    with pytest.raises(StreamPartitionError):
        assert_partition_key_matches_policy(key, POLICY, envelope)


def test_assert_partition_key_matches_policy_rejects_assessment_metadata_stream_mismatch() -> None:
    envelope = _envelope()
    key = (
        f"raw/stream=assessment_metadata/schema_version=1.0/year={envelope.accepted_year}/"
        f"month={envelope.accepted_month}/day={envelope.accepted_day}/x.json"
    )
    with pytest.raises(StreamPartitionError):
        assert_partition_key_matches_policy(key, POLICY, envelope)


def test_assert_partition_key_matches_policy_rejects_operation_extra_dimension() -> None:
    envelope = _envelope()
    key = (
        f"raw/stream=cli_event/schema_version=1.0/year={envelope.accepted_year}/"
        f"month={envelope.accepted_month}/day={envelope.accepted_day}/"
        f"operation=assess/x.json"
    )
    with pytest.raises(StreamPartitionError):
        assert_partition_key_matches_policy(key, POLICY, envelope)


def test_assert_partition_key_matches_policy_rejects_date_mismatch() -> None:
    envelope = _envelope()
    key = "raw/stream=cli_event/schema_version=1.0/year=2020/month=01/day=01/x.json"
    with pytest.raises(StreamPartitionError):
        assert_partition_key_matches_policy(key, POLICY, envelope)


def test_assert_s3_metadata_matches_policy_accepts_the_five_base_keys() -> None:
    assert_s3_metadata_matches_policy(
        {
            "codestrata-stream": "cli_event",
            "codestrata-content-sha256": "sha256:" + "0" * 64,
            "codestrata-envelope-schema": "1.0",
            "codestrata-source-schema": "1.0",
            "codestrata-object-id": "0" * 24,
        },
        POLICY,
    )


def test_assert_s3_metadata_matches_policy_rejects_client_type_key() -> None:
    with pytest.raises(StreamPartitionError):
        assert_s3_metadata_matches_policy(
            {"codestrata-client-type": "codestrata_cli"}, POLICY
        )


def test_assert_s3_metadata_matches_policy_rejects_assessment_schema_key() -> None:
    with pytest.raises(StreamPartitionError):
        assert_s3_metadata_matches_policy({"codestrata-assessment-schema": "1.2"}, POLICY)


def test_assert_s3_metadata_matches_policy_rejects_unlisted_key() -> None:
    with pytest.raises(StreamPartitionError):
        assert_s3_metadata_matches_policy({"codestrata-not-allowlisted": "x"}, POLICY)
