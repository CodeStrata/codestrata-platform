"""Determinism checks for Slice 14.13."""

from __future__ import annotations

import json

from verification.cross_surface_visual_consistency._helpers import add
from verification.cross_surface_visual_consistency.inventory import (
    ConsistencyInventory,
    build_inventory,
)
from verification.cross_surface_visual_consistency.matrix import build_matrix
from verification.cross_surface_visual_consistency.models import CheckResult


def check_determinism(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    inv_b = build_inventory(inv.monorepo, build_docs=False)
    matrix_a = [c.to_dict() for c in build_matrix(inv)]
    matrix_b = [c.to_dict() for c in build_matrix(inv_b)]
    text_a = json.dumps(matrix_a, sort_keys=True)
    text_b = json.dumps(matrix_b, sort_keys=True)

    add(
        checks,
        "determinism:matrix_stable",
        text_a == text_b,
        "stable",
        "determinism",
    )
    add(
        checks,
        "determinism:inventory_rebuild",
        bool(inv_b.policy) and bool(inv_b.consistency_contract),
        "rebuilt",
        "determinism",
    )
    add(
        checks,
        "determinism:no_render_clock_dependency",
        "datetime" not in inv.assessment_renderer,
        "no_clock",
        "determinism",
    )
    return checks
