"""Canonical retrieval document and chunk builders from Platform intelligence."""

from __future__ import annotations

from codestrata_platform.application.retrieval.policies import (
    CHUNKING_POLICY_VERSION,
    DefaultCanonicalChunkingPolicy,
)
from codestrata_platform.domain.engineering import EngineeringSnapshot
from codestrata_platform.domain.knowledge_graph.graph import EngineeringKnowledgeGraph
from codestrata_platform.domain.knowledge_graph.taxonomy import GraphNodeType
from codestrata_platform.domain.retrieval.chunk import RetrievalChunk, estimate_tokens
from codestrata_platform.domain.retrieval.document import (
    RetrievalDocument,
    RetrievalSourceReference,
)
from codestrata_platform.domain.retrieval.identifiers import (
    ChunkChecksum,
    RetrievalIndexId,
    deterministic_chunk_id,
    deterministic_document_id,
)
from codestrata_platform.domain.retrieval.taxonomy import RetrievalContentType


class CanonicalRetrievalDocumentBuilder:
    """Build retrieval documents/chunks from published CEIM + completed graph."""

    def __init__(
        self,
        *,
        policy: DefaultCanonicalChunkingPolicy | None = None,
    ) -> None:
        self._policy = policy or DefaultCanonicalChunkingPolicy()

    @property
    def policy_version(self) -> str:
        return self._policy.version or CHUNKING_POLICY_VERSION

    def build(
        self,
        *,
        index_id: RetrievalIndexId,
        snapshot: EngineeringSnapshot,
        graph: EngineeringKnowledgeGraph,
    ) -> tuple[tuple[RetrievalDocument, ...], tuple[RetrievalChunk, ...]]:
        documents: list[RetrievalDocument] = []
        chunks: list[RetrievalChunk] = []

        docs_and_texts: list[tuple[RetrievalDocument, str]] = []
        docs_and_texts.append(self._repository_summary(index_id, snapshot, graph))
        for technology in snapshot.technologies:
            docs_and_texts.append(self._technology(index_id, snapshot, technology, graph))
        for finding in snapshot.findings:
            docs_and_texts.append(self._finding(index_id, snapshot, finding, graph))
        for recommendation in snapshot.recommendations:
            docs_and_texts.append(self._recommendation(index_id, snapshot, recommendation))
        for metric in snapshot.metrics:
            docs_and_texts.append(self._metric(index_id, snapshot, metric))
        for evidence in snapshot.evidence:
            docs_and_texts.append(self._evidence(index_id, snapshot, evidence))

        for document, text in docs_and_texts:
            documents.append(document)
            chunks.extend(self._chunk_document(document, text))
        return tuple(documents), tuple(chunks)

    def _repository_summary(
        self,
        index_id: RetrievalIndexId,
        snapshot: EngineeringSnapshot,
        graph: EngineeringKnowledgeGraph,
    ) -> tuple[RetrievalDocument, str]:
        finding_dist: dict[str, int] = {}
        for finding in snapshot.findings:
            key = finding.severity.value
            finding_dist[key] = finding_dist.get(key, 0) + 1
        tech_names = ", ".join(item.display_name for item in snapshot.technologies) or "none"
        text = (
            f"Repository engineering summary for {snapshot.repository_id.value}. "
            f"Technologies: {tech_names}. "
            f"Findings by severity: {finding_dist or {'none': 0}}. "
            f"Recommendations: {len(snapshot.recommendations)}. "
            f"Graph nodes: {len(graph.nodes)}; edges: {len(graph.edges)}."
        )
        document = RetrievalDocument(
            document_id=deterministic_document_id(
                index_id=index_id.value,
                content_type=RetrievalContentType.REPOSITORY_SUMMARY.value,
                canonical_id=snapshot.repository_id.value,
            ),
            index_id=index_id,
            content_type=RetrievalContentType.REPOSITORY_SUMMARY,
            canonical_type="repository",
            canonical_id=snapshot.repository_id.value,
            title="Repository engineering summary",
            summary=text[:4000],
            structured_content={
                "technology_count": str(len(snapshot.technologies)),
                "finding_count": str(len(snapshot.findings)),
                "recommendation_count": str(len(snapshot.recommendations)),
            },
            source_references=(
                RetrievalSourceReference(
                    source_kind="engineering_snapshot",
                    source_id=snapshot.snapshot_id.value,
                    snapshot_id=snapshot.snapshot_id.value,
                    graph_id=graph.graph_id.value,
                ),
            ),
            graph_node_ids=tuple(
                item.node_id.value
                for item in graph.nodes
                if item.node_type is GraphNodeType.REPOSITORY
            ),
        )
        return document, text

    def _technology(self, index_id, snapshot, technology, graph) -> tuple[RetrievalDocument, str]:
        connected = [
            item.node_id.value
            for item in graph.nodes
            if item.node_type is GraphNodeType.TECHNOLOGY
            and item.canonical_id == technology.canonical_key
        ]
        text = (
            f"Technology {technology.display_name} ({technology.canonical_key}). "
            f"Category: {technology.category.value}."
        )
        document = RetrievalDocument(
            document_id=deterministic_document_id(
                index_id=index_id.value,
                content_type=RetrievalContentType.TECHNOLOGY.value,
                canonical_id=technology.canonical_key,
            ),
            index_id=index_id,
            content_type=RetrievalContentType.TECHNOLOGY,
            canonical_type="technology",
            canonical_id=technology.canonical_key,
            title=technology.display_name,
            summary=text,
            structured_content={"category": technology.category.value},
            source_references=(
                RetrievalSourceReference(
                    source_kind="engineering_technology",
                    source_id=technology.technology_id.value,
                    snapshot_id=snapshot.snapshot_id.value,
                    graph_id=graph.graph_id.value,
                ),
            ),
            graph_node_ids=tuple(connected),
        )
        return document, text

    def _finding(self, index_id, snapshot, finding, graph) -> tuple[RetrievalDocument, str]:
        connected = [
            item.node_id.value
            for item in graph.nodes
            if item.node_type is GraphNodeType.FINDING
            and item.canonical_id in {finding.source_finding_id, finding.finding_id.value}
        ]
        text = (
            f"Finding {finding.title}. Severity: {finding.severity.value}. "
            f"Category: {finding.category.value}. Summary: {finding.summary}. "
            f"Rule: {finding.rule_id}. Evidence refs: {len(finding.evidence_ids)}."
        )
        document = RetrievalDocument(
            document_id=deterministic_document_id(
                index_id=index_id.value,
                content_type=RetrievalContentType.FINDING.value,
                canonical_id=finding.source_finding_id,
            ),
            index_id=index_id,
            content_type=RetrievalContentType.FINDING,
            canonical_type="finding",
            canonical_id=finding.source_finding_id,
            title=finding.title,
            summary=finding.summary,
            structured_content={
                "severity": finding.severity.value,
                "category": finding.category.value,
                "rule_id": finding.rule_id,
            },
            source_references=(
                RetrievalSourceReference(
                    source_kind="engineering_finding",
                    source_id=finding.finding_id.value,
                    snapshot_id=snapshot.snapshot_id.value,
                    graph_id=graph.graph_id.value,
                ),
            ),
            graph_node_ids=tuple(connected),
            metadata={"severity": finding.severity.value, "category": finding.category.value},
        )
        return document, text

    def _recommendation(self, index_id, snapshot, recommendation) -> tuple[RetrievalDocument, str]:
        text = (
            f"Recommendation {recommendation.title}. Priority: {recommendation.priority}. "
            f"Severity: {recommendation.severity.value}. Rationale: {recommendation.rationale}. "
            f"Linked findings: {', '.join(recommendation.related_finding_ids) or 'none'}."
        )
        document = RetrievalDocument(
            document_id=deterministic_document_id(
                index_id=index_id.value,
                content_type=RetrievalContentType.RECOMMENDATION.value,
                canonical_id=recommendation.source_recommendation_id,
            ),
            index_id=index_id,
            content_type=RetrievalContentType.RECOMMENDATION,
            canonical_type="recommendation",
            canonical_id=recommendation.source_recommendation_id,
            title=recommendation.title,
            summary=recommendation.rationale,
            structured_content={
                "priority": recommendation.priority,
                "severity": recommendation.severity.value,
            },
            source_references=(
                RetrievalSourceReference(
                    source_kind="engineering_recommendation",
                    source_id=recommendation.recommendation_id.value,
                    snapshot_id=snapshot.snapshot_id.value,
                ),
            ),
            metadata={"priority": recommendation.priority},
        )
        return document, text

    def _metric(self, index_id, snapshot, metric) -> tuple[RetrievalDocument, str]:
        text = f"Metric {metric.name} = {metric.value} ({metric.kind.value})."
        document = RetrievalDocument(
            document_id=deterministic_document_id(
                index_id=index_id.value,
                content_type=RetrievalContentType.METRIC.value,
                canonical_id=metric.name,
            ),
            index_id=index_id,
            content_type=RetrievalContentType.METRIC,
            canonical_type="metric",
            canonical_id=metric.name,
            title=metric.name,
            summary=text,
            structured_content={"value": metric.value, "kind": metric.kind.value},
            source_references=(
                RetrievalSourceReference(
                    source_kind="engineering_metric",
                    source_id=metric.metric_id.value,
                    snapshot_id=snapshot.snapshot_id.value,
                ),
            ),
        )
        return document, text

    def _evidence(self, index_id, snapshot, evidence) -> tuple[RetrievalDocument, str]:
        text = (
            f"Evidence {evidence.reference} ({evidence.kind.value})"
            + (f" lines {evidence.line_start}-{evidence.line_end}" if evidence.line_start else "")
            + "."
        )
        document = RetrievalDocument(
            document_id=deterministic_document_id(
                index_id=index_id.value,
                content_type=RetrievalContentType.EVIDENCE.value,
                canonical_id=evidence.evidence_id.value,
            ),
            index_id=index_id,
            content_type=RetrievalContentType.EVIDENCE,
            canonical_type="evidence",
            canonical_id=evidence.evidence_id.value,
            title=evidence.reference,
            summary=text,
            structured_content={"kind": evidence.kind.value, "reference": evidence.reference},
            source_references=(
                RetrievalSourceReference(
                    source_kind="engineering_evidence",
                    source_id=evidence.evidence_id.value,
                    snapshot_id=snapshot.snapshot_id.value,
                ),
            ),
        )
        return document, text

    def _chunk_document(
        self,
        document: RetrievalDocument,
        text: str,
    ) -> tuple[RetrievalChunk, ...]:
        max_chars = self._policy.hard_max_tokens * 4
        parts: list[str] = []
        remaining = text.strip()
        while remaining:
            piece = remaining[:max_chars].rstrip()
            if estimate_tokens(piece) > self._policy.hard_max_tokens:
                piece = remaining[: self._policy.hard_max_tokens * 4].rstrip()
            parts.append(piece)
            remaining = remaining[len(piece) :].lstrip()
        if not parts:
            parts = [document.summary]
        chunks: list[RetrievalChunk] = []
        for ordinal, part in enumerate(parts):
            checksum = ChunkChecksum.from_text(part)
            chunks.append(
                RetrievalChunk(
                    chunk_id=deterministic_chunk_id(
                        document_id=document.document_id.value,
                        ordinal=ordinal,
                        checksum=checksum.value,
                    ),
                    document_id=document.document_id,
                    index_id=document.index_id,
                    ordinal=ordinal,
                    text=part,
                    token_estimate=estimate_tokens(part),
                    checksum=checksum,
                    source_references=document.source_references,
                    graph_node_ids=document.graph_node_ids,
                    graph_edge_ids=document.graph_edge_ids,
                    metadata=dict(document.metadata),
                )
            )
        return tuple(chunks)
