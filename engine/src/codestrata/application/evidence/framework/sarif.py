"""Narrow SARIF 2.1 normalizer preserving tool-native raw artifacts."""

from __future__ import annotations

from typing import Any

from codestrata.application.evidence.framework.collectors import CollectorContext
from codestrata.application.evidence.framework.sanitization import (
    sanitize_evidence_payload,
)
from codestrata.domain.evidence.framework.models import (
    Coverage,
    CoverageState,
    EvidenceEnvelope,
    EvidenceLocation,
    RawArtifactReference,
)


def _message_text(value: object) -> str:
    if isinstance(value, dict):
        text = value.get("text") or value.get("markdown")
        return str(text or "SARIF result")
    return str(value or "SARIF result")


def normalize_sarif_document(
    *,
    document: dict[str, Any],
    context: CollectorContext,
    collector_id: str = "import.sarif",
    collector_version: str = "1.0.0",
    raw_reference: RawArtifactReference | None = None,
) -> tuple[tuple[EvidenceEnvelope, ...], Coverage]:
    """Normalize the interoperable SARIF fields CodeStrata can faithfully preserve."""

    version = str(document.get("version", ""))
    if version != "2.1.0":
        raise ValueError(f"unsupported SARIF version {version!r}; expected '2.1.0'")
    runs = document.get("runs")
    if not isinstance(runs, list):
        raise ValueError("SARIF document must contain a runs array")
    evidence: list[EvidenceEnvelope] = []
    result_count = 0
    for run_index, run in enumerate(runs):
        if not isinstance(run, dict):
            continue
        driver = run.get("tool", {}).get("driver", {})
        tool_name = str(driver.get("name", "unknown-sarif-tool"))
        tool_version = str(
            driver.get("semanticVersion") or driver.get("version") or "unknown"
        )
        results = run.get("results", [])
        if not isinstance(results, list):
            continue
        for result_index, result in enumerate(results):
            if not isinstance(result, dict):
                continue
            result_count += 1
            locations: list[EvidenceLocation] = []
            for item in result.get("locations", []):
                physical = item.get("physicalLocation", {}) if isinstance(item, dict) else {}
                artifact = physical.get("artifactLocation", {})
                region = physical.get("region", {})
                uri = artifact.get("uri")
                if uri:
                    locations.append(
                        EvidenceLocation(
                            path=str(uri),
                            start_line=region.get("startLine"),
                            start_column=region.get("startColumn"),
                            end_line=region.get("endLine"),
                            end_column=region.get("endColumn"),
                        )
                    )
            fingerprints = result.get("partialFingerprints", {})
            suppressions = result.get("suppressions", [])
            coverage = Coverage(
                state=CoverageState.UNKNOWN,
                population="Population examined by the producing SARIF tool.",
                successful=True,
                limitations=(
                    "SARIF results do not by themselves prove complete source coverage.",
                ),
            )
            payload: dict[str, Any] = {
                "tool": tool_name,
                "tool_version": tool_version,
                "run_index": run_index,
                "result_index": result_index,
                "rule_id": str(result.get("ruleId", "unidentified")),
                "level": str(result.get("level", "warning")),
                "message": _message_text(result.get("message")),
                "baseline_state": result.get("baselineState"),
                "fingerprints": fingerprints if isinstance(fingerprints, dict) else {},
                "suppressions": suppressions if isinstance(suppressions, list) else [],
            }
            sanitized_payload, redactions = sanitize_evidence_payload(
                payload, context.plan.sensitivity
            )
            evidence.append(
                EvidenceEnvelope.create(
                    kind="analysis.finding",
                    run_id=context.run_id,
                    activity_id=context.activity.activity_id,
                    collector_id=collector_id,
                    collector_version=collector_version,
                    repository_id=context.plan.subject.repository_id,
                    revision=context.plan.subject.revision,
                    method="SARIF 2.1 import",
                    production_mode="imported",
                    coverage=coverage,
                    payload=sanitized_payload,
                    locations=tuple(locations),
                    raw_references=(raw_reference,) if raw_reference else (),
                    redactions=redactions,
                )
            )
    aggregate = Coverage(
        state=CoverageState.UNKNOWN,
        population="Runs and results declared by the SARIF producer.",
        planned=len(runs),
        examined=len(runs),
        successful=True,
        limitations=(
            "Producer coverage was not asserted; zero results must not be read as clean.",
        ),
    )
    return tuple(evidence), aggregate
