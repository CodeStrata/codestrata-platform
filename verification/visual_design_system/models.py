"""Models for Slice 14.1 verification."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Verdict = Literal["PASS", "PASS_WITH_LIMITATIONS", "FAIL"]


@dataclass(frozen=True, slots=True)
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


@dataclass(frozen=True, slots=True)
class Defect:
    classification: str
    surface: str
    expected: str
    observed: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VisualDesignSystemReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    epic: str = "14"
    slice: str = "14.1"
    design_system_version: str = "1.0.0"
    design_system_policy: str = "codestrata-design-system-policy:1.0"
    visual_language_policy: str = "codestrata-visual-language-policy:1.0"
    website_authority: str = "https://codestrata.ai"
    capture_date: str = "2026-08-07"
    tokens_status: str = "not_executed"
    colors_status: str = "not_executed"
    typography_status: str = "not_executed"
    spacing_status: str = "not_executed"
    components_status: str = "not_executed"
    report_language_status: str = "not_executed"
    documentation_language_status: str = "not_executed"
    vscode_language_status: str = "not_executed"
    marketplace_language_status: str = "not_executed"
    accessibility_status: str = "not_executed"
    responsive_status: str = "not_executed"
    no_redesign_status: str = "not_executed"
    slice_14_2_absence_status: str = "not_executed"
    release_posture: dict[str, Any] = field(default_factory=dict)
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "accessibility_status": self.accessibility_status,
            "blockers": list(self.blockers),
            "capture_date": self.capture_date,
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "colors_status": self.colors_status,
            "components_status": self.components_status,
            "defects": [d.to_dict() for d in self.defects],
            "design_system_policy": self.design_system_policy,
            "design_system_version": self.design_system_version,
            "documentation_language_status": self.documentation_language_status,
            "epic": self.epic,
            "failed_checks": self.failed_checks,
            "limitations": sorted(self.limitations),
            "marketplace_language_status": self.marketplace_language_status,
            "no_redesign_status": self.no_redesign_status,
            "release_posture": dict(sorted(self.release_posture.items())),
            "report_language_status": self.report_language_status,
            "responsive_status": self.responsive_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "slice": self.slice,
            "slice_14_2_absence_status": self.slice_14_2_absence_status,
            "spacing_status": self.spacing_status,
            "tokens_status": self.tokens_status,
            "total_checks": self.total_checks,
            "typography_status": self.typography_status,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "visual_language_policy": self.visual_language_policy,
            "vscode_language_status": self.vscode_language_status,
            "website_authority": self.website_authority,
        }
