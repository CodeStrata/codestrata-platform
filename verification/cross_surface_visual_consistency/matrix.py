"""Consistency matrix for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add, scan_hex
from verification.cross_surface_visual_consistency.contract import LEGACY_AMBER_HEX
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import (
    CheckResult,
    ConsistencyMatrixCell,
    Defect,
)


def _cell(
    row: str,
    column: str,
    inv: ConsistencyInventory,
) -> ConsistencyMatrixCell:
    """Deterministic matrix fill from inventory signals."""

    col_sources = {
        "docs": inv.docs_theme_tokens + inv.public_tokens,
        "assessment": inv.assessment_styles + inv.assessment_renderer,
        "eir": inv.eir_styles + inv.eir_renderer,
        "vscode": inv.vscode_mapping + inv.vscode_activity_svg,
        "marketplace": inv.marketplace_generator,
        "api_portal": inv.swagger_tokens + inv.swagger_css,
    }
    source = col_sources.get(column, "")

    if row == "identity":
        if column == "vscode":
            return ConsistencyMatrixCell(row, column, "adapted", "native_host")
        if column == "marketplace":
            return ConsistencyMatrixCell(row, column, "adapted", "raster_derivative")
        if column == "api_portal":
            return ConsistencyMatrixCell(row, column, "adapted", "swagger_shell")
        if "codestrata-mark" in source or "CodeStrata" in source:
            return ConsistencyMatrixCell(row, column, "canonical")
        return ConsistencyMatrixCell(row, column, "violation", "identity_missing")

    if row in ("accent", "canvas", "primary_text"):
        if column == "marketplace":
            return ConsistencyMatrixCell(row, column, "adapted", "raster_derivative")
        if scan_hex(source, LEGACY_AMBER_HEX):
            return ConsistencyMatrixCell(row, column, "violation", "amber_present")
        if column == "vscode" and row == "accent":
            return ConsistencyMatrixCell(row, column, "adapted", "currentColor")
        if "--cs-teal" in source or "var(--cs-teal" in source or "#16756a" in source.lower():
            return ConsistencyMatrixCell(row, column, "canonical")
        if column in ("vscode", "marketplace") and row != "accent":
            return ConsistencyMatrixCell(row, column, "not_applicable")
        if "--cs-canvas" in source or "--cs-ink" in source:
            return ConsistencyMatrixCell(row, column, "canonical")
        return ConsistencyMatrixCell(row, column, "adapted")

    if row == "product_bar":
        if column in ("assessment", "eir"):
            ok = "report-product-mark" in source
            return ConsistencyMatrixCell(
                row,
                column,
                "canonical" if ok else "violation",
                "mark_present" if ok else "mark_missing",
            )
        if column in ("docs", "vscode", "marketplace", "api_portal"):
            return ConsistencyMatrixCell(row, column, "not_applicable")
        return ConsistencyMatrixCell(row, column, "not_applicable")

    if row in ("evidence", "risk"):
        if column == "eir" and row == "evidence":
            return ConsistencyMatrixCell(row, column, "not_applicable")
        if column in ("assessment", "eir"):
            return ConsistencyMatrixCell(row, column, "canonical")
        if column == "docs" and row == "evidence":
            return ConsistencyMatrixCell(row, column, "adapted", "code_blocks")
        return ConsistencyMatrixCell(row, column, "not_applicable")

    if row in ("navigation", "responsive", "accessibility"):
        if column in ("assessment", "eir", "docs"):
            return ConsistencyMatrixCell(row, column, "canonical")
        if column == "vscode":
            return ConsistencyMatrixCell(row, column, "adapted", "native_host")
        return ConsistencyMatrixCell(row, column, "not_applicable")

    if column == "vscode":
        return ConsistencyMatrixCell(row, column, "adapted", "native_host")
    if column == "marketplace":
        return ConsistencyMatrixCell(row, column, "adapted", "raster")
    if column == "api_portal":
        return ConsistencyMatrixCell(row, column, "adapted", "swagger_bridge")

    if "--cs-" in source or "var(--cs-" in source:
        return ConsistencyMatrixCell(row, column, "canonical")
    return ConsistencyMatrixCell(row, column, "adapted")


def build_matrix(inv: ConsistencyInventory) -> list[ConsistencyMatrixCell]:
    contract = inv.consistency_contract
    rows = contract.get("matrix", {}).get("rows") or []
    columns = contract.get("matrix", {}).get("columns") or []
    return [_cell(row, column, inv) for row in rows for column in columns]


def check_matrix(
    inv: ConsistencyInventory,
) -> tuple[list[CheckResult], list[ConsistencyMatrixCell], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    matrix = build_matrix(inv)
    violations = [c for c in matrix if c.value == "violation"]

    add(
        checks,
        "matrix:built",
        len(matrix) > 0,
        f"{len(matrix)}_cells",
        "matrix",
    )
    add(
        checks,
        "matrix:no_violations",
        not violations,
        "clean" if not violations else f"{len(violations)}_violations",
        "matrix",
    )
    if violations:
        for cell in violations[:5]:
            defects.append(
                Defect(
                    "matrix_violation",
                    f"{cell.row}/{cell.column}:{cell.detail or cell.value}",
                )
            )
    return checks, matrix, defects
