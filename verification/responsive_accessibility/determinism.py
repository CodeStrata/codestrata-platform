"""Renderer determinism checks."""

from __future__ import annotations

from verification.responsive_accessibility.inventory import (
    SurfaceInventory,
    _render_assessment,
    _render_eir,
)
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "determinism"


def check_determinism(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    errors: list[str] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    full_a, partial_a = _render_assessment(inv.monorepo, errors)
    full_b, partial_b = _render_assessment(inv.monorepo, errors)
    add(
        "determinism:assessment_full",
        bool(full_a) and full_a == full_b,
        "identical" if full_a == full_b else "divergent",
    )
    add(
        "determinism:assessment_partial",
        bool(partial_a) and partial_a == partial_b,
        "identical" if partial_a == partial_b else "divergent",
    )

    populated_a, empty_a = _render_eir(inv.monorepo, errors)
    populated_b, empty_b = _render_eir(inv.monorepo, errors)
    add(
        "determinism:eir_populated",
        bool(populated_a) and populated_a == populated_b,
        "identical" if populated_a == populated_b else "divergent",
    )
    add(
        "determinism:eir_empty",
        bool(empty_a) and empty_a == empty_b,
        "identical" if empty_a == empty_b else "divergent",
    )
    add(
        "determinism:no_render_errors",
        not errors,
        ",".join(errors) or "ok",
    )

    if any(not c.ok for c in checks):
        defects.append(Defect("determinism", "report rendering is not deterministic"))
    return checks, defects
