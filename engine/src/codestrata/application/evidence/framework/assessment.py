"""Conservative claim/argument/evidence assessment independent of collectors."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from codestrata.domain.evidence.framework.identifiers import stable_id
from codestrata.domain.evidence.framework.models import (
    Action,
    ActivityRecord,
    ActivityStatus,
    AssessmentProfile,
    AssessmentProfileManifest,
    AssessmentResult,
    ClaimDefinition,
    ClaimOutcome,
    ClaimResult,
    CollectorManifest,
    CoverageState,
    EvidenceEnvelope,
    EvidencePlan,
    Finding,
    Risk,
    TraceabilityEdge,
)

_BASELINE_PROFILE_KEY = "repository-evidence-baseline@1.0"
_ENGINEERING_REVIEW_PROFILE_KEY = "engineering-health-review@1.0"


class AssessmentProfileRegistry:
    """Resolve versioned assessment semantics independently of collection."""

    def manifests(self) -> tuple[AssessmentProfileManifest, ...]:
        return (
            AssessmentProfileManifest(
                profile_id="repository-evidence-baseline",
                version="1.0",
                title="Repository evidence baseline",
                description=(
                    "Evaluates collection availability and coverage, while explicitly "
                    "leaving the user's decision question unassessed."
                ),
                supported_outcomes=tuple(ClaimOutcome),
                limitations=("This profile does not infer modernization or release readiness.",),
            ),
            AssessmentProfileManifest(
                profile_id="engineering-health-review",
                version="1.0",
                title="Engineering health review",
                description=(
                    "Interprets selected code-health and imported analyzer findings, "
                    "while retaining collection gaps and avoiding a universal score."
                ),
                supported_outcomes=tuple(ClaimOutcome),
                limitations=(
                    "It does not establish runtime, release, or modernization readiness.",
                    "Producer-specific scores retain their original provenance.",
                ),
            ),
        )

    def resolve(
        self,
        selection: str,
        *,
        plan: EvidencePlan,
        collectors: dict[str, CollectorManifest],
    ) -> AssessmentProfile:
        if selection not in {_BASELINE_PROFILE_KEY, _ENGINEERING_REVIEW_PROFILE_KEY}:
            known = ", ".join(f"{item.profile_id}@{item.version}" for item in self.manifests())
            raise ValueError(
                f"unknown assessment profile {selection!r}; available profiles: {known}"
            )
        if selection == _ENGINEERING_REVIEW_PROFILE_KEY:
            return create_engineering_review_profile(plan, collectors)
        return create_baseline_profile(plan, collectors)


def create_default_profile_registry() -> AssessmentProfileRegistry:
    return AssessmentProfileRegistry()


def create_baseline_profile(
    plan: EvidencePlan,
    manifests: dict[str, CollectorManifest],
) -> AssessmentProfile:
    """Create the bounded baseline from the evidence explicitly requested."""

    claims: list[ClaimDefinition] = []
    for activity in plan.activities:
        manifest = manifests.get(activity.collector_id)
        if manifest is None:
            output_kinds: tuple[str, ...] = ()
            label = activity.collector_id
        else:
            output_kinds = manifest.output_kinds
            label = manifest.label
        claims.append(
            ClaimDefinition(
                claim_id=f"evidence.{activity.activity_id}",
                statement=f"The requested {label} evidence is available for assessment.",
                activity_id=activity.activity_id,
                accepted_evidence_kinds=output_kinds,
                limitation=(manifest.limitations[0] if manifest and manifest.limitations else None),
            )
        )
    for import_item in plan.imports:
        claims.append(
            ClaimDefinition(
                claim_id=f"evidence.import.{import_item.import_id}",
                statement=(f"The requested SARIF import {import_item.import_id!r} is available."),
                activity_id=f"import:{import_item.import_id}",
                accepted_evidence_kinds=("analysis.finding",),
                minimum_evidence=0,
                limitation="SARIF producer coverage is not inferred from result count.",
            )
        )
    for attestation in plan.attestations:
        claims.append(
            ClaimDefinition(
                claim_id=f"evidence.attestation.{attestation.attestation_id}",
                statement=(
                    f"The declaration {attestation.attestation_id!r} is recorded for review."
                ),
                activity_id=f"attestation:{attestation.attestation_id}",
                accepted_evidence_kinds=("manual.attestation",),
                limitation="Declared evidence was not independently verified.",
            )
        )
    claims.append(
        ClaimDefinition(
            claim_id="decision.user-goal",
            statement=f"The stated decision can be answered: {plan.goal}",
            activity_id="assessment:decision-profile",
            accepted_evidence_kinds=(),
            limitation=(
                "The repository evidence baseline validates collection coverage; "
                "it does not apply decision-specific assessment rules."
            ),
        )
    )
    return AssessmentProfile(
        profile_id="repository-evidence-baseline",
        version="1.0",
        title="Repository evidence baseline",
        goal=(
            "Determine whether the requested repository observations were collected "
            "with enough coverage to support further decisions."
        ),
        questions=plan.questions,
        claims=tuple(claims),
    )


def create_engineering_review_profile(
    plan: EvidencePlan,
    manifests: dict[str, CollectorManifest],
) -> AssessmentProfile:
    baseline = create_baseline_profile(plan, manifests)
    return baseline.model_copy(
        update={
            "profile_id": "engineering-health-review",
            "version": "1.0",
            "title": "Engineering health review",
            "goal": (
                "Turn the explicitly selected structural, language, testing, dependency, "
                "security, and imported evidence into traceable review actions."
            ),
            "claims": tuple(
                claim for claim in baseline.claims if claim.claim_id != "decision.user-goal"
            ),
        }
    )


def _claim_result(
    claim: ClaimDefinition,
    record: ActivityRecord | None,
    matching: tuple[EvidenceEnvelope, ...],
) -> ClaimResult:
    evidence_ids = tuple(item.evidence_id for item in matching)
    limitations = tuple(
        item
        for item in (
            claim.limitation,
            *(limitation for evidence in matching for limitation in evidence.coverage.limitations),
        )
        if item
    )
    if record is None:
        return ClaimResult(
            claim_id=claim.claim_id,
            statement=claim.statement,
            outcome=ClaimOutcome.NOT_ASSESSED,
            rationale="No matching activity record exists.",
            missing_requirements=("activity record",),
            limitations=limitations,
        )
    if record.status is ActivityStatus.SKIPPED:
        return ClaimResult(
            claim_id=claim.claim_id,
            statement=claim.statement,
            outcome=ClaimOutcome.NOT_APPLICABLE,
            rationale=record.message or "The activity was not applicable.",
            limitations=limitations,
        )
    if record.status in {
        ActivityStatus.BLOCKED,
        ActivityStatus.FAILED,
        ActivityStatus.CANCELLED,
    }:
        return ClaimResult(
            claim_id=claim.claim_id,
            statement=claim.statement,
            outcome=ClaimOutcome.INSUFFICIENT_EVIDENCE,
            rationale=record.message or f"Activity ended as {record.status.value}.",
            evidence_ids=evidence_ids,
            missing_requirements=("successful evidence activity",),
            limitations=limitations,
        )
    if len(matching) >= claim.minimum_evidence:
        coverage_states = {item.coverage.state for item in matching}
        if CoverageState.FAILED in coverage_states:
            outcome = ClaimOutcome.INSUFFICIENT_EVIDENCE
            rationale = "Evidence exists, but its declared collection coverage failed."
        elif CoverageState.PARTIAL in coverage_states or CoverageState.UNKNOWN in coverage_states:
            outcome = ClaimOutcome.PARTIALLY_SUPPORTED
            rationale = "Evidence is available, with partial or producer-unknown coverage."
        else:
            outcome = ClaimOutcome.SUPPORTED
            rationale = "The requested evidence is available with successful declared coverage."
        return ClaimResult(
            claim_id=claim.claim_id,
            statement=claim.statement,
            outcome=outcome,
            rationale=rationale,
            evidence_ids=evidence_ids,
            limitations=limitations,
        )
    return ClaimResult(
        claim_id=claim.claim_id,
        statement=claim.statement,
        outcome=ClaimOutcome.INSUFFICIENT_EVIDENCE,
        rationale="The activity completed without enough normalized evidence.",
        evidence_ids=evidence_ids,
        missing_requirements=(f"at least {claim.minimum_evidence} accepted evidence record(s)",),
        limitations=limitations,
    )


def assess_evidence(
    *,
    plan: EvidencePlan,
    run_id: str,
    profile: AssessmentProfile,
    activity_records: tuple[ActivityRecord, ...],
    evidence: tuple[EvidenceEnvelope, ...],
) -> AssessmentResult:
    """Evaluate only normalized evidence and activity coverage contracts."""

    records = {item.activity_id: item for item in activity_records}
    claim_results: list[ClaimResult] = []
    findings: list[Finding] = []
    risks: list[Risk] = []
    actions: list[Action] = []
    edges: list[TraceabilityEdge] = []
    claim_id_by_activity = {
        definition.activity_id: definition.claim_id for definition in profile.claims
    }

    for definition in profile.claims:
        matching = tuple(
            item
            for item in evidence
            if item.activity_id == definition.activity_id
            and item.kind in definition.accepted_evidence_kinds
        )
        result = _claim_result(definition, records.get(definition.activity_id), matching)
        claim_results.append(result)
        relationship: Literal["supports", "contradicts"] = (
            "contradicts" if result.outcome is ClaimOutcome.CONTRADICTED else "supports"
        )
        for evidence_id in result.evidence_ids:
            edges.append(
                TraceabilityEdge(
                    source_id=evidence_id,
                    relationship=relationship,
                    target_id=result.claim_id,
                )
            )
        if result.outcome in {
            ClaimOutcome.PARTIALLY_SUPPORTED,
            ClaimOutcome.INSUFFICIENT_EVIDENCE,
            ClaimOutcome.CONTRADICTED,
            ClaimOutcome.NOT_ASSESSED,
        }:
            finding_id = stable_id("finding", run_id, result.claim_id, result.outcome)
            decision_not_assessed = (
                result.claim_id == "decision.user-goal"
                and result.outcome is ClaimOutcome.NOT_ASSESSED
            )
            finding = Finding(
                finding_id=finding_id,
                claim_id=result.claim_id,
                title=(
                    "Decision question is not assessed by the baseline profile"
                    if decision_not_assessed
                    else "Evidence gap requires review"
                ),
                summary=(
                    "Collection completed, but the baseline profile does not contain "
                    "rules that can answer the stated decision."
                    if decision_not_assessed
                    else result.rationale
                ),
                level="note" if decision_not_assessed else "warning",
                evidence_ids=result.evidence_ids,
            )
            findings.append(finding)
            risk = Risk(
                risk_id=stable_id("risk", finding_id),
                finding_id=finding_id,
                statement=(
                    "Treating collected evidence as a decision would overstate what "
                    "the selected assessment profile established."
                    if decision_not_assessed
                    else "A decision made from this run may overstate repository conditions "
                    "because the requested evidence is incomplete or inconclusive."
                ),
            )
            risks.append(risk)
            action = Action(
                action_id=stable_id("action", finding_id),
                finding_id=finding_id,
                title=(
                    "Select a decision-specific assessment profile"
                    if decision_not_assessed
                    else "Close the evidence gap"
                ),
                rationale=(
                    "Collection evidence alone cannot answer the stated goal."
                    if decision_not_assessed
                    else "Improve collection coverage before relying on this claim."
                ),
                verification=(
                    "Review a profile whose claims, rules, and evidence thresholds match "
                    "the decision, then re-run and confirm every material claim has an "
                    "explicit outcome."
                    if decision_not_assessed
                    else "Re-run the plan and confirm the claim is supported with complete "
                    "or explicitly accepted partial coverage."
                ),
                priority="next" if decision_not_assessed else "now",
            )
            actions.append(action)
            edges.extend(
                (
                    TraceabilityEdge(
                        source_id=result.claim_id,
                        relationship="produces_finding",
                        target_id=finding_id,
                    ),
                    TraceabilityEdge(
                        source_id=finding_id,
                        relationship="creates_risk",
                        target_id=risk.risk_id,
                    ),
                    TraceabilityEdge(
                        source_id=finding_id,
                        relationship="addressed_by",
                        target_id=action.action_id,
                    ),
                )
            )

    for item in evidence:
        if item.kind != "code-health.biomarker":
            continue
        claim_id = claim_id_by_activity[item.activity_id]
        biomarker_id = str(item.payload.get("biomarker_id", "code-health-signal"))
        entity = str(item.payload.get("entity", "repository evidence"))
        severity = str(item.payload.get("severity", "medium")).lower()
        if severity in {"critical", "high", "error"}:
            biomarker_level: Literal["note", "warning", "error"] = "error"
            priority: Literal["now", "next", "later"] = "now"
            likelihood: Literal["unknown", "low", "medium", "high"] = "high"
        elif severity in {"low", "info", "note"}:
            biomarker_level = "note"
            priority = "later"
            likelihood = "low"
        else:
            biomarker_level = "warning"
            priority = "next"
            likelihood = "medium"
        finding_id = stable_id("finding", run_id, item.evidence_id, "biomarker")
        finding = Finding(
            finding_id=finding_id,
            claim_id=claim_id,
            title=f"{biomarker_id.replace('_', ' ').title()} · {entity}",
            summary=str(
                item.payload.get("reason")
                or "The selected code-health biomarker reported this entity."
            ),
            level=biomarker_level,
            evidence_ids=(item.evidence_id,),
            locations=item.locations,
        )
        findings.append(finding)
        risk = Risk(
            risk_id=stable_id("risk", finding_id),
            finding_id=finding_id,
            statement=(
                f"The selected {biomarker_id.replace('_', ' ')} condition may increase "
                "change difficulty or defect exposure if it remains unreviewed."
            ),
            likelihood=likelihood,
            impact="medium" if biomarker_level != "error" else "high",
        )
        risks.append(risk)
        action = Action(
            action_id=stable_id("action", finding_id),
            finding_id=finding_id,
            title=str(
                item.payload.get("action_title")
                or f"Review {biomarker_id.replace('_', ' ')} in {entity}"
            ),
            rationale=str(
                item.payload.get("action_rationale")
                or "The user-selected biomarker crossed its recorded review threshold."
            ),
            verification=str(
                item.payload.get("verification")
                or "Re-run the same evidence plan and confirm the signal is resolved or accepted."
            ),
            priority=priority,
        )
        actions.append(action)
        edges.extend(
            (
                TraceabilityEdge(
                    source_id=item.evidence_id,
                    relationship="produces_finding",
                    target_id=finding_id,
                ),
                TraceabilityEdge(
                    source_id=finding_id,
                    relationship="creates_risk",
                    target_id=risk.risk_id,
                ),
                TraceabilityEdge(
                    source_id=finding_id,
                    relationship="addressed_by",
                    target_id=action.action_id,
                ),
            )
        )

    for item in evidence:
        if item.kind != "source.pattern.search":
            continue
        pattern_id = str(item.payload.get("pattern_id", "unnamed-pattern"))
        assertion = str(item.payload.get("assertion", "unknown"))
        count = int(item.payload.get("occurrence_count", 0))
        related = tuple(
            candidate
            for candidate in evidence
            if candidate.activity_id == item.activity_id
            and candidate.payload.get("pattern_id") == pattern_id
        )
        related_ids = tuple(candidate.evidence_id for candidate in related)
        related_locations = tuple(
            location for candidate in related for location in candidate.locations
        )
        claim_id = claim_id_by_activity[item.activity_id]
        finding_id = stable_id("finding", run_id, item.evidence_id, "interpretation")
        finding = Finding(
            finding_id=finding_id,
            claim_id=claim_id,
            title=f"Custom observation {pattern_id!r} is {assertion}",
            summary=(
                f"The bounded search recorded {count} matching location(s). Presence or "
                "absence has no inherent quality meaning until interpreted for the stated goal."
            ),
            level="note",
            evidence_ids=related_ids,
            locations=related_locations,
        )
        findings.append(finding)
        risk = Risk(
            risk_id=stable_id("risk", finding_id),
            finding_id=finding_id,
            statement=(
                "A text-pattern observation can be over-interpreted because it is not "
                "semantic analysis and its meaning depends on the decision context."
            ),
        )
        risks.append(risk)
        action = Action(
            action_id=stable_id("action", finding_id),
            finding_id=finding_id,
            title=(
                f"Review {count} location(s) for {pattern_id}"
                if count
                else f"Validate the search scope for {pattern_id}"
            ),
            rationale=(
                "Classify the observed locations against the decision before treating "
                "the pattern as a problem or an acceptable condition."
                if count
                else "Confirm the complete searched population and decide whether the "
                "absence is meaningful for the stated goal."
            ),
            verification=(
                "Record the disposition and reasoning for each relevant location, or "
                "revise the pattern/globs and re-run when the search was too broad or narrow."
            ),
            priority="next",
        )
        actions.append(action)
        edges.extend(
            (
                TraceabilityEdge(
                    source_id=item.evidence_id,
                    relationship="produces_finding",
                    target_id=finding_id,
                ),
                TraceabilityEdge(
                    source_id=finding_id,
                    relationship="creates_risk",
                    target_id=risk.risk_id,
                ),
                TraceabilityEdge(
                    source_id=finding_id,
                    relationship="addressed_by",
                    target_id=action.action_id,
                ),
            )
        )

    for item in evidence:
        if item.kind != "analysis.finding" or item.payload.get("suppressions"):
            continue
        level_value = str(item.payload.get("level", "warning"))
        level: Literal["note", "warning", "error"]
        if level_value == "note":
            level = "note"
        elif level_value == "error":
            level = "error"
        else:
            level = "warning"
        finding_id = stable_id("finding", run_id, item.evidence_id)
        claim_id = claim_id_by_activity[item.activity_id]
        finding = Finding(
            finding_id=finding_id,
            claim_id=claim_id,
            title=(
                f"{item.payload.get('tool', 'Imported analysis')}: "
                f"{item.payload.get('rule_id', 'result')}"
            ),
            summary=str(item.payload.get("message", "Imported analysis result.")),
            level=level,
            evidence_ids=(item.evidence_id,),
            locations=item.locations,
        )
        findings.append(finding)
        risk = Risk(
            risk_id=stable_id("risk", finding_id),
            finding_id=finding_id,
            statement=(
                "The imported analyzer result may represent a material issue, but "
                "CodeStrata has not independently validated its rule or severity."
            ),
        )
        risks.append(risk)
        action = Action(
            action_id=stable_id("action", finding_id),
            finding_id=finding_id,
            title="Triage the imported analysis result",
            rationale="The producing tool reported a source-located result.",
            verification=(
                "Review the source and producing rule, apply or reject remediation with "
                "a recorded rationale, then re-run the originating analyzer."
            ),
            priority="now" if level == "error" else "next",
        )
        actions.append(action)
        edges.extend(
            (
                TraceabilityEdge(
                    source_id=item.evidence_id,
                    relationship="produces_finding",
                    target_id=finding_id,
                ),
                TraceabilityEdge(
                    source_id=finding_id,
                    relationship="creates_risk",
                    target_id=risk.risk_id,
                ),
                TraceabilityEdge(
                    source_id=finding_id,
                    relationship="addressed_by",
                    target_id=action.action_id,
                ),
            )
        )

    limitations = tuple(
        sorted(
            {
                "Repository observations do not establish runtime behavior.",
                "Test structure does not establish test passage or test adequacy.",
                "No universal repository quality score is produced.",
                *(item for result in claim_results for item in result.limitations),
            }
        )
    )
    return AssessmentResult(
        assessment_id=stable_id("assessment", plan.plan_id, run_id, profile.profile_id),
        plan_id=plan.plan_id,
        run_id=run_id,
        profile_id=profile.profile_id,
        profile_version=profile.version,
        repository_id=plan.subject.repository_id,
        revision=plan.subject.revision,
        generated_at=datetime.now(UTC),
        claims=tuple(claim_results),
        findings=tuple(findings),
        risks=tuple(risks),
        actions=tuple(actions),
        traceability=tuple(edges),
        evidence_ids=tuple(item.evidence_id for item in evidence),
        limitations=limitations,
    )
