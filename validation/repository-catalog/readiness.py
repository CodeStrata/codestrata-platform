"""SV.10A curated repository catalog readiness gate.

Catalog readiness and SV.10 execution planning only. Does not assess
repositories, invent catalog entries, or change Engine/Platform product code.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from validate_catalog import (
    CATALOG_RELATIVE_PATH,
    CATALOG_SCHEMA_NAME,
    CATALOG_SCHEMA_VERSION,
    catalog_path,
    is_floating_revision,
    is_full_commit_sha,
    load_catalog_document,
    validate_catalog_document,
)

READINESS_SCHEMA_NAME = "repository-catalog-readiness"
READINESS_SCHEMA_VERSION = "1.0.0"
DEFAULT_RELEASE_VALIDATION_TARGET = 22
RELEASE_SCOPE_NOTE = (
    "v0.2.0 System Verification uses 22 curated repositories. "
    "The catalog may expand to 30 or more in later releases."
)

SUPPORTED_LANGUAGE_GROUPS = frozenset(
    {"C#/.NET", "Java", "JS/TS", "PHP", "Python"}
)
UNSUPPORTED_LANGUAGE_DIVERSITY = frozenset(
    {"Go", "Rust", "Ruby", "Kotlin", "Scala", "Swift", "C", "C++", "Objective-C"}
)

ROLE_VOCABULARY = frozenset(
    {
        "smoke",
        "regression",
        "engineering_intelligence",
        "performance",
        "release_validation",
    }
)
TIER_VOCABULARY = frozenset({"tier1", "tier2", "tier3", "tier4"})
SIZE_VOCABULARY = frozenset({"small", "medium", "large", "unknown"})

# Deterministic enrichment for existing catalog IDs only (no new repositories).
_ECOSYSTEM: dict[str, str | None] = {
    "aspnetcore": "NuGet",
    "cleanarchitecture": "NuGet",
    "eshop": "NuGet",
    "express": "npm",
    "juice-shop": "npm",
    "nodegoat": "npm",
    "typescript": "npm",
    "vite": "npm",
    "vulnerable-app-nodejs-express": "npm",
    "doris": "Maven",
    "dubbo": "Maven",
    "spring-petclinic": "Maven",
    "verademo": "Maven",
    "bagisto": "Composer",
    "laravel-io": "Composer",
    "slim": "Composer",
    "bookstack": "Composer",
    "django": "pip",
    "flask": "pip",
    "gradio": "pip",
    "moodle": "Composer",
    "product-integrator-mi": "Maven",
}

_FRAMEWORK: dict[str, str | None] = {
    "aspnetcore": "ASP.NET Core web framework",
    "cleanarchitecture": "ASP.NET Clean Architecture template",
    "eshop": ".NET cloud-native ecommerce reference",
    "express": "Node.js HTTP framework",
    "juice-shop": "OWASP Juice Shop vulnerable web app",
    "nodegoat": "OWASP NodeGoat vulnerable web app",
    "typescript": "TypeScript compiler / toolchain",
    "vite": "Frontend build tool",
    "vulnerable-app-nodejs-express": "Vulnerable Express sample",
    "doris": "Apache Doris analytics database",
    "dubbo": "Apache Dubbo RPC / microservices",
    "spring-petclinic": "Spring Boot sample web app",
    "verademo": "Veracode deliberately insecure Spring demo",
    "bagisto": "Laravel ecommerce platform",
    "laravel-io": "Laravel community portal",
    "slim": "PHP Slim microframework",
    "bookstack": "Laravel / BookStack documentation wiki",
    "django": "Django web framework",
    "flask": "Flask microframework",
    "gradio": "Gradio ML UI framework",
    "moodle": "Moodle LMS / PHP web application",
    "product-integrator-mi": "WSO2 Micro Integrator",
}

_PROJECT_SHAPE: dict[str, str] = {
    "aspnetcore": "library_framework",
    "cleanarchitecture": "web_application",
    "eshop": "web_application",
    "express": "library_framework",
    "juice-shop": "web_application",
    "nodegoat": "web_application",
    "typescript": "toolchain",
    "vite": "toolchain",
    "vulnerable-app-nodejs-express": "web_application",
    "doris": "backend_system",
    "dubbo": "library_framework",
    "spring-petclinic": "web_application",
    "verademo": "web_application",
    "bagisto": "web_application",
    "laravel-io": "web_application",
    "slim": "library_framework",
    "bookstack": "web_application",
    "django": "library_framework",
    "flask": "library_framework",
    "gradio": "library_framework",
    "moodle": "web_application",
    "product-integrator-mi": "backend_system",
}

_OVERLAP_GROUPS: dict[str, str] = {
    "aspnetcore": "dotnet_platform",
    "cleanarchitecture": "dotnet_platform",
    "eshop": "dotnet_platform",
    "express": "nodejs_express_family",
    "vulnerable-app-nodejs-express": "nodejs_express_family",
    "nodegoat": "nodejs_express_family",
    "juice-shop": "deliberately_insecure_web",
    "verademo": "deliberately_insecure_web",
    "bagisto": "laravel_ecosystem",
    "bookstack": "laravel_ecosystem",
    "laravel-io": "laravel_ecosystem",
    "django": "python_web_framework",
    "flask": "python_web_framework",
    "typescript": "js_ts_toolchain",
    "vite": "js_ts_toolchain",
}

NEAR_DUPLICATE_GROUPS: tuple[dict[str, Any], ...] = (
    {
        "group": "dotnet_platform",
        "repository_ids": ["aspnetcore", "cleanarchitecture", "eshop"],
    },
    {
        "group": "nodejs_express_family",
        "repository_ids": [
            "express",
            "nodegoat",
            "vulnerable-app-nodejs-express",
        ],
    },
    {
        "group": "deliberately_insecure_web",
        "repository_ids": [
            "juice-shop",
            "nodegoat",
            "verademo",
            "vulnerable-app-nodejs-express",
        ],
    },
    {
        "group": "laravel_ecosystem",
        "repository_ids": ["bagisto", "bookstack", "laravel-io"],
    },
    {
        "group": "python_web_framework",
        "repository_ids": ["django", "flask"],
    },
    {
        "group": "js_ts_toolchain",
        "repository_ids": ["typescript", "vite"],
    },
)

# Owner-supplied pins / candidates outside catalog.json (not imported unless listed).
OWNER_SUPPLIED_OUTSIDE_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "source_path": "validation/csharp-eshop.toml",
        "project_name": "eShop",
        "github_repository": "dotnet/eShop",
        "github_url": "https://github.com/dotnet/eShop",
        "catalog_id_if_present": "eshop",
        "pinned_commit": "9b4f9434f46fdc5c1a6e9e936af2868340cdbc48",
        "language_group": "C#/.NET",
        "note": "Community qualification config; pin promoted into catalog for existing id eshop.",
    },
    {
        "source_path": "validation/java-spring-petclinic.toml",
        "project_name": "spring-petclinic",
        "github_repository": "spring-projects/spring-petclinic",
        "github_url": "https://github.com/spring-projects/spring-petclinic",
        "catalog_id_if_present": "spring-petclinic",
        "pinned_commit": "f182358d02e4a68e52bdbabf55ca7800288511e7",
        "language_group": "Java",
        "note": "Pin already matches catalog; not a new repository.",
    },
    {
        "source_path": "validation/php-bookstack.toml",
        "project_name": "BookStack",
        "github_repository": "BookStackApp/BookStack",
        "github_url": "https://github.com/BookStackApp/BookStack",
        "catalog_id_if_present": "bookstack",
        "pinned_commit": "4e406c41c4c8060a5795e74c66fb96362e54f400",
        "language_group": "PHP",
        "note": (
            "Imported into catalog.json as the v0.2.0 hivemind replacement; "
            "pin reused from Community qualification / Epic 4 remote-php-bookstack."
        ),
    },
    {
        "source_path": "validation/python-fastapi.toml",
        "project_name": "full-stack-fastapi-template",
        "github_repository": "fastapi/full-stack-fastapi-template",
        "github_url": "https://github.com/fastapi/full-stack-fastapi-template",
        "catalog_id_if_present": None,
        "pinned_commit": "c9e70d65c74f7adda417fc8de0757207ff77514c",
        "language_group": "Python",
        "note": "Not in catalog.json; candidate for owner-approved import only.",
    },
    {
        "source_path": "validation/typescript-angular.toml",
        "project_name": "angular-realworld-example-app",
        "github_repository": "gothinkster/angular-realworld-example-app",
        "github_url": "https://github.com/gothinkster/angular-realworld-example-app",
        "catalog_id_if_present": None,
        "pinned_commit": "dd99ed2cf39c805d719f943c5d7061a5683d98a8",
        "language_group": "JS/TS",
        "note": "Not in catalog.json; candidate for owner-approved import only.",
    },
    {
        "source_path": "validation/typescript-vscode.toml",
        "project_name": "vscode",
        "github_repository": "microsoft/vscode",
        "github_url": "https://github.com/microsoft/vscode",
        "catalog_id_if_present": None,
        "pinned_commit": "618f68c2ab3cb8ef7dd6d43c341cd25e3fe211bf",
        "language_group": "JS/TS",
        "note": "Large survival target; not in catalog.json; owner-approved import only.",
    },
    {
        "source_path": "examples/real-world/THIRD_PARTY.md",
        "project_name": "realworld-laravel-layered-architecture",
        "github_repository": "yukicountry/realworld-laravel-layered-architecture",
        "github_url": "https://github.com/yukicountry/realworld-laravel-layered-architecture",
        "catalog_id_if_present": None,
        "pinned_commit": None,
        "language_group": "PHP",
        "note": "Examples attribution only; no pin recorded; not imported.",
    },
)

SV6_PREFERRED_SUBSET: tuple[str, ...] = (
    "cleanarchitecture",
    "express",
    "flask",
    "slim",
    "spring-petclinic",
)

_KB_RE = re.compile(r"([\d,]+)\s*KB", re.IGNORECASE)


def release_validation_target(data: dict[str, Any]) -> int:
    raw = data.get("release_validation_target")
    if raw is None:
        return DEFAULT_RELEASE_VALIDATION_TARGET
    return int(raw)


def parse_size_kb(approximate_size: Any) -> int | None:
    if approximate_size is None:
        return None
    text = str(approximate_size).strip()
    match = _KB_RE.search(text)
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def size_bucket(item: dict[str, Any]) -> str:
    category = str(item.get("candidate_category") or "").strip()
    kb = parse_size_kb(item.get("approximate_size"))
    if kb is not None:
        if kb < 50_000:
            return "small"
        if kb < 300_000:
            return "medium"
        return "large"
    lowered = str(item.get("approximate_size") or "").strip().lower()
    if category == "Small" or lowered == "small":
        return "small"
    if category == "Medium" or lowered in {"medium", "small/medium"}:
        return "medium"
    if category == "Large" or "large" in lowered:
        return "large"
    return "unknown"


def infer_runtime_tier(item: dict[str, Any]) -> str:
    """Map size / category to SV.10 execution tiers (planning only)."""

    rid = str(item.get("id") or "")
    # Honor explicit catalog tiers when already set.
    explicit = item.get("expected_runtime_tier")
    if explicit in TIER_VOCABULARY:
        return str(explicit)
    kb = parse_size_kb(item.get("approximate_size"))
    bucket = size_bucket(item)
    # Explicit slow / very-large schedule (Tier 4).
    if rid in {"typescript", "doris"} or (kb is not None and kb >= 1_000_000):
        return "tier4"
    if rid in {"aspnetcore", "bagisto", "gradio", "moodle"} or (
        kb is not None and kb >= 350_000
    ):
        return "tier4"
    # BookStack: Epic 4 tier-3 / comparatively slow real-world Laravel app.
    if rid == "bookstack":
        return "tier3"
    category = str(item.get("candidate_category") or "")
    if category == "Small" and bucket == "small":
        return "tier1"
    if category in {"Medium", "Known Issues"} or bucket == "medium":
        return "tier2"
    if category == "Large" or bucket == "large":
        return "tier3"
    return "tier3"


def revision_is_qualified_commit(raw: Any) -> bool:
    if not isinstance(raw, dict):
        return False
    if str(raw.get("type") or "").strip().lower() != "commit":
        return False
    value = str(raw.get("value") or "").strip()
    return is_full_commit_sha(value) and not is_floating_revision(value)


def enabled_roles(item: dict[str, Any]) -> dict[str, bool]:
    enabled = item.get("enabled_for")
    if not isinstance(enabled, dict):
        return {role: False for role in sorted(ROLE_VOCABULARY)}
    return {role: bool(enabled.get(role, False)) for role in sorted(ROLE_VOCABULARY)}


def enrichment_for(item: dict[str, Any]) -> dict[str, Any]:
    rid = str(item.get("id") or "")
    has_pin = revision_is_qualified_commit(item.get("qualified_revision"))
    status = str(item.get("qualification_status") or "").strip().lower()
    if not status:
        status = "qualified" if has_pin else "unqualified"
    tier = str(item.get("expected_runtime_tier") or infer_runtime_tier(item))
    lang = item.get("language_group")
    return {
        "repository_id": rid,
        "visibility": item.get("visibility") or "public",
        "qualification_status": status,
        "qualification_block_reason": item.get("qualification_block_reason"),
        "expected_runtime_tier": tier if tier in TIER_VOCABULARY else infer_runtime_tier(item),
        "size_bucket": size_bucket(item),
        "dependency_ecosystem": item.get("dependency_ecosystem")
        if "dependency_ecosystem" in item
        else _ECOSYSTEM.get(rid),
        "framework_or_shape": item.get("framework_or_shape")
        if "framework_or_shape" in item
        else _FRAMEWORK.get(rid),
        "project_shape": item.get("project_shape")
        if "project_shape" in item
        else _PROJECT_SHAPE.get(rid, "unknown"),
        "overlap_group": item.get("overlap_group", _OVERLAP_GROUPS.get(rid)),
        "requires_submodules": item.get("requires_submodules"),
        "requires_git_lfs": item.get("requires_git_lfs"),
        "archived": bool(item.get("archived", False)),
        "suitable_for_unattended_ci": (
            item.get("suitable_for_unattended_ci")
            if "suitable_for_unattended_ci" in item
            else bool(status == "qualified" and lang in SUPPORTED_LANGUAGE_GROUPS and tier in {"tier1", "tier2", "tier3"})
        ),
        "suitable_for_engineering_intelligence": (
            item.get("suitable_for_engineering_intelligence")
            if "suitable_for_engineering_intelligence" in item
            else bool(status == "qualified" and lang in SUPPORTED_LANGUAGE_GROUPS)
        ),
        "roles": enabled_roles(item),
        "qualified_revision": item.get("qualified_revision") if has_pin else None,
        "language_group": lang,
        "license": item.get("license"),
        "github_repository": item.get("github_repository"),
        "candidate_category": item.get("candidate_category"),
    }


def coverage_matrix(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def count(key: str) -> dict[str, int]:
        counter: Counter[str] = Counter()
        for row in rows:
            value = row.get(key)
            label = "null" if value is None or value == "" else str(value)
            counter[label] += 1
        return dict(sorted(counter.items()))

    role_counts: Counter[str] = Counter()
    for row in rows:
        for role, enabled in (row.get("roles") or {}).items():
            if enabled:
                role_counts[role] += 1

    return {
        "language": count("language_group"),
        "dependency_ecosystem": count("dependency_ecosystem"),
        "framework_or_shape": count("framework_or_shape"),
        "size_bucket": count("size_bucket"),
        "expected_runtime_tier": count("expected_runtime_tier"),
        "project_shape": count("project_shape"),
        "license": count("license"),
        "visibility": count("visibility"),
        "roles": dict(sorted(role_counts.items())),
        "overlap_group": count("overlap_group"),
        "dataset_limitation": (
            "This catalog is a curated CodeStrata verification dataset. Its results "
            "describe only the included pinned repositories and are not a product-wide "
            "accuracy or industry benchmark claim."
        ),
    }


def build_execution_batches(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deterministic SV.10 batch plan for release_validation-enabled repos."""

    sv10 = [
        row
        for row in rows
        if (row.get("roles") or {}).get("release_validation")
        and row.get("qualification_status") == "qualified"
    ]
    sv10.sort(key=lambda row: str(row["repository_id"]))

    def batch(batch_id: str, tier: str, members: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "batch_id": batch_id,
            "expected_runtime_tier": tier,
            "repository_ids": [m["repository_id"] for m in members],
            "pinned_revisions": {
                m["repository_id"]: (m.get("qualified_revision") or {}).get("value")
                for m in members
            },
            "clone_requirement": "external_temp_clone_outside_source_tree",
            "assessment_mode": {
                "command": "codestrata assess --repo . --output reports --no-ai",
                "ai_enabled": False,
                "install_dependencies": False,
                "initialize_submodules": False,
                "download_git_lfs": False,
            },
            "output_location_strategy": (
                "per-repository reports under a verification output root keyed by catalog id"
            ),
            "cache_behavior": (
                "reuse prior assessment cache only when catalog id + commit SHA match"
            ),
            "cleanup_behavior": (
                "delete temporary clones after each repository; retain reports only"
            ),
            "retry_policy": "single_retry_on_transient_clone_failure",
            "fail_fast_behavior": "continue_batch_record_failure_fail_suite_at_end",
            "disk_space_warning": (
                "warn when free disk is below estimated clone+report footprint for remaining batch"
            ),
            "network_boundary": (
                "clone/fetch only; no assessment-time dependency installs; network tests gated"
            ),
            "executed_in_sv10a": False,
        }

    by_tier = {tier: [] for tier in ("tier1", "tier2", "tier3", "tier4")}
    for row in sv10:
        tier = str(row.get("expected_runtime_tier") or "tier3")
        by_tier.setdefault(tier, []).append(row)

    return [
        batch("batch_1_tier1_fast", "tier1", by_tier.get("tier1", [])),
        batch("batch_2_tier2_regression", "tier2", by_tier.get("tier2", [])),
        batch("batch_3_tier3_intelligence_release", "tier3", by_tier.get("tier3", [])),
        batch("batch_4_tier4_scheduled_slow", "tier4", by_tier.get("tier4", [])),
    ]


