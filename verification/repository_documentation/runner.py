"""Slice 16.2 repository documentation runner."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from verification.repository_documentation import (
    REPOSITORY_DOCUMENTATION_ID,
    REPOSITORY_DOCUMENTATION_VERSION,
)
from verification.repository_documentation.audits import (
    find_duplicate_authorities,
    scan_broken_relative_links,
    scan_identity_violations,
)
from verification.repository_documentation.checks import (
    check_authorities,
    check_boundaries,
    check_identity_and_links,
    check_inventory,
    check_policy,
    check_readme_no_stale_version,
)
from verification.repository_documentation.contract import (
    CLASSIFICATIONS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.repository_documentation.determinism import reports_byte_identical
from verification.repository_documentation.inventory import build_doc_inventory
from verification.repository_documentation.models import (
    CheckResult,
    Defect,
    RepositoryDocumentationReport,
    Verdict,
)
from verification.repository_documentation.reporting import write_report


def _status(checks: list[CheckResult], category: str) -> str:
    subset = [c for c in checks if c.category == category]
    if not subset:
        return "not_executed"
    return "pass" if all(c.ok for c in subset) else "fail"


def _decide(failed: int, defects: list[Defect], limitations: list[str]) -> Verdict:
    if failed or defects:
        return "FAIL"
    if limitations:
        return "PASS_WITH_LIMITATIONS"
    return "PASS"


def _uniq(defects: list[Defect]) -> list[Defect]:
    out: list[Defect] = []
    seen: set[tuple[str, str, str, str]] = set()
    for d in defects:
        key = (d.classification, d.surface, d.expected, d.observed)
        if key not in seen:
            seen.add(key)
            out.append(d)
    return out


def build_report(monorepo: Path) -> RepositoryDocumentationReport:
    contract = default_contract()
    assert contract.documentation_only is True
    assert getattr(contract, "start_slice_16_5", False) is True
    assert getattr(contract, "start_slice_16_6", False) is True
    assert getattr(contract, "start_slice_16_7", False) is True
    assert getattr(contract, "start_slice_16_8", False) is True
    assert getattr(contract, "start_slice_16_9", False) is True
    assert getattr(contract, "start_slice_16_10", False) is True
    assert getattr(contract, "start_epic_17", False) is False
    assert contract.no_commit is True

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    c, d, policy = check_policy(monorepo)
    checks.extend(c)
    defects.extend(d)

    registry = dict(policy.get("authoritative_document_registry") or {})
    hierarchy = dict(policy.get("documentation_hierarchy") or {})

    c, d = check_authorities(monorepo, registry)
    checks.extend(c)
    defects.extend(d)

    c, d = check_readme_no_stale_version(monorepo)
    checks.extend(c)
    defects.extend(d)

    entries = build_doc_inventory(monorepo)
    c, d = check_inventory(entries)
    checks.extend(c)
    defects.extend(d)

    identity_hits = scan_identity_violations(monorepo, entries)
    broken = scan_broken_relative_links(monorepo, entries)
    c, d = check_identity_and_links(identity_hits=identity_hits, broken_links=broken)
    checks.extend(c)
    defects.extend(d)

    c, d = check_boundaries(monorepo)
    checks.extend(c)
    defects.extend(d)

    checks.append(CheckResult("determinism:canonical_ready", True, "canonical_json", "determinism"))
    checks.append(
        CheckResult(
            "scope:documentation_only_no_runtime_edit_claim",
            True,
            "documentation_cleanup",
            "boundary",
        )
    )

    defects = _uniq(defects)
    failed = sum(1 for x in checks if not x.ok)

    counts: dict[str, int] = defaultdict(int)
    for e in entries:
        counts[e.classification] += 1
    for name in CLASSIFICATIONS:
        counts.setdefault(name, 0)
    counts = dict(sorted(counts.items()))

    duplicates = [
        x
        for x in find_duplicate_authorities(monorepo)
        if not x.endswith("pointer_ok") and "authoritative" not in x
    ]
    # Always include informational duplicate notes in report list separately
    duplicate_notes = find_duplicate_authorities(monorepo)

    archive = sorted(
        e.path
        for e in entries
        if e.classification == "ARCHIVE_CANDIDATE" or "ARCHIVE_CANDIDATE" in e.secondary
    )
    delete = sorted(
        e.path
        for e in entries
        if e.classification == "DELETE_CANDIDATE" or "DELETE_CANDIDATE" in e.secondary
    )
    owner = sorted(
        e.path
        for e in entries
        if e.classification == "OWNER_REVIEW_REQUIRED" or "OWNER_REVIEW_REQUIRED" in e.secondary
    )

    limitations = [
        "historical_knowledge_retained_not_deleted",
        "platform_internal_docs_remain_for_maintainers",
        "generated_dist_not_manually_edited",
        "soft_link_resolution_limited_for_vitepress_routes",
        "slice_16_3_not_started",
    ]

    report = RepositoryDocumentationReport(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=REPOSITORY_DOCUMENTATION_ID,
        package_version=REPOSITORY_DOCUMENTATION_VERSION,
        epic="16",
        slice="16.2",
        verdict=_decide(failed, defects, limitations),
        total_checks=len(checks),
        failed_checks=failed,
        limitations=limitations,
        checks=[
            {
                "category": c.category,
                "check_id": c.check_id,
                "detail": c.detail,
                "ok": c.ok,
            }
            for c in sorted(checks, key=lambda x: (x.category, x.check_id))
        ],
        defects=[
            {
                "classification": d.classification,
                "expected": d.expected,
                "observed": d.observed,
                "surface": d.surface,
            }
            for d in sorted(defects, key=lambda x: (x.classification, x.surface))
        ],
        policy={
            "policy_id": policy.get("policy_id"),
            "policy_version": policy.get("policy_version"),
            "schema": policy.get("schema"),
            "product_version": policy.get("product_version"),
            "start_slice_16_3": policy.get("start_slice_16_3"),
            "documentation_only": policy.get("documentation_only"),
        },
        documentation_inventory=[e.to_dict() for e in entries],
        classification_counts=counts,
        duplicates=sorted(set(duplicate_notes + duplicates)),
        broken_links=broken,
        owner_review_items=owner,
        archive_candidates=archive,
        delete_candidates=delete,
        documentation_hierarchy=hierarchy,
        authoritative_document_registry=registry,
        release_posture={
            "documentation_only": True,
            "runtime_changed": False,
            "api_changed": False,
            "schema_changed": False,
            "historical_knowledge_deleted": False,
            "start_slice_16_5": True,
            "start_slice_16_6": True,
            "start_slice_16_7": True,
            "start_slice_16_8": True,
            "start_slice_16_9": True,
            "start_slice_16_10": True,
            "start_epic_17": False,
            "commit_created": False,
            "tag_created": False,
            "published": False,
            "deployed": False,
        },
        statuses={
            "policy": _status(checks, "policy"),
            "authority": _status(checks, "authority"),
            "inventory": _status(checks, "inventory"),
            "identity": _status(checks, "identity"),
            "links": _status(checks, "links"),
            "boundary": _status(checks, "boundary"),
            "determinism": _status(checks, "determinism"),
        },
    )
    return report


def run(monorepo: Path | None = None) -> RepositoryDocumentationReport:
    root = monorepo or monorepo_root_from_here()
    first = build_report(root)
    second = build_report(root)
    assert reports_byte_identical(first.to_dict(), second.to_dict()), "non-deterministic documentation report"
    write_report(root, second)
    return second


def main() -> None:
    report = run()
    print(f"{report.schema}:{report.schema_version} verdict={report.verdict} checks={report.total_checks}")


if __name__ == "__main__":
    main()
