# ruff: noqa: E501
"""Accessible, self-contained projections of the canonical assessment result."""

from __future__ import annotations

from collections import Counter
from html import escape
from typing import Any

from codestrata.domain.evidence.framework.models import (
    AssessmentResult,
    ClaimOutcome,
    EvidenceEnvelope,
    EvidencePlan,
    RunRecord,
)


def _badge(value: str) -> str:
    return f'<span class="badge badge-{escape(value)}">{escape(value.replace("_", " "))}</span>'


def _locations(item: EvidenceEnvelope) -> str:
    if not item.locations:
        return "Repository-level"
    values = []
    for location in item.locations[:5]:
        suffix = f":{location.start_line}" if location.start_line else ""
        values.append(f"{escape(location.path)}{suffix}")
    if len(item.locations) > 5:
        values.append(f"+{len(item.locations) - 5} more")
    return ", ".join(values)


def _observation(item: EvidenceEnvelope) -> str:
    payload = item.payload
    if item.kind == "repository.inventory":
        languages = (
            ", ".join(f"{name} {count}" for name, count in payload.get("languages", {}).items())
            or "no recognized source language"
        )
        return (
            f"{payload.get('file_count', 0)} files; {languages}; "
            f"{len(payload.get('manifests', []))} manifests; "
            f"{len(payload.get('quality_orchestration', []))} quality-tool configurations"
        )
    if item.kind == "repository.dependencies":
        coverage = payload.get("coverage", {})
        discovered = len(payload.get("discovered_dependency_artifacts", []))
        unsupported = len(payload.get("unsupported_dependency_artifacts", []))
        return (
            f"{discovered} artifacts discovered; "
            f"{coverage.get('manifests_parsed', len(payload.get('manifests', [])))} typed-parsed; "
            f"{unsupported} unsupported; "
            f"{coverage.get('declarations_collected', len(payload.get('declarations', [])))} declarations"
        )
    if item.kind == "repository.testing-structure":
        coverage = payload.get("coverage", {})
        return (
            f"{coverage.get('candidate_test_files_discovered', 0)} test candidates; "
            f"{coverage.get('structurally_confirmed_test_files', 0)} structurally confirmed; "
            f"{coverage.get('frameworks_declared', 0)} declared frameworks"
        )
    if item.kind == "source.pattern.search":
        count = payload.get("occurrence_count", 0)
        suffix = "+" if payload.get("occurrence_count_is_lower_bound") else ""
        return (
            f"Pattern {payload.get('pattern_id', 'unnamed')!s}: "
            f"{payload.get('assertion', 'unknown')}; {count}{suffix} matching locations"
        )
    if item.kind == "source.pattern.occurrence":
        return f"Pattern {payload.get('pattern_id', 'unnamed')!s} matched at this location"
    if item.kind == "analysis.finding":
        return (
            f"{payload.get('tool', 'analysis')} / {payload.get('rule_id', 'result')}: "
            f"{payload.get('message', 'result reported')}"
        )
    if item.kind == "language.provider-summary":
        return (
            f"{payload.get('language', 'language')}: "
            f"{payload.get('source_unit_count', 0)} source units; "
            f"{payload.get('dependency_count', 0)} dependencies; "
            f"{payload.get('framework_usage_count', 0)} framework usages"
        )
    if item.kind == "language.source-unit":
        return (
            f"{payload.get('language', 'language')} unit {payload.get('unit_id', 'unknown')}; "
            f"layer {payload.get('layer_hint', 'unknown')} ({payload.get('layer_confidence', 'unknown')})"
        )
    if item.kind == "language.dependency":
        return (
            f"{payload.get('source_unit_id', 'source')} → {payload.get('target_unit_id', 'target')} "
            f"({payload.get('semantics', 'unknown')})"
        )
    if item.kind == "language.framework-usage":
        return (
            f"{payload.get('framework_id', 'framework')} usage: {payload.get('symbol', 'symbol')}"
        )
    if item.kind == "code-health.coverage":
        return (
            f"{payload.get('files_measured', 0)} files, {payload.get('types_measured', 0)} types, "
            f"{payload.get('callables_measured', 0)} callables; "
            f"{payload.get('biomarker_findings', 0)} selected biomarker findings; no universal score"
        )
    if item.kind == "code-health.provider-summary":
        return (
            f"{payload.get('provider', 'health provider')}: {payload.get('metric_count', 0)} metrics; "
            f"{payload.get('finding_count', 0)} selected findings"
        )
    if item.kind == "code-health.measurement":
        return f"Measured {payload.get('entity_kind', 'entity')} {payload.get('entity', 'unknown')}"
    if item.kind == "code-health.biomarker":
        return (
            f"{payload.get('biomarker_id', 'biomarker')} on {payload.get('entity', 'entity')}: "
            f"{payload.get('reason', 'selected threshold crossed')}"
        )
    if item.kind == "manual.attestation":
        return f"Declared: {payload.get('statement', 'attestation recorded')}"
    return "Normalized observation; inspect evidence.jsonl for its typed payload."


