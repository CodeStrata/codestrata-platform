"""Models for Slice 14.11."""

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

    def to_dict(self) -> dict[str, str]:
        return {"classification": self.classification, "summary": self.summary}


@dataclass(slots=True)
class ContrastMeasurement:
    """A single measured pair. Token names only — no surface paths."""

    pair_id: str
    theme: str
    kind: str
    ratio: float
    required: float

    @property
    def ok(self) -> bool:
        return self.ratio >= self.required

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "ok": self.ok,
            "pair_id": self.pair_id,
            "ratio": round(self.ratio, 2),
            "required": self.required,
            "theme": self.theme,
        }


@dataclass(slots=True)
class ViewportOutcome:
    """Per-viewport overflow outcome for one surface."""

    surface: str
    width_px: int
    page_overflow: bool
    measured_in_browser: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "measured_in_browser": self.measured_in_browser,
            "page_overflow": self.page_overflow,
            "surface": self.surface,
            "width_px": self.width_px,
        }


@dataclass(slots=True)
class ResponsiveAccessibilityReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    accessibility_policy_status: str = "not_executed"
    contrast_status: str = "not_executed"
    typography_status: str = "not_executed"
    zoom_status: str = "not_executed"
    keyboard_status: str = "not_executed"
    focus_status: str = "not_executed"
    heading_status: str = "not_executed"
    landmark_status: str = "not_executed"
    skip_link_status: str = "not_executed"
    table_status: str = "not_executed"
    link_status: str = "not_executed"
    image_alt_status: str = "not_executed"
    brand_asset_status: str = "not_executed"
    status_visualization_status: str = "not_executed"
    code_evidence_status: str = "not_executed"
    responsive_viewport_status: str = "not_executed"
    documentation_responsive_status: str = "not_executed"
    assessment_responsive_status: str = "not_executed"
    eir_responsive_status: str = "not_executed"
    vscode_boundary_status: str = "not_executed"
    marketplace_status: str = "not_executed"
    touch_target_status: str = "not_executed"
    reduced_motion_status: str = "not_executed"
    forced_colors_status: str = "not_executed"
    dark_theme_status: str = "not_executed"
    print_status: str = "not_executed"
    html_language_status: str = "not_executed"
    aria_status: str = "not_executed"
    browser_validation_status: str = "not_executed"
    screen_reader_boundary_status: str = "not_executed"
    deployment_boundary_status: str = "not_executed"
    consistency_boundary_status: str = "not_executed"
    determinism_status: str = "not_executed"
    wcag_posture: dict[str, Any] = field(default_factory=dict)
    contrast_measurements: list[ContrastMeasurement] = field(default_factory=list)
    viewport_matrix: list[ViewportOutcome] = field(default_factory=list)
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0
    release_posture: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "accessibility_policy_status": self.accessibility_policy_status,
            "aria_status": self.aria_status,
            "assessment_responsive_status": self.assessment_responsive_status,
            "blockers": sorted(self.blockers),
            "brand_asset_status": self.brand_asset_status,
            "browser_validation_status": self.browser_validation_status,
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "code_evidence_status": self.code_evidence_status,
            "consistency_boundary_status": self.consistency_boundary_status,
            "contrast_measurements": [
                m.to_dict()
                for m in sorted(self.contrast_measurements, key=lambda x: (x.theme, x.pair_id))
            ],
            "contrast_status": self.contrast_status,
            "dark_theme_status": self.dark_theme_status,
            "defects": [d.to_dict() for d in self.defects],
            "deployment_boundary_status": self.deployment_boundary_status,
            "determinism_status": self.determinism_status,
            "documentation_responsive_status": self.documentation_responsive_status,
            "eir_responsive_status": self.eir_responsive_status,
            "failed_checks": self.failed_checks,
            "focus_status": self.focus_status,
            "forced_colors_status": self.forced_colors_status,
            "heading_status": self.heading_status,
            "html_language_status": self.html_language_status,
            "image_alt_status": self.image_alt_status,
            "keyboard_status": self.keyboard_status,
            "landmark_status": self.landmark_status,
            "limitations": sorted(self.limitations),
            "link_status": self.link_status,
            "marketplace_status": self.marketplace_status,
            "print_status": self.print_status,
            "reduced_motion_status": self.reduced_motion_status,
            "release_posture": dict(sorted(self.release_posture.items())),
            "responsive_viewport_status": self.responsive_viewport_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "screen_reader_boundary_status": self.screen_reader_boundary_status,
            "skip_link_status": self.skip_link_status,
            "status_visualization_status": self.status_visualization_status,
            "table_status": self.table_status,
            "total_checks": self.total_checks,
            "touch_target_status": self.touch_target_status,
            "typography_status": self.typography_status,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "viewport_matrix": [
                v.to_dict()
                for v in sorted(self.viewport_matrix, key=lambda x: (x.surface, x.width_px))
            ],
            "vscode_boundary_status": self.vscode_boundary_status,
            "wcag_posture": dict(sorted(self.wcag_posture.items())),
            "zoom_status": self.zoom_status,
        }
