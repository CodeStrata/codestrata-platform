"""Prefix and namespace isolation integration tests (Slice 8.14)."""

from __future__ import annotations

from verification.community_data_lake.contract import ACCEPTED_STREAMS
from verification.community_data_lake.inputs import project_all_streams, project_quarantine_object


def test_prefix_and_namespace_isolation() -> None:
    for stream, obj in project_all_streams().items():
        assert obj.object_key.startswith(f"raw/stream={stream}/")
        assert "event:" not in obj.object_key
        assert "evt-" not in obj.object_key
    quarantine = project_quarantine_object()
    assert quarantine.object_key.startswith("quarantine/")
    assert not quarantine.object_key.startswith("raw/")
    assert len(ACCEPTED_STREAMS) == 5
