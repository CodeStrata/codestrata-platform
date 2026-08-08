"""Surface inventory classification for Slice 14.5."""

from __future__ import annotations

SURFACE_CLASSIFICATION: dict[str, str] = {
    "package_displayName": "codestrata_brand_surface",
    "command_titles": "wording_surface",
    "command_ids": "runtime_behavior_must_not_change",
    "activity_svg": "icon_surface",
    "status_bar": "status_surface",
    "progress_messages": "progress_surface",
    "notifications": "wording_surface",
    "first_run": "onboarding_surface",
    "recovery_catalog": "recovery_surface",
    "report_ready_prompt": "report_surface",
    "settings_titles": "settings_surface",
    "output_channel": "output_surface",
    "theme_colors": "theme_controlled_by_vscode",
    "design_system_mapping": "design_system_consumer",
    "marketplace_pngs": "marketplace_only_deferred_14_6",
    "amber_activity_fills": "legacy_visual_style",
    "cursor_product": "stale_cursor_surface",
}


def inventory_summary() -> dict[str, int]:
    counts: dict[str, int] = {}
    for label in SURFACE_CLASSIFICATION.values():
        counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items()))
