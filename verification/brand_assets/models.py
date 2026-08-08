"""Models for Slice 14.10."""

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
class AssetSizeInventory:
    """Bounded, path-free size inventory grouped by asset category."""

    master_brand_assets: int = 0
    generated_derivatives: int = 0
    packaged_marketplace_assets: int = 0
    master_brand_bytes: int = 0
    generated_derivative_bytes: int = 0
    packaged_marketplace_bytes: int = 0
    archived_legacy_assets: int = 0
    archived_legacy_bytes: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "archived_legacy_assets": self.archived_legacy_assets,
            "archived_legacy_bytes": self.archived_legacy_bytes,
            "generated_derivative_bytes": self.generated_derivative_bytes,
            "generated_derivatives": self.generated_derivatives,
            "master_brand_assets": self.master_brand_assets,
            "master_brand_bytes": self.master_brand_bytes,
            "packaged_marketplace_assets": self.packaged_marketplace_assets,
            "packaged_marketplace_bytes": self.packaged_marketplace_bytes,
        }


@dataclass(slots=True)
class BrandAssetsReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    brand_asset_policy_status: str = "not_executed"
    inventory_status: str = "not_executed"
    authority_status: str = "not_executed"
    master_mark_status: str = "not_executed"
    wordmark_status: str = "not_executed"
    variant_status: str = "not_executed"
    svg_safety_status: str = "not_executed"
    raster_metadata_status: str = "not_executed"
    duplicate_status: str = "not_executed"
    legacy_asset_status: str = "not_executed"
    aimf_status: str = "not_executed"
    cursor_status: str = "not_executed"
    website_consumer_status: str = "not_executed"
    documentation_consumer_status: str = "not_executed"
    assessment_consumer_status: str = "not_executed"
    eir_consumer_status: str = "not_executed"
    vscode_consumer_status: str = "not_executed"
    marketplace_consumer_status: str = "not_executed"
    favicon_status: str = "not_executed"
    icon_language_status: str = "not_executed"
    export_boundary_status: str = "not_executed"
    asset_size_status: str = "not_executed"
    accessibility_baseline_status: str = "not_executed"
    responsive_baseline_status: str = "not_executed"
    ia_boundary_status: str = "not_executed"
    visualization_boundary_status: str = "not_executed"
    deployment_boundary_status: str = "not_executed"
    determinism_status: str = "not_executed"
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    asset_sizes: AssetSizeInventory = field(default_factory=AssetSizeInventory)
    total_checks: int = 0
    failed_checks: int = 0
    release_posture: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "accessibility_baseline_status": self.accessibility_baseline_status,
            "aimf_status": self.aimf_status,
            "asset_size_status": self.asset_size_status,
            "asset_sizes": self.asset_sizes.to_dict(),
            "assessment_consumer_status": self.assessment_consumer_status,
            "authority_status": self.authority_status,
            "blockers": sorted(self.blockers),
            "brand_asset_policy_status": self.brand_asset_policy_status,
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "cursor_status": self.cursor_status,
            "defects": [d.to_dict() for d in self.defects],
            "deployment_boundary_status": self.deployment_boundary_status,
            "determinism_status": self.determinism_status,
            "documentation_consumer_status": self.documentation_consumer_status,
            "duplicate_status": self.duplicate_status,
            "eir_consumer_status": self.eir_consumer_status,
            "export_boundary_status": self.export_boundary_status,
            "failed_checks": self.failed_checks,
            "favicon_status": self.favicon_status,
            "ia_boundary_status": self.ia_boundary_status,
            "icon_language_status": self.icon_language_status,
            "inventory_status": self.inventory_status,
            "legacy_asset_status": self.legacy_asset_status,
            "limitations": sorted(self.limitations),
            "marketplace_consumer_status": self.marketplace_consumer_status,
            "master_mark_status": self.master_mark_status,
            "raster_metadata_status": self.raster_metadata_status,
            "release_posture": dict(sorted(self.release_posture.items())),
            "responsive_baseline_status": self.responsive_baseline_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "svg_safety_status": self.svg_safety_status,
            "total_checks": self.total_checks,
            "variant_status": self.variant_status,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "visualization_boundary_status": self.visualization_boundary_status,
            "vscode_consumer_status": self.vscode_consumer_status,
            "website_consumer_status": self.website_consumer_status,
            "wordmark_status": self.wordmark_status,
        }
