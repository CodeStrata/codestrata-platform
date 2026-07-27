"""Engineering retrieval indexing and query services."""

from __future__ import annotations

from dataclasses import replace

from codestrata_platform.application.common.errors import NotFoundError, ValidationError
from codestrata_platform.application.retrieval.chunking import CanonicalRetrievalDocumentBuilder
from codestrata_platform.application.retrieval.commands import (
    ArchiveRetrievalIndexCommand,
    BuildRetrievalIndexCommand,
    FailRetrievalIndexCommand,
    RebuildRetrievalIndexCommand,
    SupersedeRetrievalIndexCommand,
)
from codestrata_platform.application.retrieval.context import (
    RetrievalContext,
    RetrievalContextAssembler,
)
from codestrata_platform.application.retrieval.errors import (
    RetrievalConfigurationError,
    RetrievalNotReadyError,
)
from codestrata_platform.application.retrieval.models import (
    RetrievalBuildResult,
    RetrievalChunkSummary,
    RetrievalDocumentSummary,
    RetrievalIndexDetails,
    RetrievalIndexStatistics,
    RetrievalIndexSummary,
    RetrievalSearchHitModel,
    RetrievalSearchResultModel,
)
from codestrata_platform.application.retrieval.policies import (
    RETRIEVAL_SCHEMA_VERSION,
    configured_embedding_dimension,
    configured_embedding_model,
    configured_embedding_provider,
    retrieval_indexing_enabled,
)
from codestrata_platform.application.retrieval.queries import (
    AssembleRetrievalContextQuery,
    GetLatestRepositoryRetrievalIndexQuery,
    GetRetrievalChunkQuery,
    GetRetrievalDocumentQuery,
    GetRetrievalIndexQuery,
    GetRetrievalIndexStatisticsQuery,
    ListRepositoryRetrievalIndexesQuery,
    ListRetrievalDocumentsQuery,
    SearchRetrievalIndexQuery,
)
from codestrata_platform.domain.engineering import (
    EngineeringSnapshotRepository,
    EngineeringSnapshotStatus,
)
from codestrata_platform.domain.knowledge_graph import GraphStatus, KnowledgeGraphRepository
from codestrata_platform.domain.knowledge_graph.identifiers import KnowledgeGraphId
from codestrata_platform.domain.retrieval.embedding import EmbeddingProvider
from codestrata_platform.domain.retrieval.identifiers import (
    EmbeddingDimension,
    EmbeddingModelId,
    EmbeddingProviderId,
    RetrievalProjectionKey,
    deterministic_index_id,
)
from codestrata_platform.domain.retrieval.index import EngineeringRetrievalIndex
from codestrata_platform.domain.retrieval.lifecycle import RetrievalIndexStatus
from codestrata_platform.domain.retrieval.ports import (
    RetrievalIndexRepository,
    RetrievalQueryRepository,
)
from codestrata_platform.domain.retrieval.query import RetrievalQuery, RetrievalScope
from codestrata_platform.domain.retrieval.taxonomy import RetrievalMode


