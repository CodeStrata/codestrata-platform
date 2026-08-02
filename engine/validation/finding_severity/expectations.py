"""Structured Finding severity expectations for Epic 4 fixtures (Slice 5.13)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from codestrata.domain.graph.validation import as_tuple, require_nonblank


_SEVERITY_RANK = {
    "informational": 0,
    "info": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


class ForbiddenSeverityPrefix(BaseModel):
    """Forbid severities for Findings whose rule_id starts with a prefix."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    prefix: str
    severities: tuple[str, ...]
    rationale: str | None = None

    @field_validator("prefix", mode="before")
    @classmethod
    def normalize_prefix(cls, value: object) -> str:
        return require_nonblank(str(value), label="prefix").strip().lower()

    @field_validator("severities", mode="before")
    @classmethod
    def normalize_severities(cls, value: object) -> tuple[str, ...]:
        items = tuple(
            sorted(
                {
                    require_nonblank(str(item), label="severity").strip().lower()
                    for item in as_tuple(value)
                }
            )
        )
        unknown = [item for item in items if item not in _SEVERITY_RANK]
        if unknown:
            raise ValueError(f"unknown severities: {unknown}")
        return items


class FindingSeverityExpectation(BaseModel):
    """Optional repository-level severity constraints."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    forbidden_severity_prefixes: tuple[ForbiddenSeverityPrefix, ...] = ()
    notes: str | None = None

    @field_validator("forbidden_severity_prefixes", mode="before")
    @classmethod
    def normalize_prefixes(cls, value: object) -> tuple[Any, ...]:
        return tuple(as_tuple(value))


def compare_finding_severity_expectations(
    *,
    expectation: FindingSeverityExpectation,
    findings: list[dict[str, Any]],
) -> list[str]:
    """Return mismatch diagnostics for forbidden severity/prefix pairs."""

    mismatches: list[str] = []
    for item in expectation.forbidden_severity_prefixes:
        forbidden = set(item.severities)
        for finding in findings:
            if not isinstance(finding, dict):
                continue
            rule_id = str(finding.get("rule_id") or "").strip().lower()
            severity = str(finding.get("severity") or "").strip().lower()
            if not rule_id or not severity:
                continue
            if rule_id.startswith(item.prefix) and severity in forbidden:
                mismatches.append(
                    f"forbidden severity {severity!r} for {rule_id} "
                    f"(prefix {item.prefix!r})"
                )
    return mismatches
