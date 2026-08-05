"""Determinism checks for completion verification (Slice 8.15)."""

from __future__ import annotations

from verification.community_data_lake_completion.inventory import build_package_inventory
from verification.community_data_lake_completion.models import CheckResult
from verification.community_data_lake_completion.scenarios import (
    build_quarantine_matrix,
    build_stream_matrix,
)
from verification.community_data_lake_completion.versions import (
    build_product_contract_versions,
    build_verification_contract_versions,
)


def check_determinism() -> list[CheckResult]:
    inventory_a = build_package_inventory()
    inventory_b = build_package_inventory()
    stream_a = build_stream_matrix()
    stream_b = build_stream_matrix()
    quarantine_a = build_quarantine_matrix()
    quarantine_b = build_quarantine_matrix()
    product_a = build_product_contract_versions()
    product_b = build_product_contract_versions()
    verification_a = build_verification_contract_versions()
    verification_b = build_verification_contract_versions()

    return [
        CheckResult(
            name="determinism:inventory_stable",
            ok=inventory_a == inventory_b,
            detail=f"count={len(inventory_a)}",
            category="determinism",
        ),
        CheckResult(
            name="determinism:stream_matrix_stable",
            ok=stream_a == stream_b,
            detail=f"rows={len(stream_a)}",
            category="determinism",
        ),
        CheckResult(
            name="determinism:quarantine_matrix_stable",
            ok=quarantine_a == quarantine_b,
            detail="stable",
            category="determinism",
        ),
        CheckResult(
            name="determinism:product_versions_stable",
            ok=product_a == product_b,
            detail=f"keys={len(product_a)}",
            category="determinism",
        ),
        CheckResult(
            name="determinism:verification_versions_stable",
            ok=verification_a == verification_b,
            detail=f"keys={len(verification_a)}",
            category="determinism",
        ),
    ]


__all__ = ["check_determinism"]
