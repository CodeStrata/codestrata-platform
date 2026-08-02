"""Additive required/forbidden Finding correlation expectations (Slice 5.12).

Does not change validation record/summary schema versions. Expectations are
rule-pair oriented so they remain stable across Finding ID generation.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from codestrata.domain.graph.validation import as_tuple, require_nonblank


class FindingCorrelationPairExpectation(BaseModel):
    """One required or forbidden correlation between two rule IDs."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_ids: tuple[str, ...]
    correlation_type: str | None = None
    rationale: str | None = None

    @field_validator("rule_ids", mode="before")
    @classmethod
    def normalize_rules(cls, value: object) -> tuple[str, ...]:
        items = tuple(
            sorted(
                {
                    require_nonblank(str(item), label="rule_id").strip()
                    for item in as_tuple(value)
                }
            )
        )
        if len(items) != 2:
            raise ValueError("correlation pair expectation requires exactly two rule_ids")
        return items


class FindingCorrelationExpectation(BaseModel):
    """Optional correlation expectations for one validation repository."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    required_correlations: tuple[FindingCorrelationPairExpectation, ...] = ()
    forbidden_correlations: tuple[FindingCorrelationPairExpectation, ...] = ()
    notes: str | None = None

    @field_validator("required_correlations", "forbidden_correlations", mode="before")
    @classmethod
    def normalize_pairs(cls, value: object) -> tuple[Any, ...]:
        return tuple(as_tuple(value))


def pair_key(rule_a: str, rule_b: str) -> str:
    return "|".join(sorted((rule_a.strip(), rule_b.strip())))


def extract_correlation_pair_keys(
    *,
    findings: list[dict[str, Any]],
    correlations: list[dict[str, Any]],
) -> tuple[str, ...]:
    """Derive stable rule-pair keys from report finding_correlations."""

    by_id = {
        str(item.get("id")): str(item.get("rule_id") or "")
        for item in findings
        if isinstance(item, dict) and item.get("id") and item.get("rule_id")
    }
    keys: set[str] = set()
    for item in correlations:
        if not isinstance(item, dict):
            continue
        members = [str(fid) for fid in (item.get("finding_ids") or []) if fid]
        rules = sorted({by_id[fid] for fid in members if fid in by_id and by_id[fid]})
        if len(rules) >= 2:
            # Pairwise among distinct rules in the correlation.
            for i, left in enumerate(rules):
                for right in rules[i + 1 :]:
                    keys.add(pair_key(left, right))
    return tuple(sorted(keys))


def compare_correlation_expectations(
    *,
    expectation: FindingCorrelationExpectation,
    actual_pair_keys: tuple[str, ...],
) -> list[str]:
    """Return human-readable mismatch diagnostics (empty when OK)."""

    actual = set(actual_pair_keys)
    mismatches: list[str] = []
    for item in expectation.required_correlations:
        key = pair_key(*item.rule_ids)
        if key not in actual:
            mismatches.append(f"missing required correlation {key}")
    for item in expectation.forbidden_correlations:
        key = pair_key(*item.rule_ids)
        if key in actual:
            mismatches.append(f"forbidden correlation present {key}")
    return mismatches