def render_html(
    *,
    plan: EvidencePlan,
    run: RunRecord,
    assessment: AssessmentResult,
    evidence: tuple[EvidenceEnvelope, ...],
) -> str:
    outcomes = Counter(item.outcome.value for item in assessment.claims)
    finding_levels = Counter(item.level for item in assessment.findings)
    outcome_set = {item.outcome for item in assessment.claims}
    if finding_levels.get("error", 0):
        decision_state = f"Action required · {finding_levels['error']} high-priority finding(s)"
    elif outcome_set & {
        ClaimOutcome.PARTIALLY_SUPPORTED,
        ClaimOutcome.INSUFFICIENT_EVIDENCE,
        ClaimOutcome.CONTRADICTED,
    }:
        decision_state = "Review evidence gaps"
    elif ClaimOutcome.NOT_ASSESSED in outcome_set:
        decision_state = "Evidence collected; decision not assessed"
    else:
        decision_state = "Evidence available for assessed claims"
    claim_rows = "".join(
        "<tr>"
        f"<td><code>{escape(item.claim_id)}</code></td>"
        f"<td>{escape(item.statement)}</td>"
        f"<td>{_badge(item.outcome.value)}</td>"
        f"<td>{escape(item.rationale)}</td>"
        f"<td>{len(item.evidence_ids)}</td>"
        "</tr>"
        for item in assessment.claims
    )
    activity_rows = "".join(
        "<tr>"
        f"<td><code>{escape(item.activity_id)}</code></td>"
        f"<td>{escape(item.collector_id)}</td>"
        f"<td>{_badge(item.status.value)}</td>"
        f"<td>{item.evidence_count}</td>"
        f"<td>{escape(item.message)}</td>"
        "</tr>"
        for item in run.activities
    )
    finding_order = {"error": 0, "warning": 1, "note": 2}
    ordered_findings = sorted(
        assessment.findings, key=lambda item: (finding_order[item.level], item.title)
    )
    finding_cards = (
        "".join(
            '<article class="card finding">'
            f"<div>{_badge(item.level)} <code>{escape(item.finding_id)}</code></div>"
            f"<h3>{escape(item.title)}</h3><p>{escape(item.summary)}</p>"
            f"<p><strong>Claim:</strong> <code>{escape(item.claim_id)}</code><br>"
            f"<strong>Evidence:</strong> {', '.join(f'<code>{escape(evidence_id)}</code>' for evidence_id in item.evidence_ids) or 'None; this is a declared assessment gap.'}<br>"
            f"<strong>Locations:</strong> {', '.join(escape(location.path) + (f':{location.start_line}' if location.start_line else '') for location in item.locations) or 'Repository-level'}</p>"
            "</article>"
            for item in ordered_findings
        )
        or '<p class="empty">No findings were produced. Confirm coverage before interpreting this as clean.</p>'
    )
    action_order = {"now": 0, "next": 1, "later": 2}
    actions = (
        "".join(
            "<li>"
            f"{_badge(item.priority)} <strong>{escape(item.title)}</strong> — "
            f'{escape(item.rationale)}<br><span class="verify">From finding '
            f"<code>{escape(item.finding_id)}</code><br>Verify: "
            f"{escape(item.verification)}</span></li>"
            for item in sorted(
                assessment.actions, key=lambda item: (action_order[item.priority], item.title)
            )
        )
        or "<li>No action generated.</li>"
    )
    risk_rows = (
        "".join(
            "<tr>"
            f"<td><code>{escape(item.risk_id)}</code></td>"
            f"<td><code>{escape(item.finding_id)}</code></td>"
            f"<td>{escape(item.statement)}</td>"
            f"<td>{_badge(item.likelihood)}</td>"
            f"<td>{_badge(item.impact)}</td>"
            "</tr>"
            for item in assessment.risks
        )
        or '<tr><td colspan="5">No risks generated.</td></tr>'
    )
    trace_rows = (
        "".join(
            "<tr>"
            f"<td><code>{escape(item.source_id)}</code></td>"
            f"<td>{escape(item.relationship.replace('_', ' '))}</td>"
            f"<td><code>{escape(item.target_id)}</code></td>"
            "</tr>"
            for item in assessment.traceability
        )
        or '<tr><td colspan="3">No traceability edges generated.</td></tr>'
    )
    evidence_rows = "".join(
        "<tr>"
        f"<td><code>{escape(item.evidence_id)}</code></td>"
        f"<td>{escape(item.kind)}</td>"
        f"<td>{escape(_observation(item))}</td>"
        f"<td>{escape(item.collector_id)}@{escape(item.collector_version)}</td>"
        f"<td>{escape(item.method)}</td>"
        f"<td>{_badge(item.coverage.state.value)}</td>"
        f"<td>{escape('; '.join(item.redactions) or 'Default policy; no additional redaction recorded')}</td>"
        f"<td>{_locations(item)}</td>"
        "</tr>"
        for item in evidence
    )
    limitations = "".join(f"<li>{escape(item)}</li>" for item in assessment.limitations)
    questions = (
        "".join(f"<li>{escape(item)}</li>" for item in plan.questions) or "<li>None declared.</li>"
    )
    counts = " · ".join(f"{escape(key)} {value}" for key, value in sorted(outcomes.items()))
    pack_list = (
        "".join(f"<li><code>{escape(item)}</code></li>" for item in plan.packs)
        or "<li>No pack recorded.</li>"
    )
    choice_rows = "".join(
        "<tr>"
        f"<td><code>{escape(item.activity_id)}</code></td>"
        f"<td>{escape(item.collector_id)}</td>"
        f"<td>{escape(', '.join(str(value) for value in item.configuration.get('capabilities', item.configuration.get('biomarkers', []))) or 'Collector defaults')}</td>"
        f"<td>{_badge('enabled' if item.enabled else 'disabled')}</td>"
        "</tr>"
        for item in plan.activities
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(plan.goal)} — CodeStrata Evidence Report</title>
<style>
:root{{--ink:#17231d;--muted:#5f6f66;--paper:#f7f5ef;--panel:#fff;--line:#d9ded9;--green:#176b4b;--amber:#9a5d00;--red:#a52b2b;--blue:#315f8c}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 system-ui,sans-serif}}
main{{max-width:1180px;margin:auto;padding:32px 24px 80px}} header{{border-bottom:3px solid var(--ink);padding-bottom:24px}}
.eyebrow{{letter-spacing:.12em;text-transform:uppercase;color:var(--green);font-weight:800;font-size:.8rem}} h1{{font-size:clamp(2rem,5vw,4.5rem);line-height:1;margin:.25em 0}} h2{{margin-top:2.5rem}} h3{{margin:.6rem 0}}
.brief{{display:grid;grid-template-columns:2fr 1fr;gap:18px;margin:26px 0}} .card{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:20px;box-shadow:0 4px 18px #17231d0b}}
.status{{font-size:1.5rem;font-weight:800}} .meta{{color:var(--muted)}} table{{border-collapse:collapse;width:100%;background:var(--panel)}} th,td{{padding:12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}} th{{font-size:.8rem;text-transform:uppercase;letter-spacing:.05em}} th:first-child,td:first-child{{min-width:10rem}} code{{font-size:.78rem;overflow-wrap:anywhere}}
.table-wrap{{overflow:auto;border:1px solid var(--line);border-radius:12px}} .badge{{display:inline-block;border-radius:999px;background:#e8ece9;padding:2px 9px;font-size:.75rem;font-weight:800;text-transform:uppercase;white-space:nowrap}} .badge-supported,.badge-completed,.badge-complete{{background:#d9f0e5;color:var(--green)}} .badge-partially_supported,.badge-partial,.badge-warning,.badge-next{{background:#fff0cc;color:var(--amber)}} .badge-insufficient_evidence,.badge-failed,.badge-error,.badge-now{{background:#f9dddd;color:var(--red)}} .badge-unknown,.badge-not_assessed{{background:#e1e9f1;color:var(--blue)}}
.finding{{margin:12px 0;border-left:5px solid var(--amber)}} .verify{{color:var(--muted)}} li{{margin:.6rem 0}} .empty{{border:1px dashed var(--line);padding:18px;background:#fff}} @media(max-width:760px){{.brief{{grid-template-columns:1fr}} main{{padding:20px 14px 60px}}}}
</style>
</head>
<body><main>
<header><div class="eyebrow">CodeStrata · Evidence-led repository assessment</div><h1>{escape(plan.goal)}</h1><p class="meta">Run {escape(run.run_id)} · Repository {escape(run.repository_id)} · Revision {escape(run.revision)}</p></header>
<section class="brief" aria-labelledby="decision-heading"><div class="card"><div class="eyebrow">Decision brief</div><h2 id="decision-heading" class="status">{escape(decision_state)}</h2><p>{escape(counts or "No claims evaluated")}. This report separates collected observations from assessment judgments.</p></div><div class="card"><div class="eyebrow">Scope</div><p><strong>{len(evidence)}</strong> evidence records<br><strong>{len(assessment.findings)}</strong> findings<br><strong>{len(assessment.actions)}</strong> actions</p></div></section>
<section><h2>Your evidence choices</h2><div class="brief"><div class="card"><div class="eyebrow">Selected packs</div><ul>{pack_list}</ul></div><div class="card"><div class="eyebrow">Assessment head</div><p><code>{escape(assessment.profile_id)}@{escape(assessment.profile_version)}</code></p><p class="meta">Collector measurements remain separate from assessment judgments.</p></div></div><div class="table-wrap"><table><thead><tr><th>Activity</th><th>Collector</th><th>Capabilities or biomarkers</th><th>State</th></tr></thead><tbody>{choice_rows}</tbody></table></div></section>
<section><h2>Questions</h2><ul>{questions}</ul></section>
<section><h2>Collection coverage</h2><div class="table-wrap"><table><thead><tr><th>Activity</th><th>Collector</th><th>Status</th><th>Evidence</th><th>Explanation</th></tr></thead><tbody>{activity_rows}</tbody></table></div></section>
<section><h2>Claims and arguments</h2><div class="table-wrap"><table><thead><tr><th>Claim</th><th>Statement</th><th>Outcome</th><th>Rationale</th><th>Evidence</th></tr></thead><tbody>{claim_rows}</tbody></table></div></section>
<section><h2>Findings</h2>{finding_cards}</section>
<section><h2>Risks</h2><div class="table-wrap"><table><thead><tr><th>Risk</th><th>Finding</th><th>Statement</th><th>Likelihood</th><th>Impact</th></tr></thead><tbody>{risk_rows}</tbody></table></div></section>
<section><h2>Guiding actions</h2><ol>{actions}</ol></section>
<section><h2>Traceability</h2><div class="table-wrap"><table><thead><tr><th>Source</th><th>Relationship</th><th>Target</th></tr></thead><tbody>{trace_rows}</tbody></table></div></section>
<section><h2>Evidence explorer</h2><p class="meta">This view summarizes normalized observations. The complete typed payloads are in <code>evidence.jsonl</code>.</p><div class="table-wrap"><table><thead><tr><th>Evidence ID</th><th>Kind</th><th>Observation</th><th>Producer</th><th>Method</th><th>Coverage</th><th>Protections</th><th>Location</th></tr></thead><tbody>{evidence_rows}</tbody></table></div></section>
<section><h2>Limitations</h2><ul>{limitations}</ul></section>
</main></body></html>"""


def render_sarif(assessment: AssessmentResult) -> dict[str, Any]:
    rules: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []
    for finding in assessment.findings:
        if not finding.locations:
            continue
        rules.setdefault(
            finding.claim_id,
            {
                "id": finding.claim_id,
                "shortDescription": {"text": finding.title},
                "help": {"text": finding.summary},
            },
        )
        locations = []
        for item in finding.locations:
            region = {
                key: value
                for key, value in {
                    "startLine": item.start_line,
                    "startColumn": item.start_column,
                    "endLine": item.end_line,
                    "endColumn": item.end_column,
                }.items()
                if value is not None
            }
            locations.append(
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": item.path},
                        **({"region": region} if region else {}),
                    }
                }
            )
        results.append(
            {
                "ruleId": finding.claim_id,
                "level": finding.level,
                "message": {"text": finding.summary},
                "locations": locations,
                "partialFingerprints": {"codestrataFindingId": finding.finding_id},
                "properties": {
                    "codestrata/evidenceIds": list(finding.evidence_ids),
                    "codestrata/runId": assessment.run_id,
                },
            }
        )
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "CodeStrata Evidence Framework",
                        "semanticVersion": "1.0.0",
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
            }
        ],
    }
