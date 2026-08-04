"""Aggregation determinism (delegates to shared EI pipeline order checks)."""

from __future__ import annotations

from verification.deterministic_outputs.intelligence_dataset import (
    check_intelligence_pipeline_order,
)


def check_aggregation(monorepo):
    checks, defects = check_intelligence_pipeline_order(monorepo)
    filtered = [
        c
        for c in checks
        if c.name.startswith("ei_order_invariant_") or c.name == "ei_population_22"
    ]
    return filtered, defects