def build_import_template(*, missing_count: int) -> dict[str, Any]:
    """Deterministic template for release-owner supplied candidates (not invented)."""

    return {
        "schema_name": "repository-catalog-candidate-import",
        "schema_version": "1.0.0",
        "purpose": (
            "Import template for release-owner / Vinay supplied repositories. "
            "Do not invent candidates. Fill only approved GitHub identities, then "
            "qualify full commit SHAs before enabling release_validation."
        ),
        "slots_required": missing_count,
        "supported_language_groups": sorted(SUPPORTED_LANGUAGE_GROUPS),
        "forbidden_languages_for_diversity_only": sorted(UNSUPPORTED_LANGUAGE_DIVERSITY),
        "required_fields": [
            "id",
            "project_name",
            "github_repository",
            "github_url",
            "visibility",
            "license",
            "language_group",
            "dependency_ecosystem",
            "framework_or_shape",
            "candidate_category",
            "expected_runtime_tier",
            "enabled_for",
            "qualified_revision",
            "source_attribution",
        ],
        "qualified_revision_contract": {
            "type": "commit",
            "value": "<full lowercase 40-character SHA>",
            "source_tag": "<optional human-readable release tag>",
        },
        "candidate_slots": [
            {
                "slot": index,
                "id": None,
                "project_name": None,
                "github_repository": None,
                "github_url": None,
                "language_group": None,
                "source_attribution": None,
                "qualified_revision": None,
            }
            for index in range(1, missing_count + 1)
        ],
        "owner_supplied_outside_catalog_not_auto_imported": [
            {
                "project_name": row["project_name"],
                "github_repository": row["github_repository"],
                "github_url": row["github_url"],
                "source_path": row["source_path"],
                "pinned_commit": row["pinned_commit"],
                "language_group": row["language_group"],
                "catalog_id_if_present": row["catalog_id_if_present"],
                "note": row["note"],
            }
            for row in OWNER_SUPPLIED_OUTSIDE_CATALOG
            if row["catalog_id_if_present"] is None
        ],
    }


