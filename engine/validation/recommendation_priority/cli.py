"""Read-only Recommendation priority calibration diagnostics.

Usage::

    python -m validation.recommendation_priority --changed-only
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from validation.paths import RESULTS_DIR
from validation.recording import (
    list_run_ids,
    load_repository_validation_record,
    repository_records_root,
)
from validation.summary_from_records import list_repository_ids_with_records

_PRIORITY_RANK = {
    "immediate": 3,
    "critical": 3,
    "high": 2,
    "medium": 1,
    "low": 0,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m validation.recommendation_priority",
        description="Internal Recommendation priority diagnostics (read-only).",
    )
    parser.add_argument("--records-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--repository")
    parser.add_argument("--provider")
    parser.add_argument("--head")
    parser.add_argument("--priority")
    parser.add_argument("--policy")
    parser.add_argument("--changed-only", action="store_true")
    parser.add_argument("--provisional", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    repositories = list_repository_ids_with_records(records_root=args.records_dir)
    if args.repository:
        repositories = tuple(item for item in repositories if item == args.repository)

    rows: list[dict] = []
    summary = {
        "recommendations_evaluated": 0,
        "unchanged_count": 0,
        "increased_count": 0,
        "decreased_count": 0,
        "provisional_count": 0,
        "legacy_count": 0,
        "by_provider": Counter(),
        "by_head": Counter(),
        "by_priority": Counter(),
        "confidence_cap_count": 0,
        "correlation_adjustment_count": 0,
        "phase_change_count": 0,
        "bucket_change_count": 0,
        "unsupported_high_priority_count": 0,
    }

    for repository_id in repositories:
        run_ids = list_run_ids(repository_id, records_root=args.records_dir)
        if not run_ids:
            continue
        record_dir = (
            repository_records_root(repository_id, records_root=args.records_dir)
            / "runs"
            / run_ids[-1]
        )
        try:
            record = load_repository_validation_record(record_dir)
        except Exception as exc:  # noqa: BLE001
            print(f"skip {repository_id}: {exc}", file=sys.stderr)
            continue
        actual = getattr(record, "actual", None) or {}
        recommendations = (
            actual.get("deterministic_recommendations")
            if isinstance(actual, dict)
            else None
        )
        if not isinstance(recommendations, list):
            recommendations = actual.get("recommendations") if isinstance(actual, dict) else None
        if not isinstance(recommendations, list):
            continue
        for item in recommendations:
            if not isinstance(item, dict):
                continue
            assessment = item.get("priority_assessment")
            if not isinstance(assessment, dict):
                assessment = {}
            priority = str(assessment.get("priority") or item.get("priority") or "").lower()
            provider = str(item.get("provider_id") or item.get("rule_id") or "")
            policy_id = str(assessment.get("policy_id") or "")
            status = str(assessment.get("calibration_status") or "")
            category = str(item.get("category") or "").lower()
            basis = assessment.get("basis") if isinstance(assessment.get("basis"), list) else []

            if args.provider and args.provider not in provider:
                continue
            if args.priority and args.priority.lower() != priority:
                continue
            if args.policy and args.policy not in policy_id:
                continue
            if args.head and args.head.lower() not in category:
                continue
            if args.provisional and status not in {"provisional", "legacy"}:
                continue

            previous = str(item.get("priority") or "").lower()
            # When assessment present, compatibility priority should match; "change"
            # vs provider seed is not recoverable from payload alone — treat
            # provisional/legacy as changed diagnostics.
            changed = status in {"provisional", "legacy"} or (
                assessment.get("component_summary", {}) or {}
            ).get("base_score") != assessment.get("score")
            if args.changed_only and not changed:
                continue

            summary["recommendations_evaluated"] += 1
            summary["by_provider"][provider or "unknown"] += 1
            summary["by_head"][category or "unknown"] += 1
            summary["by_priority"][priority or "unknown"] += 1
            if status == "provisional":
                summary["provisional_count"] += 1
            if status == "legacy":
                summary["legacy_count"] += 1
            if "confidence_cap" in basis:
                summary["confidence_cap_count"] += 1
            if "correlated_supporting_findings" in basis:
                summary["correlation_adjustment_count"] += 1
            if category in {"cloud", "cloud_readiness", "ai_readiness", "testing", "performance"} and priority in {
                "high",
                "immediate",
                "critical",
            }:
                summary["unsupported_high_priority_count"] += 1

            prev_rank = _PRIORITY_RANK.get(previous, -1)
            new_rank = _PRIORITY_RANK.get(priority, -1)
            if new_rank == prev_rank:
                summary["unchanged_count"] += 1
            elif new_rank > prev_rank:
                summary["increased_count"] += 1
            else:
                summary["decreased_count"] += 1

            rows.append(
                {
                    "repository": repository_id,
                    "recommendation_id": item.get("id"),
                    "provider_id": provider,
                    "category": category,
                    "priority": priority,
                    "score": assessment.get("score"),
                    "policy_id": policy_id,
                    "calibration_status": status,
                    "basis": basis,
                    "presentation_bucket": item.get("presentation_bucket"),
                }
            )

    payload = {
        "summary": {
            **{k: (dict(v) if isinstance(v, Counter) else v) for k, v in summary.items()}
        },
        "rows": rows,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        s = payload["summary"]
        print(
            "recommendations_evaluated={recommendations_evaluated} "
            "unchanged={unchanged_count} increased={increased_count} "
            "decreased={decreased_count} provisional={provisional_count} "
            "legacy={legacy_count} confidence_caps={confidence_cap_count} "
            "correlation_adj={correlation_adjustment_count} "
            "unsupported_high={unsupported_high_priority_count}".format(**s)
        )
        for row in rows[:50]:
            print(
                f"{row['repository']}\t{row['priority']}\t{row['score']}\t"
                f"{row['policy_id']}\t{row['recommendation_id']}"
            )
        if len(rows) > 50:
            print(f"... {len(rows) - 50} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
