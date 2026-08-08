"""Models for Slice 14.6 verification reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
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
class MarketplaceVisualAssetsReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    visual_policy_status: str = "not_executed"
    design_system_status: str = "not_executed"
    icon_status: str = "not_executed"
    gallery_banner_status: str = "not_executed"
    screenshot_manifest_status: str = "not_executed"
    screenshot_dimension_status: str = "not_executed"
    screenshot_safety_status: str = "not_executed"
    screenshot_metadata_status: str = "not_executed"
    screenshot_content_status: str = "not_executed"
    gallery_order_status: str = "not_executed"
    caption_status: str = "not_executed"
    alt_text_status: str = "not_executed"
    legacy_asset_status: str = "not_executed"
    cursor_absence_status: str = "not_executed"
    commercial_boundary_status: str = "not_executed"
    package_inventory_status: str = "not_executed"
    asset_size_status: str = "not_executed"
    readme_reference_status: str = "not_executed"
    vscode_visual_boundary_status: str = "not_executed"
    logo_boundary_status: str = "not_executed"
    accessibility_status: str = "not_executed"
    vscode_regression_status: str = "not_executed"
    determinism_status: str = "not_executed"
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0
    release_posture: dict[str, bool] = field(default_factory=dict)
    asset_size_summary: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "accessibility_status": self.accessibility_status,
            "alt_text_status": self.alt_text_status,
            "asset_size_status": self.asset_size_status,
            "asset_size_summary": self.asset_size_summary,
            "blockers": sorted(self.blockers),
            "caption_status": self.caption_status,
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "commercial_boundary_status": self.commercial_boundary_status,
            "cursor_absence_status": self.cursor_absence_status,
            "defects": [d.to_dict() for d in self.defects],
            "design_system_status": self.design_system_status,
            "determinism_status": self.determinism_status,
            "failed_checks": self.failed_checks,
            "gallery_banner_status": self.gallery_banner_status,
            "gallery_order_status": self.gallery_order_status,
            "icon_status": self.icon_status,
            "legacy_asset_status": self.legacy_asset_status,
            "limitations": sorted(self.limitations),
            "logo_boundary_status": self.logo_boundary_status,
            "package_inventory_status": self.package_inventory_status,
            "readme_reference_status": self.readme_reference_status,
            "release_posture": dict(sorted(self.release_posture.items())),
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "screenshot_content_status": self.screenshot_content_status,
            "screenshot_dimension_status": self.screenshot_dimension_status,
            "screenshot_manifest_status": self.screenshot_manifest_status,
            "screenshot_metadata_status": self.screenshot_metadata_status,
            "screenshot_safety_status": self.screenshot_safety_status,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "visual_policy_status": self.visual_policy_status,
            "vscode_regression_status": self.vscode_regression_status,
            "vscode_visual_boundary_status": self.vscode_visual_boundary_status,
        }
