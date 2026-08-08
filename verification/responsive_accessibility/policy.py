"""Policy and design-system contract validation for Slice 14.11."""

from __future__ import annotations

from verification.responsive_accessibility.contract import (
    ACCESSIBILITY_CONTRACT_ID,
    CONTRACT_VERSION,
    POLICY_ID,
    POLICY_VERSION,
    RESPONSIVE_CONTRACT_ID,
    VIEWPORT_MATRIX_PX,
    ALLOWED_LIMITATIONS,
)
from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect


def check_policy(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = inv.policy

    def add(name: str, ok: bool, detail: str, category: str = "accessibility_policy") -> None:
        checks.append(CheckResult(name, ok, detail, category))

    add(
        "policy:id_version",
        policy.get("policy_id") == POLICY_ID
        and policy.get("policy_version") == POLICY_VERSION,
        f"{POLICY_ID}:{POLICY_VERSION}",
    )
    add("policy:slice", policy.get("slice") == "14.11", str(policy.get("slice")))
    add(
        "policy:wcag_target",
        policy.get("wcag_target") == "2.2_AA_oriented",
        str(policy.get("wcag_target")),
    )
    add(
        "policy:no_certification_claim",
        policy.get("formal_certification_claimed") is False
        and policy.get("automated_tooling_not_equivalent_to_certification") is True,
        "not_certified",
    )
    add(
        "policy:certification_language_present",
        "not a substitute for formal accessibility certification"
        in policy.get("certification_language", ""),
        "language",
    )

    for flag in (
        "keyboard_access_required",
        "visible_focus_required",
        "semantic_heading_required",
        "landmarks_required",
        "skip_navigation_required_for_long_documents",
        "accessible_tables_required",
        "image_alt_contract_required",
        "decorative_asset_hidden_required",
        "reduced_motion_required",
        "text_zoom_required",
        "responsive_mobile_required",
        "responsive_table_overflow_required",
        "responsive_code_overflow_required",
        "print_readability_required",
        "native_vscode_host_exception_allowed",
        "forced_colors_baseline_required",
        "dark_theme_contrast_required",
        "scrollable_region_keyboard_reachable_required",
        "table_header_scope_required",
        "skip_link_target_must_exist",
        "unique_banner_landmark_required",
        "root_font_size_must_respect_user_preference",
    ):
        add(f"policy:flag:{flag}", policy.get(flag) is True, "true")

    for flag in (
        "color_only_meaning_allowed",
        "aria_on_generic_role_allowed",
        "page_level_horizontal_overflow_allowed",
    ):
        add(f"policy:flag_false:{flag}", policy.get(flag) is False, "false")

    add(
        "policy:min_viewport",
        policy.get("min_viewport_px") == 320,
        str(policy.get("min_viewport_px")),
    )
    add(
        "policy:touch_target",
        policy.get("touch_target_min_px") == 44
        and policy.get("compact_control_min_px") == 34,
        "44/34",
    )
    targets = policy.get("contrast_targets", {})
    add(
        "policy:contrast_targets",
        targets.get("normal_text") == 4.5
        and targets.get("large_text") == 3.0
        and targets.get("non_text_essential") == 3.0,
        "4.5/3.0/3.0",
    )
    add(
        "policy:prohibits_forward_slice",
        policy.get("prohibited", {}).get("start_slice_15_7") is True,
        "14_13_prohibited",
    )
    add(
        "policy:limitations_declared",
        set(policy.get("limitations", [])) == set(ALLOWED_LIMITATIONS),
        f"{len(policy.get('limitations', []))}",
    )
    expected = policy.get("expected_unchanged", {})
    add(
        "policy:expected_unchanged",
        expected.get("design_system_version") == "1.0"
        and expected.get("assessment_schema_version") == "1.2"
        and expected.get("extension_version") == "0.2.0",
        "unchanged",
    )
    if policy.get("policy_id") != POLICY_ID:
        defects.append(Defect("harness/tooling", "accessibility policy missing or misidentified"))

    return checks, defects


def check_design_system_contract(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    accessibility = inv.accessibility_contract
    responsive = inv.responsive_contract

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, "design_system_contract"))

    add(
        "contract:accessibility_identity",
        accessibility.get("contract_id") == ACCESSIBILITY_CONTRACT_ID
        and accessibility.get("contract_version") == CONTRACT_VERSION
        and accessibility.get("schema_version") == "1.0.0",
        f"{ACCESSIBILITY_CONTRACT_ID}:{CONTRACT_VERSION}",
    )
    add(
        "contract:responsive_identity",
        responsive.get("contract_id") == RESPONSIVE_CONTRACT_ID
        and responsive.get("contract_version") == CONTRACT_VERSION
        and responsive.get("schema_version") == "1.0.0",
        f"{RESPONSIVE_CONTRACT_ID}:{CONTRACT_VERSION}",
    )
    add(
        "contract:policy_backreference",
        accessibility.get("policy") == f"{POLICY_ID}:{POLICY_VERSION}"
        and responsive.get("policy") == f"{POLICY_ID}:{POLICY_VERSION}",
        "linked",
    )
    add(
        "contract:design_system_pinned",
        accessibility.get("design_system") == "codestrata-visual-design-system:1.0",
        str(accessibility.get("design_system")),
    )

    for section in (
        "contrast",
        "focus",
        "keyboard",
        "semantics",
        "tables",
        "links",
        "images",
        "status_and_risk",
        "motion",
        "forced_colors",
        "zoom_and_text",
        "touch_targets",
        "language",
        "print",
        "surface_exceptions",
    ):
        add(f"contract:accessibility_section:{section}", section in accessibility, "present")

    pairs = accessibility.get("contrast", {}).get("required_pairs", {})
    add(
        "contract:contrast_themes",
        {"light", "dark", "print"} <= set(pairs),
        ",".join(sorted(pairs)),
    )

    # The contract must reference tokens by name, not restate hex values.
    serialised = str(accessibility)
    add("contract:no_duplicated_hex", "#" not in serialised, "token_names_only")

    add(
        "contract:viewport_matrix",
        tuple(responsive.get("viewport_matrix_px", ())) == VIEWPORT_MATRIX_PX,
        ",".join(str(width) for width in VIEWPORT_MATRIX_PX),
    )
    add(
        "contract:no_page_overflow_rule",
        responsive.get("page_level_horizontal_overflow_allowed") is False,
        "false",
    )
    add(
        "contract:allowed_inner_overflow",
        bool(responsive.get("allowed_inner_overflow", {}).get("selectors")),
        "declared",
    )
    add(
        "contract:media_presence_not_sufficient",
        responsive.get("static_validation", {}).get("media_query_presence_sufficient_for_pass")
        is False,
        "false",
    )
    surfaces = responsive.get("surfaces", {})
    for surface in (
        "documentation",
        "assessment_report",
        "engineering_intelligence_report",
        "vscode_extension",
        "marketplace",
    ):
        add(f"contract:responsive_surface:{surface}", surface in surfaces, "declared")

    if not accessibility or not responsive:
        defects.append(Defect("harness/tooling", "design-system accessibility contract missing"))
    return checks, defects
