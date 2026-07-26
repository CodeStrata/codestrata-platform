"""Report contract identifier remapping tests (Phase 5.15)."""

from __future__ import annotations

from codestrata.reporting.contract.identifiers import remap_related_finding_ids


def test_remap_related_finding_ids_keeps_known_and_drops_unknown() -> None:
    id_map = {
        "runtime-a": "stable-a",
        "runtime-b": "stable-b",
    }
    assert remap_related_finding_ids(
        ["runtime-b", "SEC001", "runtime-a", "runtime-b"],
        id_map,
    ) == ("stable-a", "stable-b")
    assert remap_related_finding_ids(["SEC001"], id_map) == ()
    assert remap_related_finding_ids([], id_map) == ()
