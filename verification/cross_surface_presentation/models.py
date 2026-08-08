"""Models for Slice 14.7."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Verdict = Literal["PASS", "PASS_WITH_LIMITATIONS", "FAIL"]


@dataclass(slots=True)
class CheckResult:
    name: str
    ok: bool
    detail: str
    category: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "detail": self.detail,
            "name": self.name,
            "ok": self.ok,
        }


@dataclass(slots=True)
class Defect:
    classification: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {"classification": self.classification, "summary": self.summary}


@dataclass(slots=True)
class CrossSurfacePresentationReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    visual_policy_status: str = "not_executed"
    token_authority_status: str = "not_executed"
    typography_status: str = "not_executed"
    typography_delivery_status: str = "not_executed"
    colors_status: str = "not_executed"
    surfaces_status: str = "not_executed"
    spacing_status: str = "not_executed"
    radii_status: str = "not_executed"
    borders_status: str = "not_executed"
    shadows_status: str = "not_executed"
    layouts_status: str = "not_executed"
    components_status: str = "not_executed"
    cards_status: str = "not_executed"
    tables_status: str = "not_executed"
    code_evidence_status: str = "not_executed"
    callouts_status: str = "not_executed"
    actions_status: str = "not_executed"
    docs_consumer_status: str = "not_executed"
    assessment_consumer_status: str = "not_executed"
    eir_consumer_status: str = "not_executed"
    vscode_consumer_status: str = "not_executed"
    marketplace_consumer_status: str = "not_executed"
    legacy_status: str = "not_executed"
    duplication_status: str = "not_executed"
    chart_boundary_status: str = "not_executed"
    navigation_boundary_status: str = "not_executed"
    asset_boundary_status: str = "not_executed"
    accessibility_boundary_status: str = "not_executed"
    determinism_status: str = "not_executed"
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0
    release_posture: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "accessibility_boundary_status": self.accessibility_boundary_status,
            "actions_status": self.actions_status,
            "assessment_consumer_status": self.assessment_consumer_status,
            "asset_boundary_status": self.asset_boundary_status,
            "blockers": sorted(self.blockers),
            "borders_status": self.borders_status,
            "callouts_status": self.callouts_status,
            "cards_status": self.cards_status,
            "chart_boundary_status": self.chart_boundary_status,
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "code_evidence_status": self.code_evidence_status,
            "colors_status": self.colors_status,
            "components_status": self.components_status,
            "defects": [d.to_dict() for d in self.defects],
            "determinism_status": self.determinism_status,
            "docs_consumer_status": self.docs_consumer_status,
            "duplication_status": self.duplication_status,
            "eir_consumer_status": self.eir_consumer_status,
            "failed_checks": self.failed_checks,
            "layouts_status": self.layouts_status,
            "legacy_status": self.legacy_status,
            "limitations": sorted(self.limitations),
            "marketplace_consumer_status": self.marketplace_consumer_status,
            "navigation_boundary_status": self.navigation_boundary_status,
            "radii_status": self.radii_status,
            "release_posture": dict(sorted(self.release_posture.items())),
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "shadows_status": self.shadows_status,
            "spacing_status": self.spacing_status,
            "surfaces_status": self.surfaces_status,
            "tables_status": self.tables_status,
            "token_authority_status": self.token_authority_status,
            "total_checks": self.total_checks,
            "typography_delivery_status": self.typography_delivery_status,
            "typography_status": self.typography_status,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "visual_policy_status": self.visual_policy_status,
            "vscode_consumer_status": self.vscode_consumer_status,
        }
