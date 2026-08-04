"""Negative scenario helpers for SV.12 tests (fixtures only)."""

from __future__ import annotations

import copy
from typing import Any


def minimal_eir_payload(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "schema_version": "1.0",
        "report_id": "eir:fixture",
        "interpretation_policy_bundle_id": "interp-bundle:fixture",
        "report_scope": "public_oss_dataset",
        "title": "Fixture EIR",
        "dataset": {"dataset_id": "dataset:fixture", "repositories": []},
        "repository_population": {
            "repositories": [{"repository_id": f"repo:r{i}"} for i in range(1, 23)]
        },
        "technology_distribution": {"observations": []},
        "capability_comparisons": [],
        "assessment_head_distributions": [],
        "recurring_patterns": [
            {
                "pattern_id": "pat:1",
                "repository_ids": ["repo:r1", "repo:r2"],
                "rule_id": "rule:x",
                "statement": "Within this dataset, observed in 2 of 22 eligible repositories.",
            }
        ],
        "modernization_observations": [
            {
                "observation_id": "mod:1",
                "repository_ids": ["repo:r1", "repo:r2"],
                "supporting_recommendation_ids": ["rec:1"],
                "statement": "Recommendations were produced for related themes within this dataset.",
            }
        ],
        "confidence": {"level": "limited"},
        "limitations": [
            {"statement": "Curated public OSS dataset; not an industry benchmark."},
            {"statement": "Pinned revisions only."},
        ],
        "repository_drilldowns": [
            {"repository_id": f"repo:r{i}", "pinned_revision": "a" * 40} for i in range(1, 23)
        ],
        "executive_summary": "Within this dataset...",
        "methodology": "Deterministic aggregation; does not establish product-wide accuracy.",
    }
    base.update(overrides)
    return base


def mutate_single_repo_pattern(payload: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(payload)
    out["recurring_patterns"] = [
        {
            "pattern_id": "pat:bad",
            "repository_ids": ["repo:r1"],
            "rule_id": "rule:x",
            "statement": "Observed once",
        }
    ]
    return out


def mutate_observation_without_recommendations(payload: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(payload)
    out["modernization_observations"] = [
        {
            "observation_id": "mod:bad",
            "repository_ids": ["repo:r1", "repo:r2"],
            "supporting_recommendation_ids": [],
            "statement": "Migrate everything",
        }
    ]
    return out


def mutate_maturity_ranking(payload: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(payload)
    out["capability_comparisons"] = [{"statement": "Repository maturity score ranking"}]
    return out


def mutate_industry_benchmark_claim(payload: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(payload)
    out["executive_summary"] = "This is an industry benchmark for engineering quality."
    return out
