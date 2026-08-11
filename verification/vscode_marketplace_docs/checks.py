"""Focused static checks for Slice 13.13 Marketplace documentation."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.vscode_marketplace_docs.contract import (
    AI_QUALIFICATION,
    ASSESSMENT_SCHEMA_VERSION,
    BRANDING_POLICY_VERSION,
    DISPLAY_NAME,
    DOCS_PACKAGE,
    DOCS_POLICY_ID,
    DOCS_POLICY_VERSION,
    FORBIDDEN_CLAIM_FRAGMENTS,
    FORBIDDEN_INTERNAL_FRAGMENTS,
    GALLERY_ORDER,
    INTENDED_VSCODE_VERSION,
    MARKETPLACE_MD_RELATIVE,
    PRIVATE_URL_FRAGMENTS,
    README_RELATIVE,
    REQUIRED_HEADINGS,
    TAGLINE,
)
from verification.vscode_marketplace_docs.models import CheckResult, Defect


def _read(monorepo: Path, relative: str) -> str:
    return (monorepo / relative).read_text(encoding="utf-8")


def _pkg(monorepo: Path) -> dict:
    return json.loads(_read(monorepo, "vscode-plugin/package.json"))


def _heading_order_ok(readme: str) -> bool:
    positions: list[int] = []
    for heading in REQUIRED_HEADINGS:
        needle = f"## {heading}"
        idx = readme.find(needle)
        if idx < 0:
            return False
        positions.append(idx)
    return positions == sorted(positions)


def check_all(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    policy = _read(monorepo, f"{DOCS_PACKAGE}/policy.ts")
    claims = _read(monorepo, f"{DOCS_PACKAGE}/claims.ts")
    readme = _read(monorepo, README_RELATIVE)
    marketplace_md = _read(monorepo, MARKETPLACE_MD_RELATIVE)
    docs_meta = _read(monorepo, "vscode-plugin/docs/marketplace-documentation.md")
    branding_docs = _read(monorepo, "vscode-plugin/docs/marketplace-branding.md")
    pkg = _pkg(monorepo)
    ext = _read(monorepo, "vscode-plugin/src/extension.ts")
    vscodeignore = _read(monorepo, "vscode-plugin/.vscodeignore")

    readme_lower = readme.lower()
    claim_hits = [f for f in FORBIDDEN_CLAIM_FRAGMENTS if f in readme_lower]
    internal_hits = [f for f in FORBIDDEN_INTERNAL_FRAGMENTS if f in readme_lower]
    # Word-boundary Cursor product claims (allow historical docs elsewhere)
    cursor_hit = bool(re.search(r"\bcursor\b", readme_lower))
    cloud_hits = [
        f
        for f in (
            "cloud dashboard",
            "data lake",
            "synced insights",
            "team dashboards",
            "centralized analytics",
        )
        if f in readme_lower
    ]

    private_hits = [
        f
        for f in PRIVATE_URL_FRAGMENTS
        if f in readme_lower or f in marketplace_md.lower()
    ]

    images = re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", readme)
    broken_images = [
        src
        for _alt, src in images
        if not (monorepo / "vscode-plugin" / src).is_file()
    ]
    missing_alt = [src for alt, src in images if not alt.strip()]

    gallery_present = all(
        (monorepo / "vscode-plugin" / rel).is_file() for rel in GALLERY_ORDER
    )
    gallery_order_readme = all(
        readme.find(GALLERY_ORDER[i]) < readme.find(GALLERY_ORDER[i + 1])
        for i in range(len(GALLERY_ORDER) - 1)
    )

    relative_links = re.findall(r"\]\(([^)]+)\)", readme)
    broken_rel = []
    for link in relative_links:
        if link.startswith("http://") or link.startswith("https://"):
            continue
        if link.startswith("#"):
            continue
        target = link.split("#", 1)[0]
        if not target:
            continue
        if not (monorepo / "vscode-plugin" / target).exists():
            broken_rel.append(link)

    public_link_needles = (
        "https://docs.codestrata.ai/extensions/vscode",
        "https://codestrata.ai",
        "PRIVACY.md",
        "SECURITY.md",
        "SUPPORT.md",
        "LICENSE",
    )

    slice_1314_absent = not (
        monorepo / "verification" / "vscode_epic14_product_experience"
    ).exists() and "startEpic14ProductExperience" not in ext

    authority_ok = (
        'listing_authority: "readme"' in policy
        or 'MARKETPLACE_LISTING_AUTHORITY = "readme"' in policy
    ) and "Authoritative Marketplace listing" in marketplace_md

    checks.extend(
        [
            CheckResult(
                "policy:id_version",
                DOCS_POLICY_ID in policy and DOCS_POLICY_VERSION in policy,
                f"{DOCS_POLICY_ID}:{DOCS_POLICY_VERSION}",
                "documentation_policy",
            ),
            CheckResult(
                "policy:authority_readme",
                authority_ok and "authoritative" in docs_meta.lower(),
                "README is listing authority",
                "documentation_policy",
            ),
            CheckResult(
                "policy:flags",
                "telemetry_operational_claim_allowed: false" in policy
                and "automatic_installation_claim_allowed: false" in policy
                and "cursor_claim_allowed: false" in policy
                and "cloud_dashboard_claim_allowed: false" in policy
                and "clean_install_validation_complete: true" in policy,
                "claim flags",
                "documentation_policy",
            ),
            CheckResult(
                "structure:headings",
                _heading_order_ok(readme),
                f"headings={len(REQUIRED_HEADINGS)}",
                "structure",
            ),
            CheckResult(
                "structure:display_tagline",
                DISPLAY_NAME.split("–")[0].strip() in readme
                and TAGLINE in readme
                and pkg.get("displayName") == DISPLAY_NAME,
                "naming preserved",
                "structure",
            ),
            CheckResult(
                "claims:matrix",
                "MARKETPLACE_CLAIM_MATRIX" in claims
                and "prohibited_claim" in claims
                and "cursor_support" in claims,
                "claim matrix present",
                "claim_matrix",
            ),
            CheckResult(
                "claims:readme_clean",
                not claim_hits,
                "clean" if not claim_hits else str(claim_hits),
                "claim_matrix",
            ),
            CheckResult(
                "workflow:quick_start",
                "Initialize Repository" in readme
                and "Run Assessment" in readme
                and "Open HTML Report" in readme,
                "quick start commands",
                "workflow",
            ),
            CheckResult(
                "installation:guidance_only",
                "does **not** install the CLI automatically" in readme
                or "Does **not** run package managers" in readme,
                "guidance-only install",
                "installation",
            ),
            CheckResult(
                "initialization:engine_owned",
                "codestrata.toml" in readme
                and "Engine-owned" in readme
                and "no force overwrite" in readme.lower(),
                "init documented",
                "initialization",
            ),
            CheckResult(
                "assessment:local_cli",
                "local Engine CLI" in readme
                and "Running an Assessment" in readme,
                "assessment documented",
                "assessment",
            ),
            CheckResult(
                "ai:qualification",
                AI_QUALIFICATION in readme
                and "Engine may send provider request content" in readme,
                "AI qualified",
                "ai",
            ),
            CheckResult(
                "progress:indeterminate",
                "indeterminate" in readme_lower
                and "percentage" in readme_lower,
                "indeterminate progress",
                "progress",
            ),
            CheckResult(
                "report:local_html",
                "Open HTML Report" in readme
                and "assessment.html" in readme
                and "does **not** change the assessment result" in readme,
                "report documented",
                "report",
            ),
            CheckResult(
                "recovery:user_triggered",
                "user-triggered" in readme_lower
                and "Nothing installs, retries, or remediates automatically"
                in readme,
                "recovery documented",
                "recovery",
            ),
            CheckResult(
                "compatibility:0_2_x",
                "0.2.x" in readme
                and "0.1.x" in readme
                and "prerelease" in readme_lower,
                "matrix documented",
                "compatibility",
            ),
            CheckResult(
                "telemetry:posture",
                "default" in readme_lower
                and "deny" in readme_lower
                and "not persisted" in readme_lower
                or ("not saved" in readme_lower and "deny" in readme_lower),
                "telemetry posture",
                "telemetry",
            ),
            CheckResult(
                "telemetry:not_operational",
                "default assessment does not transmit" in readme_lower
                and "telemetry opt-in is **not** report-publish authorization"
                in readme_lower,
                "no default operational transmission claim",
                "telemetry",
            ),
            CheckResult(
                "locality:no_upload",
                "does **not** upload repository source to CodeStrata Community"
                in readme
                or "does **not** upload repository source to CodeStrata Community services"
                in readme,
                "no Community upload",
                "locality",
            ),
            CheckResult(
                "privacy:no_identity",
                "machine identity" in readme_lower
                and "installation identity" in readme_lower,
                "no identity",
                "privacy",
            ),
            CheckResult(
                "security:links",
                "[SECURITY.md](SECURITY.md)" in readme
                and "[PRIVACY.md](PRIVACY.md)" in readme,
                "security/privacy linked",
                "security",
            ),
            CheckResult(
                "screenshots:gallery",
                gallery_present and gallery_order_readme,
                "gallery order",
                "screenshot",
            ),
            CheckResult(
                "screenshots:alt_text",
                not missing_alt and len(images) >= 5,
                f"images={len(images)} missing_alt={len(missing_alt)}",
                "accessibility",
            ),
            CheckResult(
                "screenshots:paths",
                not broken_images,
                "ok" if not broken_images else str(broken_images),
                "screenshot",
            ),
            CheckResult(
                "links:relative",
                not broken_rel,
                "ok" if not broken_rel else str(broken_rel),
                "link",
            ),
            CheckResult(
                "links:public",
                all(n in readme for n in public_link_needles)
                and not private_hits,
                "public links",
                "link",
            ),
            CheckResult(
                "cursor:absent",
                not cursor_hit,
                "absent" if not cursor_hit else "cursor present",
                "cursor_absence",
            ),
            CheckResult(
                "cloud:absent",
                not cloud_hits,
                "absent" if not cloud_hits else str(cloud_hits),
                "cloud_claim",
            ),
            CheckResult(
                "internal:boundary",
                not internal_hits,
                "clean" if not internal_hits else str(internal_hits),
                "internal_boundary",
            ),
            CheckResult(
                "package:readme_authority",
                "README.md" in marketplace_md
                and "publishing" in marketplace_md.lower(),
                "MARKETPLACE.md is checklist",
                "package_rendering",
            ),
            CheckResult(
                "package:ignore",
                "src/**" in vscodeignore and "out/test/**" in vscodeignore
                and not (monorepo / "vscode-plugin" / "reports").exists(),
                "package boundary",
                "package_rendering",
            ),
            CheckResult(
                "accessibility:headings",
                readme.startswith("# ")
                and readme.count("\n## ") >= 10
                and readme.count("\n### ") == 0,
                "H1 then H2",
                "accessibility",
            ),
            CheckResult(
                "vscode:version",
                pkg.get("version") == INTENDED_VSCODE_VERSION,
                INTENDED_VSCODE_VERSION,
                "vscode_regression",
            ),
            CheckResult(
                "schema:assessment_1_2",
                ASSESSMENT_SCHEMA_VERSION == "1.2",
                ASSESSMENT_SCHEMA_VERSION,
                "vscode_regression",
            ),
            CheckResult(
                "prior:branding_1_0",
                BRANDING_POLICY_VERSION == "1.0"
                and 'MARKETPLACE_BRANDING_POLICY_VERSION = "1.0"'
                in _read(
                    monorepo, "vscode-plugin/src/marketplaceBranding/policy.ts"
                ),
                "branding policy 1.0",
                "vscode_regression",
            ),
            CheckResult(
                "package:test_wired",
                "marketplaceDocs.test.js"
                in _read(monorepo, "vscode-plugin/package.json"),
                "unit test wired",
                "vscode_regression",
            ),
            CheckResult(
                "epic_14:not_started",
                slice_1314_absent,
                "Epic 14 deferred",
                "deferred_clean_install",
            ),
            CheckResult(
                "docs:meta_present",
                (monorepo / "vscode-plugin/docs/marketplace-documentation.md").is_file()
                and "listing" in docs_meta.lower()
                and "marketplace-documentation.md" in branding_docs,
                "meta docs",
                "documentation_policy",
            ),
            CheckResult(
                "limitations:section",
                "## Known Limitations" in readme
                and "CLI auto-install is not supported" in readme,
                "limitations present",
                "structure",
            ),
        ]
    )

    # Fix telemetry check operator precedence - rewrite as clearer
    telemetry_ok = (
        "deny" in readme_lower
        and ("not saved" in readme_lower or "not persisted" in readme_lower)
        and "command-local" in readme_lower
    )
    for i, c in enumerate(checks):
        if c.name == "telemetry:posture":
            checks[i] = CheckResult(
                c.name, telemetry_ok, c.detail, c.category
            )

    if claim_hits:
        defects.append(
            Defect("claim defect", "README", "no forbidden claims", str(claim_hits))
        )
    if internal_hits:
        defects.append(
            Defect(
                "public/internal boundary defect",
                "README",
                "no internal jargon",
                str(internal_hits),
            )
        )
    if cursor_hit:
        defects.append(
            Defect("Cursor regression", "README", "no Cursor", "present")
        )
    if broken_images:
        defects.append(
            Defect("screenshot defect", "README", "resolving images", str(broken_images))
        )

    return checks, defects
