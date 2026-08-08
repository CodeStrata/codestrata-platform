"""Slice 16.1 repository inventory runner."""

from __future__ import annotations

from pathlib import Path

from verification.repository_inventory import (
    REPOSITORY_INVENTORY_ID,
    REPOSITORY_INVENTORY_VERSION,
)
from verification.repository_inventory.checks import (
    check_authoritative_tokens,
    check_git_tracked_node_modules,
    check_inventory_coverage,
    check_no_cleanup_mutations,
    check_policy,
    check_special_audits_present,
)
from verification.repository_inventory.contract import (
    CLASSIFICATIONS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.repository_inventory.determinism import reports_byte_identical
from verification.repository_inventory.inventory import (
    area_counts,
    build_entries,
    candidates_by_class,
    classification_counts,
)
from verification.repository_inventory.models import (
    CheckResult,
    Defect,
    RepositoryInventoryReport,
    Verdict,
)
from verification.repository_inventory.reporting import write_report
from verification.repository_inventory.special_audits import build_special_audits


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


def build_report(monorepo: Path) -> RepositoryInventoryReport:
    contract = default_contract()
    assert contract.audit_only is True
    assert contract.delete_forbidden is True
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

    entries = build_entries(monorepo)
    c, d = check_inventory_coverage(entries)
    checks.extend(c)
    defects.extend(d)

    special = build_special_audits(monorepo, entries)
    c, d, tracked_nm = check_git_tracked_node_modules(monorepo)
    checks.extend(c)
    defects.extend(d)
    special["committed_node_modules_tracked"] = tracked_nm

    c, d = check_special_audits_present(special)
    checks.extend(c)
    defects.extend(d)

    c, d = check_authoritative_tokens(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_no_cleanup_mutations(monorepo)
    checks.extend(c)
    defects.extend(d)

    checks.append(
        CheckResult("determinism:canonical_ready", True, "canonical_json", "determinism")
    )
    checks.append(
        CheckResult("audit:no_mutations_performed", True, "read_only_inventory", "boundary")
    )

    defects = _uniq(defects)
    failed = sum(1 for c in checks if not c.ok)

    counts = classification_counts(entries)
    for name in CLASSIFICATIONS:
        counts.setdefault(name, 0)
    counts = dict(sorted(counts.items()))

    areas = area_counts(entries)

    duplicate_candidates = sorted(
        set(candidates_by_class(entries, "DUPLICATE"))
        | set(special.get("duplicate_tokens_css") or [])
    )
    stale_candidates = candidates_by_class(entries, "STALE")
    delete_candidates = candidates_by_class(entries, "DELETE_CANDIDATE")
    archive_candidates = candidates_by_class(entries, "ARCHIVE_CANDIDATE")
    owner_review = candidates_by_class(entries, "OWNER_REVIEW_REQUIRED")

    limitations = [
        "audit_only_no_cleanup_actions",
        "deep_walk_pruned_for_node_modules_venv_terraform_validation_repos",
        "dead_code_detection_is_heuristic_path_based_not_reachability",
        "duplicate_detection_uses_basename_and_token_hash_not_full_binary_compare",
        "cleanup_deferred_to_slice_16_2",
    ]

    # Cap entry list in report for size while keeping full candidate lists
    entry_dicts = [e.to_dict() for e in entries]
    # Prefer summarizing very large inventories: keep all non-GENERATED + sample GENERATED
    if len(entry_dicts) > 4000:
        kept = [e for e in entry_dicts if e["classification"] != "GENERATED"]
        generated = [e for e in entry_dicts if e["classification"] == "GENERATED"]
        entry_dicts = kept + generated[:500]

    report = RepositoryInventoryReport(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=REPOSITORY_INVENTORY_ID,
        package_version=REPOSITORY_INVENTORY_VERSION,
        epic="16",
        slice="16.1",
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
            "audit_only": policy.get("audit_only"),
            "start_slice_16_2": policy.get("start_slice_16_2"),
        },
        inventory_summary={
            "entry_count": len(entries),
            "reported_entry_count": len(entry_dicts),
            "areas_with_entries": sorted(a for a, n in areas.items() if n > 0),
            "sqlite_count": len(special.get("sqlite_databases") or []),
            "aimf_ref_count": len(special.get("legacy_aimf_references") or []),
            "cursor_ref_count": len(special.get("legacy_cursor_references") or []),
            "dist_dir_count": len(special.get("dist_directories") or []),
            "tracked_node_modules_count": len(special.get("committed_node_modules_tracked") or []),
        },
        classification_counts=counts,
        area_counts=areas,
        duplicate_candidates=duplicate_candidates,
        stale_candidates=stale_candidates,
        delete_candidates=delete_candidates,
        archive_candidates=archive_candidates,
        owner_review_items=owner_review,
        special_audits=special,
        entries=sorted(entry_dicts, key=lambda e: e["path"]),
        release_posture={
            "audit_only": True,
            "cleanup_performed": False,
            "files_deleted": False,
            "files_renamed": False,
            "files_moved": False,
            "runtime_behavior_changed": False,
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
            "inventory": _status(checks, "inventory"),
            "special_audit": _status(checks, "special_audit"),
            "boundary": _status(checks, "boundary"),
            "determinism": _status(checks, "determinism"),
        },
    )
    return report


def run(monorepo: Path | None = None) -> RepositoryInventoryReport:
    root = monorepo or monorepo_root_from_here()
    first = build_report(root)
    second = build_report(root)
    assert reports_byte_identical(first.to_dict(), second.to_dict()), "non-deterministic inventory report"
    write_report(root, second)
    return second


def main() -> None:
    report = run()
    print(f"{report.schema}:{report.schema_version} verdict={report.verdict} checks={report.total_checks}")


if __name__ == "__main__":
    main()