def qualification_checks(
    data: dict[str, Any], rows: list[dict[str, Any]], *, target: int
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def add(check_id: str, ok: bool, detail: str) -> None:
        checks.append({"check_id": check_id, "ok": ok, "detail": detail})

    validation = validate_catalog_document(data)
    add(
        "catalog_schema_valid",
        validation.ok,
        "ok" if validation.ok else f"{len(validation.issues)} issue(s)",
    )
    add(
        "canonical_catalog_path",
        True,
        CATALOG_RELATIVE_PATH,
    )
    add(
        "schema_name_version",
        data.get("schema_name") == CATALOG_SCHEMA_NAME
        and data.get("schema_version") == CATALOG_SCHEMA_VERSION,
        f"{data.get('schema_name')}@{data.get('schema_version')}",
    )

    ids = [str(r.get("repository_id")) for r in rows]
    add("unique_repository_ids", len(ids) == len(set(ids)), f"count={len(ids)}")
    githubs = [str(r.get("github_repository")) for r in rows]
    add(
        "unique_github_repositories",
        len(githubs) == len(set(githubs)),
        f"count={len(githubs)}",
    )

    actual = len(rows)
    add(
        "release_validation_target_count",
        actual == target,
        f"actual={actual} target={target} (v0.2.0 curated set)",
    )

    all_pinned = all(revision_is_qualified_commit(r.get("qualified_revision")) for r in rows)
    add(
        "all_repositories_full_commit_sha",
        all_pinned,
        "all 22 pinned" if all_pinned else "missing pins",
    )

    sv10 = [r for r in rows if (r.get("roles") or {}).get("release_validation")]
    add(
        "all_repositories_release_validation_enabled",
        len(sv10) == target == actual,
        f"sv10_enabled={len(sv10)} target={target}",
    )

    unpinned_sv10 = [
        r["repository_id"]
        for r in sv10
        if r.get("qualification_status") != "qualified"
        or not revision_is_qualified_commit(r.get("qualified_revision"))
    ]
    add(
        "sv10_pin_completeness",
        not unpinned_sv10,
        "all pinned" if not unpinned_sv10 else f"unpinned={unpinned_sv10}",
    )

    unsupported = [
        r["repository_id"]
        for r in rows
        if r.get("language_group") in UNSUPPORTED_LANGUAGE_DIVERSITY
    ]
    add(
        "no_unsupported_language_diversity",
        not unsupported,
        "ok" if not unsupported else f"unsupported={unsupported}",
    )

    missing_lang = [
        r["repository_id"]
        for r in rows
        if r.get("language_group") not in SUPPORTED_LANGUAGE_GROUPS
    ]
    add(
        "supported_language_vocabulary_complete",
        not missing_lang,
        "ok" if not missing_lang else f"incomplete={missing_lang}",
    )

    incomplete_meta = [
        r["repository_id"]
        for r in rows
        if r.get("language_group") not in SUPPORTED_LANGUAGE_GROUPS
        or not r.get("license")
        or str(r.get("license")).lower().startswith("see repo")
        or r.get("visibility") != "public"
        or r.get("expected_runtime_tier") not in TIER_VOCABULARY
        or not revision_is_qualified_commit(r.get("qualified_revision"))
    ]
    add(
        "complete_qualification_metadata",
        not incomplete_meta,
        "ok" if not incomplete_meta else f"incomplete={incomplete_meta}",
    )

    role_ok = True
    for r in rows:
        roles = r.get("roles") or {}
        if set(roles) != ROLE_VOCABULARY:
            role_ok = False
            break
    add("role_vocabulary", role_ok, "enabled_for roles present")

    tier_ok = all(r.get("expected_runtime_tier") in TIER_VOCABULARY for r in rows)
    add("tier_vocabulary", tier_ok, "expected_runtime_tier in vocabulary")

    license_gaps = [
        r["repository_id"]
        for r in rows
        if not r.get("license") or str(r.get("license")).startswith("See repo")
    ]
    add(
        "license_resolved",
        not license_gaps,
        "ok" if not license_gaps else f"unresolved={license_gaps}",
    )

    visibility_ok = all(r.get("visibility") == "public" for r in rows)
    add("public_visibility", visibility_ok, "public required for v0.2.0 curated set")

    sv6_ok = all(
        any(r["repository_id"] == rid and r["qualification_status"] == "qualified" for r in rows)
        for rid in SV6_PREFERRED_SUBSET
    )
    add("sv6_preferred_subset_still_qualified", sv6_ok, ",".join(SV6_PREFERRED_SUBSET))

    floating = []
    for item in data.get("repositories") or []:
        rev = item.get("qualified_revision")
        if isinstance(rev, dict) and is_floating_revision(str(rev.get("value") or "")):
            floating.append(item.get("id"))
    add("no_floating_revisions", not floating, "ok" if not floating else str(floating))

    batches = build_execution_batches(rows)
    add(
        "execution_batches_defined",
        len(batches) == 4 and all("repository_ids" in batch for batch in batches),
        "four deterministic SV.10 batches",
    )

    return checks


def build_readiness_report(data: dict[str, Any]) -> dict[str, Any]:
    target = release_validation_target(data)
    repos = [item for item in (data.get("repositories") or []) if isinstance(item, dict)]
    rows = [enrichment_for(item) for item in repos]
    rows.sort(key=lambda row: str(row["repository_id"]))

    qualified = [r for r in rows if r["qualification_status"] == "qualified"]
    unqualified = [r["repository_id"] for r in rows if r["qualification_status"] != "qualified"]
    sv10 = [r for r in rows if (r.get("roles") or {}).get("release_validation")]
    sv10_qualified = [r for r in sv10 if r["qualification_status"] == "qualified"]

    missing_count = max(0, target - len(rows))
    checks = qualification_checks(data, rows, target=target)
    failed = [c for c in checks if not c["ok"]]

    blockers: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    if missing_count > 0:
        blockers.append(
            {
                "code": "catalog_population_gap",
                "message": (
                    f"v0.2.0 curated target is {target} repositories; catalog has {len(rows)} "
                    f"entries ({missing_count} missing). Missing repositories were not invented."
                ),
            }
        )
    elif len(rows) != target:
        blockers.append(
            {
                "code": "catalog_population_mismatch",
                "message": (
                    f"v0.2.0 curated target is exactly {target} repositories; "
                    f"catalog has {len(rows)}."
                ),
            }
        )

    blocked_entries = [
        r for r in rows if r.get("qualification_status") == "blocked"
    ]
    for row in blocked_entries:
        blockers.append(
            {
                "code": "repository_qualification_blocked",
                "message": (
                    f"{row['repository_id']}: "
                    f"{row.get('qualification_block_reason') or 'qualification blocked'}; "
                    "not release_validation-enabled. Target remains 22; run not silently reduced."
                ),
            }
        )

    if len(sv10) != target:
        blockers.append(
            {
                "code": "release_validation_enablement_incomplete",
                "message": (
                    f"v0.2.0 PASS requires all {target} curated repositories enabled for "
                    f"release_validation; currently {len(sv10)} enabled "
                    f"({', '.join(r['repository_id'] for r in rows if not (r.get('roles') or {}).get('release_validation'))} excluded)."
                ),
            }
        )

    unpinned_sv10 = [
        r["repository_id"]
        for r in sv10
        if r["qualification_status"] != "qualified"
    ]
    if unpinned_sv10:
        blockers.append(
            {
                "code": "sv10_unqualified_enabled",
                "message": (
                    "SV.10-enabled repositories missing full commit pins: "
                    + ", ".join(unpinned_sv10)
                ),
            }
        )

    incomplete_meta = [
        r["repository_id"]
        for r in rows
        if r.get("language_group") not in SUPPORTED_LANGUAGE_GROUPS
        or r.get("license") is None
        or str(r.get("license")).lower().startswith("see repo")
        or not revision_is_qualified_commit(r.get("qualified_revision"))
    ]
    if incomplete_meta:
        blockers.append(
            {
                "code": "incomplete_qualification_metadata",
                "message": (
                    "v0.2.0 PASS requires complete qualification metadata for all curated "
                    "repositories: " + ", ".join(incomplete_meta)
                ),
            }
        )

    overlap_notes = [
        f"{group['group']}={','.join(group['repository_ids'])}"
        for group in NEAR_DUPLICATE_GROUPS
    ]
    if overlap_notes:
        warnings.append(
            {
                "code": "framework_overlap",
                "message": "Near-duplicate / framework overlap groups: "
                + "; ".join(overlap_notes),
            }
        )

    warnings.append(
        {
            "code": "future_catalog_expansion",
            "message": RELEASE_SCOPE_NOTE,
        }
    )

    large_slow = [
        r["repository_id"]
        for r in rows
        if r.get("expected_runtime_tier") == "tier4"
    ]
    if large_slow:
        warnings.append(
            {
                "code": "known_large_slow_repositories",
                "message": "Tier 4 schedule only: " + ", ".join(large_slow),
            }
        )

    submodule_repos = [
        r["repository_id"] for r in rows if r.get("requires_submodules")
    ]
    if submodule_repos:
        warnings.append(
            {
                "code": "submodules_declared",
                "message": (
                    "Repositories declare .gitmodules; do not initialize unless approved: "
                    + ", ".join(submodule_repos)
                ),
            }
        )

    limitations = [
        RELEASE_SCOPE_NOTE,
        "SV.10A performs catalog qualification and planning only; no full multi-repository assessment run.",
        "PASS_WITH_LIMITATIONS is not used to bypass missing repositories, unsupported languages, or unpinned SV.10 entries.",
        (
            "This catalog is a curated CodeStrata verification dataset. Its results describe "
            "only the included pinned repositories and are not a product-wide accuracy or "
            "industry benchmark claim."
        ),
        *list(data.get("limitations") or []),
    ]

    # Verdict rules: never PASS_WITH_LIMITATIONS for population/pin/support gaps.
    hard_check_ids = {
        "release_validation_target_count",
        "all_repositories_full_commit_sha",
        "all_repositories_release_validation_enabled",
        "sv10_pin_completeness",
        "supported_language_vocabulary_complete",
        "complete_qualification_metadata",
        "catalog_schema_valid",
        "execution_batches_defined",
    }
    if blockers or any(c["check_id"] in hard_check_ids and not c["ok"] for c in checks):
        verdict = "BLOCKED"
    elif failed:
        verdict = "BLOCKED"
    else:
        verdict = "PASS"

    lang_dist = Counter(str(r.get("language_group")) for r in rows)
    eco_dist = Counter(str(r.get("dependency_ecosystem")) for r in rows)
    tier_dist = Counter(str(r.get("expected_runtime_tier")) for r in rows)
    role_dist: Counter[str] = Counter()
    for r in rows:
        for role, enabled in (r.get("roles") or {}).items():
            if enabled:
                role_dist[role] += 1
    license_dist = Counter(str(r.get("license")) for r in rows)

    report = {
        "schema_name": READINESS_SCHEMA_NAME,
        "schema_version": READINESS_SCHEMA_VERSION,
        "catalog_id": data.get("catalog_id"),
        "catalog_schema_name": data.get("schema_name"),
        "catalog_schema_version": data.get("schema_version"),
        "catalog_path": CATALOG_RELATIVE_PATH,
        "release_scope": data.get("release_scope")
        or {
            "release": "v0.2.0",
            "curated_repository_count": target,
            "note": RELEASE_SCOPE_NOTE,
        },
        "target_repository_count": target,
        "actual_repository_count": len(rows),
        "qualified_repository_count": len(qualified),
        "blocked_repository_count": len(blocked_entries),
        "sv10_enabled_repository_count": len(sv10),
        "sv10_qualified_repository_count": len(sv10_qualified),
        "unqualified_repository_ids": unqualified,
        "blocked_repository_ids": [r["repository_id"] for r in blocked_entries],
        "sv10_enabled_repository_ids": [r["repository_id"] for r in sv10],
        "language_distribution": dict(sorted(lang_dist.items())),
        "ecosystem_distribution": dict(sorted(eco_dist.items())),
        "tier_distribution": dict(sorted(tier_dist.items())),
        "role_distribution": dict(sorted(role_dist.items())),
        "license_distribution": dict(sorted(license_dist.items())),
        "coverage_matrix": coverage_matrix(rows),
        "repository_assignments": rows,
        "qualification_checks": checks,
        "execution_batches": build_execution_batches(rows),
        "import_template": build_import_template(missing_count=missing_count),
        "owner_supplied_outside_catalog": list(OWNER_SUPPLIED_OUTSIDE_CATALOG),
        "vinay_eight_candidates_present": False,
        "sv6_preferred_subset": list(SV6_PREFERRED_SUBSET),
        "blockers": blockers,
        "warnings": warnings,
        "limitations": limitations,
        "verdict": verdict,
        "sv10_execution_started": False,
        "sv11_started": False,
    }
    return report


def write_readiness_report(repo_root: Path, output: Path | None = None) -> Path:
    data = load_catalog_document(repo_root)
    report = build_readiness_report(data)
    out = output or (
        catalog_path(repo_root).parent / "repository-catalog-readiness.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def write_import_template(repo_root: Path, output: Path | None = None) -> Path:
    data = load_catalog_document(repo_root)
    target = release_validation_target(data)
    actual = len(data.get("repositories") or [])
    missing = max(0, target - actual)
    template = build_import_template(missing_count=missing)
    out = output or (
        catalog_path(repo_root).parent / "candidate-import-template.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(template, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out