class EngineeringRetrievalIndexingService:
    """Build and query Engineering Retrieval Indexes."""

    def __init__(
        self,
        *,
        indexes: RetrievalIndexRepository,
        snapshots: EngineeringSnapshotRepository,
        graphs: KnowledgeGraphRepository,
        embeddings: EmbeddingProvider,
        queries: RetrievalQueryRepository | None = None,
        builder: CanonicalRetrievalDocumentBuilder | None = None,
    ) -> None:
        self._indexes = indexes
        self._snapshots = snapshots
        self._graphs = graphs
        self._embeddings = embeddings
        self._queries = queries
        self._builder = builder or CanonicalRetrievalDocumentBuilder()

    def build_retrieval_index(
        self,
        command: BuildRetrievalIndexCommand,
    ) -> RetrievalBuildResult:
        snapshot = self._require_published_snapshot(command.snapshot_id)
        graph = self._require_completed_graph(
            command.graph_id,
            repository_id=snapshot.repository_id,
        )
        provider_id = EmbeddingProviderId(
            command.embedding_provider or self._embeddings.provider_id().value
        )
        model_id = EmbeddingModelId(command.embedding_model or self._embeddings.model_id().value)
        dimension = EmbeddingDimension(
            command.embedding_dimension or self._embeddings.dimension().value
        )
        if dimension.value != self._embeddings.dimension().value:
            raise RetrievalConfigurationError(
                "Configured embedding dimension does not match provider",
                reason_code="embedding_dimension_mismatch",
            )
        projection_key = RetrievalProjectionKey.from_parts(
            engineering_snapshot_id=snapshot.snapshot_id.value,
            engineering_snapshot_version=snapshot.version.value,
            knowledge_graph_id=graph.graph_id.value,
            knowledge_graph_version=graph.graph_version.value,
            retrieval_schema_version=RETRIEVAL_SCHEMA_VERSION,
            chunking_policy_version=self._builder.policy_version,
            embedding_provider_id=provider_id.value,
            embedding_model_id=model_id.value,
            embedding_dimension=dimension.value,
        )
        existing = self._indexes.find_by_projection_key(projection_key.value)
        if existing is not None and existing.status is RetrievalIndexStatus.COMPLETED:
            return RetrievalBuildResult(
                index=RetrievalIndexDetails.from_aggregate(existing),
                created=False,
                idempotent=True,
            )

        if existing is not None and existing.status is RetrievalIndexStatus.FAILED:
            index_id = existing.index_id
            index_version = existing.index_version.value
        else:
            index_version = (
                self._indexes.latest_index_version_for_repository(snapshot.repository_id) + 1
            )
            if index_version > 1:
                self._supersede_active_for_repository(snapshot.repository_id)
            index_id = deterministic_index_id(
                repository_id=snapshot.repository_id.value,
                snapshot_id=snapshot.snapshot_id.value,
                graph_id=graph.graph_id.value,
                projection_key=projection_key.value,
            )
        index = EngineeringRetrievalIndex.create_pending(
            index_id=index_id,
            organization_id=snapshot.organization_id,
            workspace_id=snapshot.workspace_id,
            repository_id=snapshot.repository_id,
            assessment_id=snapshot.assessment_id,
            engineering_snapshot_id=snapshot.snapshot_id,
            engineering_snapshot_version=snapshot.version.value,
            knowledge_graph_id=graph.graph_id,
            knowledge_graph_version=graph.graph_version.value,
            index_version=index_version,
            projection_key=projection_key,
            retrieval_schema_version=RETRIEVAL_SCHEMA_VERSION,
            chunking_policy_version=self._builder.policy_version,
            embedding_provider_id=provider_id,
            embedding_model_id=model_id,
            embedding_dimension=dimension,
        )
        index.begin_indexing()
        try:
            documents, chunks = self._builder.build(
                index_id=index.index_id,
                snapshot=snapshot,
                graph=graph,
            )
            for document in documents:
                index.add_document(document)
            texts = tuple(chunk.text for chunk in chunks)
            vectors = self._embeddings.embed_batch(texts)
            if len(vectors) != len(chunks):
                raise ValidationError(
                    "Embedding batch size mismatch",
                    reason_code="embedding_batch_mismatch",
                )
            for chunk, vector in zip(chunks, vectors, strict=True):
                index.add_chunk(replace(chunk, embedding=vector))
            index.complete()
        except Exception as error:  # noqa: BLE001 - indexing boundary
            index.fail(reason=str(error)[:1000])
            self._indexes.save(index)
            raise ValidationError(
                f"Retrieval indexing failed: {error}",
                reason_code="retrieval_indexing_failed",
            ) from error

        self._indexes.save(index)
        return RetrievalBuildResult(
            index=RetrievalIndexDetails.from_aggregate(index),
            created=True,
            idempotent=False,
        )

    def rebuild_retrieval_index(
        self,
        command: RebuildRetrievalIndexCommand,
    ) -> RetrievalBuildResult:
        current = self._require_index(command.index_id)
        return self.build_retrieval_index(
            BuildRetrievalIndexCommand(
                snapshot_id=current.engineering_snapshot_id,
                graph_id=current.knowledge_graph_id,
                embedding_provider=command.embedding_provider,
                embedding_model=command.embedding_model,
                embedding_dimension=command.embedding_dimension,
            )
        )

    def fail_retrieval_index(self, command: FailRetrievalIndexCommand) -> RetrievalIndexDetails:
        index = self._require_index(command.index_id)
        index.fail(command.reason)
        self._indexes.save(index)
        return RetrievalIndexDetails.from_aggregate(index)

    def supersede_retrieval_index(
        self,
        command: SupersedeRetrievalIndexCommand,
    ) -> RetrievalIndexDetails:
        index = self._require_index(command.index_id)
        index.supersede()
        self._indexes.save(index)
        return RetrievalIndexDetails.from_aggregate(index)

    def archive_retrieval_index(
        self,
        command: ArchiveRetrievalIndexCommand,
    ) -> RetrievalIndexDetails:
        index = self._require_index(command.index_id)
        index.archive()
        self._indexes.save(index)
        return RetrievalIndexDetails.from_aggregate(index)

    def get_retrieval_index(self, query: GetRetrievalIndexQuery) -> RetrievalIndexDetails:
        return RetrievalIndexDetails.from_aggregate(self._require_index(query.index_id))

    def get_latest_repository_index(
        self,
        query: GetLatestRepositoryRetrievalIndexQuery,
    ) -> RetrievalIndexDetails:
        index = self._indexes.get_latest_completed(query.repository_id)
        if index is None:
            raise NotFoundError(
                f"Retrieval index not found for repository {query.repository_id.value}",
                reason_code="retrieval_index_not_found",
            )
        return RetrievalIndexDetails.from_aggregate(index)

    def list_repository_indexes(
        self,
        query: ListRepositoryRetrievalIndexesQuery,
    ) -> tuple[RetrievalIndexSummary, ...]:
        items = self._indexes.list_by_repository(query.repository_id)
        return tuple(RetrievalIndexSummary.from_aggregate(item) for item in items)

    def list_documents(
        self,
        query: ListRetrievalDocumentsQuery,
    ) -> tuple[RetrievalDocumentSummary, ...]:
        index = self._require_completed(query.index_id)
        documents = index.documents
        if query.content_types:
            allowed = set(query.content_types)
            documents = tuple(item for item in documents if item.content_type in allowed)
        page = documents[query.offset : query.offset + query.limit]
        return tuple(
            RetrievalDocumentSummary(
                document_id=item.document_id.value,
                content_type=item.content_type.value,
                canonical_type=item.canonical_type,
                canonical_id=item.canonical_id,
                title=item.title,
                summary=item.summary,
            )
            for item in page
        )

    def get_document(self, query: GetRetrievalDocumentQuery) -> RetrievalDocumentSummary:
        index = self._require_completed(query.index_id)
        for item in index.documents:
            if item.document_id == query.document_id:
                return RetrievalDocumentSummary(
                    document_id=item.document_id.value,
                    content_type=item.content_type.value,
                    canonical_type=item.canonical_type,
                    canonical_id=item.canonical_id,
                    title=item.title,
                    summary=item.summary,
                )
        raise NotFoundError(
            f"Retrieval document not found: {query.document_id.value}",
            reason_code="retrieval_document_not_found",
        )

    def get_chunk(self, query: GetRetrievalChunkQuery) -> RetrievalChunkSummary:
        index = self._require_completed(query.index_id)
        for item in index.chunks:
            if item.chunk_id == query.chunk_id:
                return RetrievalChunkSummary(
                    chunk_id=item.chunk_id.value,
                    document_id=item.document_id.value,
                    ordinal=item.ordinal,
                    token_estimate=item.token_estimate,
                    text=item.text,
                    has_embedding=item.embedding is not None,
                )
        raise NotFoundError(
            f"Retrieval chunk not found: {query.chunk_id.value}",
            reason_code="retrieval_chunk_not_found",
        )

    def search(self, query: SearchRetrievalIndexQuery) -> RetrievalSearchResultModel:
        index = self._require_completed(query.index_id)
        scope = RetrievalScope(
            organization_id=index.organization_id.value,
            workspace_id=index.workspace_id.value,
            repository_id=index.repository_id.value,
        )
        if self._queries is not None:
            result = self._queries.search(query.index_id, query.query, scope=scope)
            return RetrievalSearchResultModel(
                hits=tuple(RetrievalSearchHitModel.from_hit(item) for item in result.hits),
                mode=result.mode,
                top_k=result.top_k,
            )
        raise ValidationError(
            "Retrieval query repository is not configured",
            reason_code="retrieval_query_unavailable",
        )

    def assemble_context(self, query: AssembleRetrievalContextQuery) -> RetrievalContext:
        index = self._require_completed(query.index_id)
        scope = RetrievalScope(
            organization_id=index.organization_id.value,
            workspace_id=index.workspace_id.value,
            repository_id=index.repository_id.value,
        )
        if self._queries is None:
            raise ValidationError(
                "Retrieval query repository is not configured",
                reason_code="retrieval_query_unavailable",
            )
        result = self._queries.search(
            query.index_id,
            RetrievalQuery(
                query_text=query.query_text,
                mode=query.mode,
                top_k=query.top_k,
                content_types=query.content_types,
            ),
            scope=scope,
        )
        assembler = RetrievalContextAssembler(max_tokens=query.max_tokens)
        return assembler.assemble(result.hits)

    def statistics(self, query: GetRetrievalIndexStatisticsQuery) -> RetrievalIndexStatistics:
        index = self._require_completed(query.index_id)
        content_type_counts: dict[str, int] = {}
        for document in index.documents:
            key = document.content_type.value
            content_type_counts[key] = content_type_counts.get(key, 0) + 1
        embedded = sum(1 for item in index.chunks if item.embedding is not None)
        return RetrievalIndexStatistics(
            index_id=index.index_id.value,
            document_count=len(index.documents),
            chunk_count=len(index.chunks),
            embedded_chunk_count=embedded,
            content_type_counts=content_type_counts,
        )

    def maybe_auto_index_for_snapshot(self, snapshot_id) -> RetrievalBuildResult | None:
        if not retrieval_indexing_enabled():
            return None
        try:
            provider = configured_embedding_provider()
            model = configured_embedding_model()
            dimension = configured_embedding_dimension()
        except ValueError as error:
            raise RetrievalConfigurationError(
                "Invalid embedding configuration for auto-indexing",
                reason_code="invalid_embedding_configuration",
            ) from error
        if provider != self._embeddings.provider_id().value:
            return None
        return self.build_retrieval_index(
            BuildRetrievalIndexCommand(
                snapshot_id=snapshot_id,
                embedding_provider=provider,
                embedding_model=model,
                embedding_dimension=dimension,
            )
        )

    def _require_published_snapshot(self, snapshot_id):
        snapshot = self._snapshots.get(snapshot_id)
        if snapshot is None:
            raise NotFoundError(
                f"Engineering snapshot not found: {snapshot_id.value}",
                reason_code="engineering_snapshot_not_found",
            )
        if snapshot.status is not EngineeringSnapshotStatus.PUBLISHED:
            raise RetrievalNotReadyError(
                "Retrieval indexing requires a published EngineeringSnapshot",
                reason_code="snapshot_not_published",
            )
        return snapshot

    def _require_completed_graph(self, graph_id: KnowledgeGraphId | None, *, repository_id):
        if graph_id is not None:
            graph = self._graphs.get(graph_id)
        else:
            graph = self._graphs.get_latest_completed(repository_id)
        if graph is None:
            raise NotFoundError(
                "Completed knowledge graph not found for retrieval indexing",
                reason_code="knowledge_graph_not_found",
            )
        if graph.status is not GraphStatus.COMPLETED:
            raise RetrievalNotReadyError(
                "Retrieval indexing requires a completed Knowledge Graph",
                reason_code="graph_not_completed",
            )
        if graph.repository_id != repository_id:
            raise RetrievalNotReadyError(
                "Knowledge graph repository ownership mismatch",
                reason_code="graph_repository_mismatch",
            )
        return graph

    def _require_index(self, index_id):
        index = self._indexes.get(index_id)
        if index is None:
            raise NotFoundError(
                f"Retrieval index not found: {index_id.value}",
                reason_code="retrieval_index_not_found",
            )
        return index

    def _require_completed(self, index_id):
        index = self._require_index(index_id)
        if index.status is not RetrievalIndexStatus.COMPLETED:
            raise RetrievalNotReadyError(
                f"Retrieval index {index_id.value} is not completed",
                reason_code="retrieval_index_not_completed",
            )
        return index

    def _supersede_active_for_repository(self, repository_id) -> None:
        for item in self._indexes.list_by_repository(repository_id):
            if item.status is RetrievalIndexStatus.COMPLETED:
                item.supersede()
                self._indexes.save(item)


__all__ = ["EngineeringRetrievalIndexingService", "RetrievalMode"]
