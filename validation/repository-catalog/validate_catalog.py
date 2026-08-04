"""Permanent repository catalog validation and qualification helpers.

Single source of truth: ``validation/repository-catalog/catalog.json``.
This package does not invent repository lists or change product behavior.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

CATALOG_RELATIVE_PATH = "validation/repository-catalog/catalog.json"
CATALOG_SCHEMA_NAME = "codestrata-repository-catalog"
CATALOG_SCHEMA_VERSION = "1.0.0"
QUALIFICATION_REPORT_SCHEMA = "repository-catalog-qualification"
QUALIFICATION_REPORT_VERSION = "1.0.0"

FULL_COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")
FLOATING = frozenset(
    {
        "main",
        "master",
        "head",
        "default",
        "latest",
        "origin/main",
        "origin/master",
    }
)
ACCEPTED_REVISION_TYPES = frozenset({"commit", "tag"})
ENABLED_FOR_REQUIRED_KEYS = (
    "smoke",
    "regression",
    "engineering_intelligence",
    "performance",
    "release_validation",
)
SUPPORTED_LANGUAGE_GROUPS = frozenset(
    {"C#/.NET", "Java", "JS/TS", "PHP", "Python", None}
)
RUNTIME_TIERS = frozenset({"tier1", "tier2", "tier3", "tier4"})
DEFAULT_RELEASE_VALIDATION_TARGET = 22


@dataclass(frozen=True, slots=True)
class CatalogIssue:
    code: str
    message: str
    repository_id: str | None = None


@dataclass
class CatalogValidationResult:
    ok: bool = True
    issues: list[CatalogIssue] = field(default_factory=list)

    def error(self, code: str, message: str, repository_id: str | None = None) -> None:
        self.ok = False
        self.issues.append(CatalogIssue(code, message, repository_id))


def catalog_path(repo_root: Path) -> Path:
    path = repo_root / CATALOG_RELATIVE_PATH
    if path.is_file():
        return path
    alt = repo_root.parent / CATALOG_RELATIVE_PATH
    if alt.is_file():
        return alt
    raise FileNotFoundError(CATALOG_RELATIVE_PATH)


def load_catalog_document(repo_root: Path) -> dict[str, Any]:
    return json.loads(catalog_path(repo_root).read_text(encoding="utf-8"))


def is_full_commit_sha(value: str) -> bool:
    return bool(FULL_COMMIT_SHA.match(value.strip().lower())) and value == value.lower()


def is_floating_revision(value: str) -> bool:
    return value.strip().lower() in FLOATING


def validate_github_https_url(url: str, github_repository: str) -> list[str]:
    errors: list[str] = []
    parsed = urlparse(url.strip())
    if parsed.scheme != "https":
        errors.append("url_scheme_must_be_https")
    if parsed.username or parsed.password or "@" in url.split("://", 1)[-1].split("/", 1)[0]:
        errors.append("credentials_in_url_forbidden")
    if parsed.hostname not in {"github.com", "www.github.com"}:
        errors.append("host_must_be_github_com")
    expected_path = f"/{github_repository}".rstrip("/")
    actual = (parsed.path or "").rstrip("/")
    if actual != expected_path and actual != f"{expected_path}.git":
        errors.append("url_owner_repo_mismatch")
    return errors


def validate_qualified_revision(raw: Any, *, repository_id: str) -> list[CatalogIssue]:
    issues: list[CatalogIssue] = []
    if raw is None:
        return issues
    if not isinstance(raw, dict):
        return [
            CatalogIssue(
                "qualified_revision_type",
                "qualified_revision must be null or an object",
                repository_id,
            )
        ]
    rtype = str(raw.get("type") or "").strip().lower()
    value = str(raw.get("value") or "").strip()
    if rtype not in ACCEPTED_REVISION_TYPES:
        issues.append(
            CatalogIssue(
                "revision_type_invalid",
                f"type must be commit|tag, got {rtype!r}",
                repository_id,
            )
        )
    if not value:
        issues.append(CatalogIssue("revision_value_missing", "value required", repository_id))
        return issues
    if is_floating_revision(value):
        issues.append(
            CatalogIssue(
                "floating_revision_forbidden",
                f"floating revision forbidden: {value}",
                repository_id,
            )
        )
    if rtype == "commit":
        if not FULL_COMMIT_SHA.match(value):
            issues.append(
                CatalogIssue(
                    "commit_sha_invalid",
                    "commit value must be a full 40-character hexadecimal SHA",
                    repository_id,
                )
            )
        elif value != value.lower():
            issues.append(
                CatalogIssue(
                    "commit_sha_not_lowercase",
                    "commit SHA must be lowercase",
                    repository_id,
                )
            )
    if rtype == "tag" and is_floating_revision(value):
        issues.append(
            CatalogIssue(
                "floating_tag_forbidden",
                "tag must not be a floating branch name",
                repository_id,
            )
        )
    source_tag = raw.get("source_tag")
    if source_tag is not None and not isinstance(source_tag, str):
        issues.append(
            CatalogIssue(
                "source_tag_invalid",
                "source_tag must be a string when present",
                repository_id,
            )
        )
    # Prefer commit as authoritative; tag-only is allowed by revision_policy but
    # SV.4A records commit SHAs.
    return issues


def validate_catalog_document(data: MappingLike) -> CatalogValidationResult:
    result = CatalogValidationResult()
    if data.get("schema_name") != CATALOG_SCHEMA_NAME:
        result.error("schema_name", f"expected {CATALOG_SCHEMA_NAME}")
    if data.get("schema_version") != CATALOG_SCHEMA_VERSION:
        result.error("schema_version", f"expected {CATALOG_SCHEMA_VERSION}")
    if not data.get("catalog_id"):
        result.error("catalog_id_missing", "catalog_id required")

    repos = data.get("repositories")
    if not isinstance(repos, list) or not repos:
        result.error("repositories_missing", "repositories must be a non-empty list")
        return result

    ids: set[str] = set()
    githubs: set[str] = set()
    for item in repos:
        if not isinstance(item, dict):
            result.error("repository_not_object", "repository entry must be an object")
            continue
        rid = str(item.get("id") or "").strip()
        if not rid:
            result.error("id_missing", "repository id required")
            continue
        if rid in ids:
            result.error("duplicate_id", f"duplicate id {rid}", rid)
        ids.add(rid)
        name = str(item.get("project_name") or "").strip()
        if not name:
            result.error("project_name_missing", "project_name required", rid)
        gh = str(item.get("github_repository") or "").strip()
        if not gh or "/" not in gh:
            result.error("github_repository_invalid", "owner/name required", rid)
        elif gh in githubs:
            result.error("duplicate_github_repository", f"duplicate {gh}", rid)
        else:
            githubs.add(gh)
        url = str(item.get("github_url") or "").strip()
        for code in validate_github_https_url(url, gh):
            result.error(code, code, rid)
        enabled = item.get("enabled_for")
        if not isinstance(enabled, dict):
            result.error("enabled_for_invalid", "enabled_for must be an object", rid)
        else:
            for key in ENABLED_FOR_REQUIRED_KEYS:
                if key not in enabled:
                    result.error("enabled_for_missing_key", f"missing {key}", rid)
                elif not isinstance(enabled[key], bool):
                    result.error("enabled_for_not_bool", f"{key} must be bool", rid)
        lang = item.get("language_group")
        if lang is not None and lang not in SUPPORTED_LANGUAGE_GROUPS - {None}:
            result.error(
                "language_group_unsupported",
                f"unsupported language_group {lang!r}",
                rid,
            )
        tier = item.get("expected_runtime_tier")
        if tier is not None and tier not in RUNTIME_TIERS:
            result.error(
                "runtime_tier_invalid",
                f"expected_runtime_tier must be one of {sorted(RUNTIME_TIERS)}",
                rid,
            )
        for issue in validate_qualified_revision(
            item.get("qualified_revision"), repository_id=rid
        ):
            result.issues.append(issue)
            result.ok = False

        # SV.10-enabled entries must be fully pinned commits (not tag-only).
        if isinstance(enabled, dict) and enabled.get("release_validation"):
            rev = item.get("qualified_revision")
            if not isinstance(rev, dict) or str(rev.get("type") or "").lower() != "commit":
                result.error(
                    "sv10_requires_commit_pin",
                    "release_validation requires qualified_revision.type=commit",
                    rid,
                )
            elif not FULL_COMMIT_SHA.match(str(rev.get("value") or "")):
                result.error(
                    "sv10_requires_full_sha",
                    "release_validation requires a full 40-character commit SHA",
                    rid,
                )

    target = data.get("release_validation_target", DEFAULT_RELEASE_VALIDATION_TARGET)
    if not isinstance(target, int) or target < 1:
        result.error(
            "release_validation_target_invalid",
            "release_validation_target must be a positive integer",
        )

    # Forbidden content in catalog identity material.
    blob = json.dumps(data, sort_keys=True)
    for needle, code in (
        ("/Users/", "absolute_path"),
        ("/home/", "absolute_path"),
        ("AKIA", "secret_shaped"),
        ("cscc_v1_", "secret_shaped"),
    ):
        if needle in blob:
            result.error(code, f"forbidden content: {code}")
    return result


# Typing alias without importing Mapping to keep file light for scripts.
MappingLike = dict[str, Any]


def serialize_catalog(data: dict[str, Any]) -> str:
    """Deterministic JSON serialization for the permanent catalog."""

    return json.dumps(data, indent=4, ensure_ascii=False) + "\n"


def build_qualification_report(data: dict[str, Any]) -> dict[str, Any]:
    """Privacy-safe deterministic qualification report (no local paths/timestamps)."""

    entries = []
    for item in data.get("repositories") or []:
        if not isinstance(item, dict):
            continue
        rev = item.get("qualified_revision")
        qualified = isinstance(rev, dict) and rev.get("type") and rev.get("value")
        enabled = item.get("enabled_for") or {}
        entries.append(
            {
                "repository_id": item.get("id"),
                "github_repository": item.get("github_repository"),
                "project_name": item.get("project_name"),
                "candidate_category": item.get("candidate_category"),
                "language_group": item.get("language_group"),
                "qualified_revision": rev if qualified else None,
                "source_tag": (rev or {}).get("source_tag") if isinstance(rev, dict) else None,
                "revision_verification_status": "pinned" if qualified else "unqualified",
                "clone_status": "verified_at_qualification" if qualified else "not_attempted",
                "checkout_status": "detached_sha_verified" if qualified else "not_attempted",
                "smoke_eligibility": bool(enabled.get("smoke")) and bool(qualified),
                "limitations": (
                    []
                    if qualified
                    else ["qualified_revision is null; not eligible for repeatable automated runs"]
                ),
                "verdict": "qualified" if qualified else "unqualified",
            }
        )
    entries.sort(key=lambda row: str(row.get("repository_id") or ""))
    qualified_count = sum(1 for row in entries if row["verdict"] == "qualified")
    return {
        "schema_name": QUALIFICATION_REPORT_SCHEMA,
        "schema_version": QUALIFICATION_REPORT_VERSION,
        "catalog_id": data.get("catalog_id"),
        "catalog_path": CATALOG_RELATIVE_PATH,
        "qualified_count": qualified_count,
        "unqualified_count": len(entries) - qualified_count,
        "repositories": entries,
        "limitations": list(data.get("limitations") or []),
        "verdict": "pass" if qualified_count > 0 else "fail_qualification_gap",
    }


def write_qualification_report(repo_root: Path, output: Path | None = None) -> Path:
    data = load_catalog_document(repo_root)
    report = build_qualification_report(data)
    out = output or (repo_root / "validation" / "repository-catalog" / "qualification-report.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate the permanent CodeStrata repository catalog (SV.4A / SV.10A)."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Monorepo root (default: discover from this file).",
    )
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Write privacy-safe qualification-report.json",
    )
    parser.add_argument(
        "--write-readiness-report",
        action="store_true",
        help="Write SV.10A repository-catalog-readiness.json",
    )
    parser.add_argument(
        "--write-import-template",
        action="store_true",
        help="Write candidate-import-template.json for missing slots",
    )
    args = parser.parse_args(argv)
    root = args.repo_root
    if root is None:
        root = Path(__file__).resolve().parents[2]

    data = load_catalog_document(root)
    result = validate_catalog_document(data)
    if result.ok:
        print("catalog validation: OK")
    else:
        print("catalog validation: FAIL")
        for issue in result.issues:
            loc = f" [{issue.repository_id}]" if issue.repository_id else ""
            print(f"  - {issue.code}{loc}: {issue.message}")

    if args.write_report:
        path = write_qualification_report(root)
        print(f"qualification report: {path.as_posix()}")

    if args.write_readiness_report or args.write_import_template:
        from readiness import write_import_template, write_readiness_report

        if args.write_readiness_report:
            path = write_readiness_report(root)
            report = json.loads(path.read_text(encoding="utf-8"))
            print(f"readiness report: {path.as_posix()}")
            print(f"readiness verdict: {report.get('verdict')}")
        if args.write_import_template:
            path = write_import_template(root)
            print(f"import template: {path.as_posix()}")

    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
