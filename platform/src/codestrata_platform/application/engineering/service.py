"""EngineeringNormalizationService — Assessment Intelligence → CEIM snapshot."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from codestrata_platform.application.commands.engineering import (
    BuildEngineeringSnapshotCommand,
    PublishEngineeringSnapshotCommand,
    SupersedeEngineeringSnapshotCommand,
)
from codestrata_platform.application.common.errors import NotFoundError, ValidationError
from codestrata_platform.application.models.engineering import (
    EngineeringBuildResult,
    EngineeringSnapshotDetails,
    EngineeringSnapshotSummary,
    EvidenceSummary,
    FindingSummary,
    MetricSummary,
    RecommendationSummary,
    RiskSummary,
    TechnologySummary,
)
from codestrata_platform.application.queries.engineering import (
    GetEngineeringSnapshotQuery,
    GetFindingInventoryQuery,
    GetLatestEngineeringSnapshotQuery,
    GetMetricInventoryQuery,
    GetRecommendationInventoryQuery,
    GetRiskInventoryQuery,
    GetTechnologyInventoryQuery,
    ListEngineeringSnapshotsQuery,
)
from codestrata_platform.domain.engineering import (
    EngineeringComponent,
    EngineeringComponentId,
    EngineeringEvidence,
    EngineeringEvidenceId,
    EngineeringFinding,
    EngineeringFindingId,
    EngineeringMetric,
    EngineeringMetricId,
    EngineeringRecommendation,
    EngineeringRecommendationId,
    EngineeringRelationshipType,
    EngineeringSnapshot,
    EngineeringSnapshotId,
    EngineeringSnapshotRepository,
    EngineeringSnapshotStatus,
    EngineeringTag,
    EngineeringTechnology,
    EngineeringTechnologyId,
    EvidenceKind,
    TechnologyTaxonomy,
    normalize_technology_name,
)
from codestrata_platform.domain.engineering.relationships import relationship
from codestrata_platform.domain.engineering.services import (
    map_category,
    map_metric_kind,
    map_priority_to_severity,
    map_severity,
)
from codestrata_platform.domain.intelligence import (
    AssessmentIntelligence,
    AssessmentIntelligenceRepository,
    IntelligenceIngestionStatus,
)


class EngineeringNormalizationService:
    """Deterministic Assessment Intelligence → Engineering Snapshot normalization."""

    def __init__(
        self,
        *,
        snapshots: EngineeringSnapshotRepository,
        intelligence: AssessmentIntelligenceRepository,
        taxonomy: TechnologyTaxonomy | None = None,
        on_snapshot_published: Callable[[Any], Any] | None = None,
    ) -> None:
        self._snapshots = snapshots
        self._intelligence = intelligence
        self._taxonomy = taxonomy or TechnologyTaxonomy()
        self._on_snapshot_published = on_snapshot_published

    def build_engineering_snapshot(
        self,
        command: BuildEngineeringSnapshotCommand,
    ) -> EngineeringBuildResult:
        intelligence = self._resolve_intelligence(
            assessment_id=command.assessment_id,
            intelligence_id=command.intelligence_id,
        )
        if intelligence.status is not IntelligenceIngestionStatus.COMPLETED:
            raise ValidationError(
                "Assessment intelligence must be completed before engineering normalization",
                reason_code="intelligence_not_completed",
            )

        existing = self._snapshots.find_by_intelligence_revision(
            assessment_id=intelligence.assessment_id,
            assessment_intelligence_id=intelligence.intelligence_id.value,
            assessment_revision=intelligence.revision,
        )
        if (
            existing is not None
            and existing.status is EngineeringSnapshotStatus.PUBLISHED
        ):
            return EngineeringBuildResult(
                snapshot=EngineeringSnapshotDetails.from_aggregate(existing),
                created=False,
                idempotent=True,
            )

        version = self._snapshots.latest_version_for_assessment(intelligence.assessment_id) + 1
        if version > 1:
            self._supersede_published(intelligence.assessment_id)

        snapshot = EngineeringSnapshot.create(
            organization_id=intelligence.organization_id,
            workspace_id=intelligence.workspace_id,
            repository_id=intelligence.repository_id,
            assessment_id=intelligence.assessment_id,
            assessment_intelligence_id=intelligence.intelligence_id.value,
            assessment_revision=intelligence.revision,
            version=version,
            source_artifact_ids=intelligence.source_artifact_ids,
        )
        payload = self._normalize(intelligence)
        snapshot.build(**payload)
        if command.publish:
            snapshot.publish()
        self._snapshots.save(snapshot)
        if command.publish:
            self._notify_snapshot_published(snapshot.snapshot_id)
        return EngineeringBuildResult(
            snapshot=EngineeringSnapshotDetails.from_aggregate(snapshot),
            created=True,
            idempotent=False,
        )

    def publish_engineering_snapshot(
        self,
        command: PublishEngineeringSnapshotCommand,
    ) -> EngineeringSnapshotDetails:
        snapshot = self._require_snapshot(command.snapshot_id)
        snapshot.publish()
        self._snapshots.save(snapshot)
        self._notify_snapshot_published(snapshot.snapshot_id)
        return EngineeringSnapshotDetails.from_aggregate(snapshot)

    def supersede_engineering_snapshot(
        self,
        command: SupersedeEngineeringSnapshotCommand,
    ) -> EngineeringSnapshotDetails:
        snapshot = self._require_snapshot(command.snapshot_id)
        snapshot.supersede()
        self._snapshots.save(snapshot)
        return EngineeringSnapshotDetails.from_aggregate(snapshot)

    def get_engineering_snapshot(
        self,
        query: GetEngineeringSnapshotQuery,
    ) -> EngineeringSnapshotDetails:
        return EngineeringSnapshotDetails.from_aggregate(
            self._require_snapshot(query.snapshot_id)
        )

    def get_latest_engineering_snapshot(
        self,
        query: GetLatestEngineeringSnapshotQuery,
    ) -> EngineeringSnapshotDetails:
        snapshot = self._snapshots.get_latest_published(query.assessment_id)
        if snapshot is None:
            raise NotFoundError(
                f"Engineering snapshot not found for assessment {query.assessment_id.value}",
                reason_code="engineering_snapshot_not_found",
            )
        return EngineeringSnapshotDetails.from_aggregate(snapshot)

    def list_engineering_snapshots(
        self,
        query: ListEngineeringSnapshotsQuery,
    ) -> tuple[EngineeringSnapshotSummary, ...]:
        if query.assessment_id is None:
            raise ValidationError(
                "assessment_id is required to list engineering snapshots",
                reason_code="assessment_id_required",
            )
        items = self._snapshots.list_by_assessment(query.assessment_id)
        return tuple(EngineeringSnapshotSummary.from_aggregate(item) for item in items)

    def get_technology_inventory(
        self,
        query: GetTechnologyInventoryQuery,
    ) -> tuple[TechnologySummary, ...]:
        snapshot = self._resolve_snapshot_for_inventory(
            snapshot_id=query.snapshot_id,
            assessment_id=query.assessment_id,
        )
        return tuple(TechnologySummary.from_domain(item) for item in snapshot.technologies)

    def get_finding_inventory(
        self,
        query: GetFindingInventoryQuery,
    ) -> tuple[FindingSummary, ...]:
        snapshot = self._resolve_snapshot_for_inventory(
            snapshot_id=query.snapshot_id,
            assessment_id=query.assessment_id,
        )
        findings = snapshot.findings
        if query.severity is not None:
            findings = tuple(item for item in findings if item.severity is query.severity)
        return tuple(FindingSummary.from_domain(item) for item in findings)

    def get_risk_inventory(
        self,
        query: GetRiskInventoryQuery,
    ) -> tuple[RiskSummary, ...]:
        from codestrata_platform.domain.engineering.enums import EngineeringSeverity

        snapshot = self._resolve_snapshot_for_inventory(
            snapshot_id=query.snapshot_id,
            assessment_id=query.assessment_id,
        )
        findings = snapshot.findings
        if query.severity is not None:
            findings = tuple(item for item in findings if item.severity is query.severity)
        risk_severities = {
            EngineeringSeverity.MEDIUM,
            EngineeringSeverity.HIGH,
            EngineeringSeverity.CRITICAL,
        }
        return tuple(
            RiskSummary(
                finding_id=item.finding_id.value,
                severity=item.severity,
                category=item.category,
                title=item.title,
            )
            for item in findings
            if item.severity in risk_severities
        )

    def get_recommendation_inventory(
        self,
        query: GetRecommendationInventoryQuery,
    ) -> tuple[RecommendationSummary, ...]:
        snapshot = self._resolve_snapshot_for_inventory(
            snapshot_id=query.snapshot_id,
            assessment_id=query.assessment_id,
        )
        return tuple(
            RecommendationSummary.from_domain(item) for item in snapshot.recommendations
        )

    def get_metric_inventory(
        self,
        query: GetMetricInventoryQuery,
    ) -> tuple[MetricSummary, ...]:
        snapshot = self._resolve_snapshot_for_inventory(
            snapshot_id=query.snapshot_id,
            assessment_id=query.assessment_id,
        )
        return tuple(MetricSummary.from_domain(item) for item in snapshot.metrics)

    def get_evidence_inventory(
        self,
        *,
        snapshot_id: EngineeringSnapshotId | None = None,
        assessment_id=None,
    ) -> tuple[EvidenceSummary, ...]:
        snapshot = self._resolve_snapshot_for_inventory(
            snapshot_id=snapshot_id,
            assessment_id=assessment_id,
        )
        return tuple(EvidenceSummary.from_domain(item) for item in snapshot.evidence)

    def _normalize(self, intelligence: AssessmentIntelligence) -> dict:
        technologies: dict[str, EngineeringTechnology] = {}
        components: dict[str, EngineeringComponent] = {}
        evidence_items: list[EngineeringEvidence] = []
        findings: list[EngineeringFinding] = []
        relationships = []
        tags: dict[str, EngineeringTag] = {}

        for finding in intelligence.findings:
            evidence_ids: list[str] = []
            for evidence in finding.evidence_references:
                eng_evidence = EngineeringEvidence(
                    evidence_id=EngineeringEvidenceId.generate(),
                    kind=_evidence_kind(evidence.evidence_type, evidence.path_reference),
                    reference=evidence.path_reference,
                    line_start=evidence.line_start,
                    line_end=evidence.line_end,
                    symbol=evidence.symbol,
                    source_artifact_id=evidence.source_artifact_id,
                    checksum=evidence.checksum,
                )
                evidence_items.append(eng_evidence)
                evidence_ids.append(eng_evidence.evidence_id.value)
                relationships.append(
                    relationship(
                        relationship_type=EngineeringRelationshipType.SUPPORTED_BY,
                        source_type="finding",
                        source_id=finding.finding_id.value,
                        target_type="evidence",
                        target_id=eng_evidence.evidence_id.value,
                    )
                )

            tech_keys: list[str] = []
            for candidate in _technology_candidates(finding):
                resolved = self._taxonomy.resolve(candidate) or normalize_technology_name(
                    candidate
                )
                if resolved is None:
                    continue
                key, display = resolved
                if key not in technologies:
                    technologies[key] = EngineeringTechnology(
                        technology_id=EngineeringTechnologyId.generate(),
                        canonical_key=key,
                        display_name=display,
                        category=map_category(finding.category),
                    )
                tech_keys.append(key)
                relationships.append(
                    relationship(
                        relationship_type=EngineeringRelationshipType.USES,
                        source_type="repository",
                        source_id=intelligence.repository_id.value,
                        target_type="technology",
                        target_id=technologies[key].technology_id.value,
                    )
                )

            component_ids: list[str] = []
            if finding.affected_component:
                name = finding.affected_component.strip()
                if name and name not in components:
                    components[name] = EngineeringComponent(
                        component_id=EngineeringComponentId.generate(),
                        name=name,
                        path_reference=finding.affected_path_reference,
                    )
                if name in components:
                    component_ids.append(components[name].component_id.value)

            eng_finding = EngineeringFinding(
                finding_id=EngineeringFindingId.generate(),
                source_finding_id=finding.finding_id.value,
                category=map_category(finding.category),
                severity=map_severity(finding.severity),
                title=finding.title,
                summary=finding.summary,
                rule_id=finding.rule_id,
                confidence=finding.confidence,
                evidence_ids=tuple(evidence_ids),
                technology_keys=tuple(sorted(set(tech_keys))),
                component_ids=tuple(component_ids),
                metadata=dict(finding.metadata or {}),
            )
            findings.append(eng_finding)
            relationships.append(
                relationship(
                    relationship_type=EngineeringRelationshipType.HAS,
                    source_type="repository",
                    source_id=intelligence.repository_id.value,
                    target_type="finding",
                    target_id=eng_finding.finding_id.value,
                )
            )
            tags[eng_finding.category.value] = EngineeringTag(name=eng_finding.category.value)

        finding_source_to_eng = {
            item.source_finding_id: item.finding_id.value for item in findings
        }

        recommendations: list[EngineeringRecommendation] = []
        for recommendation in intelligence.recommendations:
            related = tuple(recommendation.related_finding_ids)
            eng_recommendation = EngineeringRecommendation(
                recommendation_id=EngineeringRecommendationId.generate(),
                source_recommendation_id=recommendation.recommendation_id.value,
                category=map_category(recommendation.category),
                severity=map_priority_to_severity(recommendation.priority.value),
                title=recommendation.title,
                rationale=recommendation.rationale,
                priority=recommendation.priority.value,
                related_finding_ids=related,
            )
            recommendations.append(eng_recommendation)
            for related_id in related:
                target = finding_source_to_eng.get(related_id, related_id)
                relationships.append(
                    relationship(
                        relationship_type=EngineeringRelationshipType.RESOLVES,
                        source_type="recommendation",
                        source_id=eng_recommendation.recommendation_id.value,
                        target_type="finding",
                        target_id=target,
                    )
                )

        metrics: list[EngineeringMetric] = []
        for metric in intelligence.metrics:
            metrics.append(
                EngineeringMetric(
                    metric_id=EngineeringMetricId.generate(),
                    name=metric.name.value,
                    kind=map_metric_kind(metric.value.kind),
                    value=str(metric.value.value),
                    unit=metric.unit,
                    metadata=dict(metric.metadata or {}),
                )
            )

        # Deduplicate repository→technology USES relationships by target.
        unique_relationships = []
        seen = set()
        for item in relationships:
            key = (
                item.relationship_type.value,
                item.source_type,
                item.source_id,
                item.target_type,
                item.target_id,
            )
            if key in seen:
                continue
            seen.add(key)
            unique_relationships.append(item)

        return {
            "technologies": tuple(
                technologies[key] for key in sorted(technologies.keys())
            ),
            "components": tuple(components[name] for name in sorted(components.keys())),
            "findings": tuple(findings),
            "recommendations": tuple(recommendations),
            "metrics": tuple(metrics),
            "evidence": tuple(evidence_items),
            "relationships": tuple(unique_relationships),
            "tags": tuple(tags[name] for name in sorted(tags.keys())),
        }

    def _resolve_intelligence(self, *, assessment_id, intelligence_id):
        if intelligence_id is not None:
            item = self._intelligence.get(intelligence_id)
            if item is None:
                raise NotFoundError(
                    f"Assessment intelligence not found: {intelligence_id.value}",
                    reason_code="intelligence_not_found",
                )
            if item.assessment_id != assessment_id:
                raise ValidationError(
                    "Intelligence does not belong to the requested assessment",
                    reason_code="intelligence_assessment_mismatch",
                )
            return item

        items = self._intelligence.list_by_assessment(assessment_id)
        completed = [
            item
            for item in items
            if item.status is IntelligenceIngestionStatus.COMPLETED
        ]
        if not completed:
            raise NotFoundError(
                f"Completed assessment intelligence not found for {assessment_id.value}",
                reason_code="intelligence_not_found",
            )
        return sorted(completed, key=lambda item: item.revision, reverse=True)[0]

    def _notify_snapshot_published(self, snapshot_id: EngineeringSnapshotId) -> None:
        if self._on_snapshot_published is None:
            return
        try:
            self._on_snapshot_published(snapshot_id)
        except Exception:  # noqa: BLE001 - optional graph projection must not fail CEIM
            return

    def _supersede_published(self, assessment_id) -> None:
        for item in self._snapshots.list_by_assessment(assessment_id):
            if item.status is EngineeringSnapshotStatus.PUBLISHED:
                item.supersede()
                self._snapshots.save(item)

    def _require_snapshot(self, snapshot_id: EngineeringSnapshotId) -> EngineeringSnapshot:
        snapshot = self._snapshots.get(snapshot_id)
        if snapshot is None:
            raise NotFoundError(
                f"Engineering snapshot not found: {snapshot_id.value}",
                reason_code="engineering_snapshot_not_found",
            )
        return snapshot

    def _resolve_snapshot_for_inventory(
        self,
        *,
        snapshot_id: EngineeringSnapshotId | None,
        assessment_id,
    ) -> EngineeringSnapshot:
        if snapshot_id is not None:
            return self._require_snapshot(snapshot_id)
        if assessment_id is None:
            raise ValidationError(
                "snapshot_id or assessment_id is required",
                reason_code="snapshot_selector_required",
            )
        snapshot = self._snapshots.get_latest_published(assessment_id)
        if snapshot is None:
            raise NotFoundError(
                f"Engineering snapshot not found for assessment {assessment_id.value}",
                reason_code="engineering_snapshot_not_found",
            )
        return snapshot


def _technology_candidates(finding) -> list[str]:
    candidates: list[str] = []
    metadata = dict(finding.metadata or {})
    for key in ("technology", "framework", "stack", "runtime"):
        if key in metadata:
            candidates.append(metadata[key])
    if finding.affected_component:
        candidates.append(finding.affected_component)
    # Rule ids often encode domain.technology.rule
    parts = finding.rule_id.split(".")
    if len(parts) >= 2:
        candidates.append(parts[1])
        candidates.append(parts[0])
    return candidates


def _evidence_kind(evidence_type: str | None, path_reference: str) -> EvidenceKind:
    raw = (evidence_type or "").strip().lower()
    for item in EvidenceKind:
        if item.value == raw:
            return item
    path = path_reference.lower()
    if path.endswith((".yml", ".yaml", ".toml", ".ini", ".json", ".xml", ".properties")):
        return EvidenceKind.CONFIGURATION
    if "/" in path or path.endswith(
        (".py", ".java", ".ts", ".js", ".go", ".rs", ".cs", ".kt")
    ):
        return EvidenceKind.FILE
    return EvidenceKind.OTHER
