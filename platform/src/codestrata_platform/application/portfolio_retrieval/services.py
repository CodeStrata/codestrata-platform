"""Portfolio retrieval indexing and query services."""

from __future__ import annotations

from dataclasses import replace

from codestrata_platform.application.common.errors import NotFoundError, ValidationError
from codestrata_platform.application.portfolio_retrieval.commands import (
    ArchivePortfolioRetrievalIndexCommand,
    BuildPortfolioRetrievalIndexCommand,
    FailPortfolioRetrievalIndexCommand,
    RebuildPortfolioRetrievalIndexCommand,
    SupersedePortfolioRetrievalIndexCommand,
)
from codestrata_platform.application.portfolio_retrieval.context import (
    PortfolioRetrievalContextAssembler,
)
from codestrata_platform.application.portfolio_retrieval.document_builder import (
    PortfolioRetrievalDocumentBuilder,
)
from codestrata_platform.application.portfolio_retrieval.errors import (
    PortfolioRetrievalConfigurationError,
    PortfolioRetrievalNotReadyError,
)
from codestrata_platform.application.portfolio_retrieval.models import (
    PortfolioRetrievalBuildResult,
    PortfolioRetrievalChunkSummary,
    PortfolioRetrievalContext,
    PortfolioRetrievalDocumentDetails,
    PortfolioRetrievalDocumentSummary,
    PortfolioRetrievalIndexDetails,
    PortfolioRetrievalIndexStatistics,
    PortfolioRetrievalIndexSummary,
    PortfolioRetrievalSearchHitModel,
    PortfolioRetrievalSearchResultModel,
)
from codestrata_platform.application.portfolio_retrieval.policies import (
    PORTFOLIO_RANKING_POLICY_VERSION,
    PORTFOLIO_RETRIEVAL_SCHEMA_VERSION,
    configured_portfolio_embedding_dimension,
    configured_portfolio_embedding_model,
    configured_portfolio_embedding_provider,
    portfolio_retrieval_enabled,
)
from codestrata_platform.application.portfolio_retrieval.queries import (
    BuildPortfolioRetrievalContextQuery,
    GetLatestPortfolioRetrievalIndexQuery,
    GetPortfolioRetrievalChunkQuery,
    GetPortfolioRetrievalDocumentQuery,
    GetPortfolioRetrievalIndexQuery,
    GetPortfolioRetrievalIndexStatisticsQuery,
    ListPortfolioRetrievalDocumentsQuery,
    ListPortfolioRetrievalIndexesQuery,
    SearchPortfolioRetrievalIndexQuery,
)
from codestrata_platform.domain.portfolio.coverage import PortfolioCoverageSummary
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.portfolio.lifecycle import (
    AssessmentFreshnessStatus,
    PortfolioSnapshotStatus,
    RepositoryAvailabilityStatus,
    RepositoryCriticality,
)
from codestrata_platform.domain.portfolio.ports import (
    EngineeringPortfolioRepository,
    PortfolioSnapshotRepository,
)
from codestrata_platform.domain.portfolio.snapshot import PortfolioSnapshot
from codestrata_platform.domain.portfolio_retrieval.identifiers import (
    EmbeddingDimension,
    EmbeddingModelId,
    EmbeddingProviderId,
    PortfolioRetrievalProjectionKey,
    deterministic_portfolio_index_id,
)
from codestrata_platform.domain.portfolio_retrieval.index import PortfolioRetrievalIndex
from codestrata_platform.domain.portfolio_retrieval.lifecycle import (
    PortfolioRetrievalIndexStatus,
)
from codestrata_platform.domain.portfolio_retrieval.ports import (
    PortfolioRetrievalIndexRepository,
    PortfolioRetrievalQueryRepository,
    PortfolioRetrievalSourceRepository,
)
from codestrata_platform.domain.portfolio_retrieval.query import PortfolioRetrievalQuery
from codestrata_platform.domain.portfolio_retrieval.scope import PortfolioRetrievalScope
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.retrieval.embedding import EmbeddingProvider


class PortfolioRetrievalIndexingService:
    """Build and query Portfolio Retrieval Indexes."""

    def __init__(
        self,
        *,
        indexes: PortfolioRetrievalIndexRepository,
        portfolio_snapshots: PortfolioSnapshotRepository,
        portfolios: EngineeringPortfolioRepository,
        embeddings: EmbeddingProvider,
        queries: PortfolioRetrievalQueryRepository | None = None,
        sources: PortfolioRetrievalSourceRepository | None = None,
        builder: PortfolioRetrievalDocumentBuilder | None = None,
    ) -> None:
        self._indexes = indexes
        self._portfolio_snapshots = portfolio_snapshots
        self._portfolios = portfolios
        self._embeddings = embeddings
        self._queries = queries
        self._sources = sources
        self._builder = builder or PortfolioRetrievalDocumentBuilder()

    def build_index(
        self,
        command: BuildPortfolioRetrievalIndexCommand,
    ) -> PortfolioRetrievalBuildResult:
        if not portfolio_retrieval_enabled():
            raise PortfolioRetrievalNotReadyError(
                "Portfolio retrieval indexing is disabled",
                reason_code="portfolio_retrieval_disabled",
            )
        snapshot = self._require_owned_completed_snapshot(command)
        provider_id = EmbeddingProviderId(
            command.embedding_provider or self._embeddings.provider_id().value
        )
        model_id = EmbeddingModelId(command.embedding_model or self._embeddings.model_id().value)
        dimension = EmbeddingDimension(
            command.embedding_dimension or self._embeddings.dimension().value
        )
        if provider_id.value != self._embeddings.provider_id().value:
            raise PortfolioRetrievalConfigurationError(
                "Configured embedding provider does not match provider",
                reason_code="portfolio_embedding_provider_mismatch",
            )
        if model_id.value != self._embeddings.model_id().value:
            raise PortfolioRetrievalConfigurationError(
                "Configured embedding model does not match provider",
                reason_code="portfolio_embedding_model_mismatch",
            )
        if dimension.value != self._embeddings.dimension().value:
            raise PortfolioRetrievalConfigurationError(
                "Configured embedding dimension does not match provider",
                reason_code="portfolio_embedding_dimension_mismatch",
            )

        selected_identities = tuple(
            f"{item.repository_id.value}:{item.engineering_snapshot_id or ''}:"
            f"{item.engineering_snapshot_version or 0}:{item.knowledge_graph_id or ''}:"
            f"{item.knowledge_graph_version or 0}"
            for item in snapshot.repository_selections
        )
        projection_key = PortfolioRetrievalProjectionKey.from_parts(
            portfolio_id=snapshot.portfolio_id.value,
            portfolio_snapshot_id=snapshot.portfolio_snapshot_id.value,
            portfolio_snapshot_version=snapshot.version.value,
            selected_repository_snapshot_identities=selected_identities,
            retrieval_schema_version=PORTFOLIO_RETRIEVAL_SCHEMA_VERSION,
            chunking_policy_version=self._builder.policy_version,
            ranking_policy_version=PORTFOLIO_RANKING_POLICY_VERSION,
            embedding_provider_id=provider_id.value,
            embedding_model_id=model_id.value,
            embedding_dimension=dimension.value,
        )
        existing = self._indexes.find_by_projection_key(projection_key.value)
        if (
            existing is not None
            and existing.status is PortfolioRetrievalIndexStatus.COMPLETED
            and not command.force
        ):
            return PortfolioRetrievalBuildResult(
                index=PortfolioRetrievalIndexDetails.from_aggregate(existing),
                created=False,
                idempotent=True,
            )

        prior_completed: PortfolioRetrievalIndex | None = None
        if (
            command.force
            and existing is not None
            and existing.status is PortfolioRetrievalIndexStatus.COMPLETED
        ):
            # Snapshot prior completed index, then free the unique projection-key slot.
            prior_completed = existing.snapshot()
            existing.supersede()
            existing.projection_key = PortfolioRetrievalProjectionKey(
                f"{existing.projection_key.value}:s{existing.index_version.value}"[:128]
            )
            self._indexes.save(existing)
            existing = None

        if existing is not None and existing.status is PortfolioRetrievalIndexStatus.FAILED:
            index_id = existing.index_id
            index_version = existing.index_version.value
        else:
            index_version = (
                self._indexes.latest_index_version_for_portfolio(snapshot.portfolio_id) + 1
            )
            index_id = deterministic_portfolio_index_id(
                portfolio_id=snapshot.portfolio_id.value,
                portfolio_snapshot_id=snapshot.portfolio_snapshot_id.value,
                projection_key=(
                    f"{projection_key.value}:v{index_version}"
                    if command.force or prior_completed is not None
                    else projection_key.value
                ),
            )

        if self._sources is not None:
            sourced = self._sources.load_completed(snapshot.portfolio_snapshot_id)
            if sourced is None:
                raise PortfolioRetrievalNotReadyError(
                    "Portfolio retrieval source snapshot is unavailable",
                    reason_code="portfolio_retrieval_source_unavailable",
                )

        repository_ids = tuple(item.repository_id for item in snapshot.repository_selections)
        index = PortfolioRetrievalIndex.create_pending(
            index_id=index_id,
            organization_id=snapshot.organization_id,
            workspace_id=snapshot.workspace_id,
            portfolio_id=snapshot.portfolio_id,
            portfolio_snapshot_id=snapshot.portfolio_snapshot_id,
            portfolio_snapshot_version=snapshot.version.value,
            index_version=index_version,
            projection_key=projection_key,
            retrieval_schema_version=PORTFOLIO_RETRIEVAL_SCHEMA_VERSION,
            chunking_policy_version=self._builder.policy_version,
            ranking_policy_version=PORTFOLIO_RANKING_POLICY_VERSION,
            embedding_provider_id=provider_id,
            embedding_model_id=model_id,
            embedding_dimension=dimension,
            repository_ids=repository_ids,
        )
        index.begin_indexing()
        try:
            documents, chunks = self._builder.build(
                index_id=index.index_id,
                portfolio_snapshot=snapshot,
            )
            for document in documents:
                index.add_document(document)
            texts = tuple(chunk.text for chunk in chunks)
            vectors = self._embeddings.embed_batch(texts)
            if len(vectors) != len(chunks):
                raise ValidationError(
                    "Embedding batch size mismatch",
                    reason_code="portfolio_embedding_batch_mismatch",
                )
            for chunk, vector in zip(chunks, vectors, strict=True):
                index.add_chunk(replace(chunk, embedding=vector))
            index.complete()
        except Exception as error:  # noqa: BLE001 - indexing boundary
            index.fail(reason=str(error)[:1000])
            # Keep unique projection_key free for prior restore / future retries.
            index.projection_key = PortfolioRetrievalProjectionKey(
                f"{projection_key.value}:f{index_version}"[:128]
            )
            self._indexes.save(index)
            if prior_completed is not None:
                self._indexes.save(prior_completed)
            raise ValidationError(
                f"Portfolio retrieval indexing failed: {error}",
                reason_code="portfolio_retrieval_indexing_failed",
            ) from error

        if prior_completed is None and index_version > 1:
            self._supersede_active_for_portfolio(
                snapshot.portfolio_id,
                except_index_id=index.index_id,
            )
        self._indexes.save(index)
        return PortfolioRetrievalBuildResult(
            index=PortfolioRetrievalIndexDetails.from_aggregate(index),
            created=True,
            idempotent=False,
        )

    def rebuild_index(
        self,
        command: RebuildPortfolioRetrievalIndexCommand,
    ) -> PortfolioRetrievalBuildResult:
        current = self._require_owned_index(
            command.index_id,
            command.organization_id,
            command.workspace_id,
        )
        return self.build_index(
            BuildPortfolioRetrievalIndexCommand(
                portfolio_id=current.portfolio_id,
                organization_id=current.organization_id,
                workspace_id=current.workspace_id,
                portfolio_snapshot_id=current.portfolio_snapshot_id,
                embedding_provider=command.embedding_provider,
                embedding_model=command.embedding_model,
                embedding_dimension=command.embedding_dimension,
                force=command.force,
            )
        )

    def fail(self, command: FailPortfolioRetrievalIndexCommand) -> PortfolioRetrievalIndexDetails:
        index = self._require_index(command.index_id)
        index.fail(command.reason)
        self._indexes.save(index)
        return PortfolioRetrievalIndexDetails.from_aggregate(index)

    def supersede(
        self,
        command: SupersedePortfolioRetrievalIndexCommand,
    ) -> PortfolioRetrievalIndexDetails:
        index = self._require_index(command.index_id)
        index.supersede()
        self._indexes.save(index)
        return PortfolioRetrievalIndexDetails.from_aggregate(index)

    def archive(
        self,
        command: ArchivePortfolioRetrievalIndexCommand,
    ) -> PortfolioRetrievalIndexDetails:
        index = self._require_index(command.index_id)
        index.archive()
        self._indexes.save(index)
        return PortfolioRetrievalIndexDetails.from_aggregate(index)

    def get(self, query: GetPortfolioRetrievalIndexQuery) -> PortfolioRetrievalIndexDetails:
        index = self._require_owned_index(
            query.index_id, query.organization_id, query.workspace_id
        )
        return PortfolioRetrievalIndexDetails.from_aggregate(index)

    def get_latest(
        self,
        query: GetLatestPortfolioRetrievalIndexQuery,
    ) -> PortfolioRetrievalIndexDetails:
        self._require_owned_portfolio(query.portfolio_id, query.organization_id, query.workspace_id)
        index = self._indexes.get_latest_completed(query.portfolio_id)
        if index is None or (
            index.organization_id != query.organization_id
            or index.workspace_id != query.workspace_id
        ):
            raise NotFoundError(
                f"Portfolio retrieval index not found for portfolio {query.portfolio_id.value}",
                reason_code="portfolio_retrieval_index_not_found",
            )
        return PortfolioRetrievalIndexDetails.from_aggregate(index)

    def list(
        self,
        query: ListPortfolioRetrievalIndexesQuery,
    ) -> tuple[PortfolioRetrievalIndexSummary, ...]:
        self._require_owned_portfolio(query.portfolio_id, query.organization_id, query.workspace_id)
        items = self._indexes.list_by_portfolio(query.portfolio_id)
        return tuple(PortfolioRetrievalIndexSummary.from_aggregate(item) for item in items)

    def list_documents(
        self,
        query: ListPortfolioRetrievalDocumentsQuery,
    ) -> tuple[PortfolioRetrievalDocumentSummary, ...]:
        index = self._require_completed(query.index_id)
        documents = index.documents
        if query.content_types:
            allowed = set(query.content_types)
            documents = tuple(item for item in documents if item.content_type in allowed)
        page = documents[query.offset : query.offset + query.limit]
        return tuple(self._document_summary(item) for item in page)

    def get_document(
        self,
        query: GetPortfolioRetrievalDocumentQuery,
    ) -> PortfolioRetrievalDocumentDetails:
        index = self._require_completed(query.index_id)
        for item in index.documents:
            if item.document_id == query.document_id:
                return self._document_details(item)
        raise NotFoundError(
            f"Portfolio retrieval document not found: {query.document_id.value}",
            reason_code="portfolio_retrieval_document_not_found",
        )

    def get_chunk(self, query: GetPortfolioRetrievalChunkQuery) -> PortfolioRetrievalChunkSummary:
        index = self._require_completed(query.index_id)
        for item in index.chunks:
            if item.chunk_id == query.chunk_id:
                return PortfolioRetrievalChunkSummary(
                    chunk_id=item.chunk_id.value,
                    document_id=item.document_id.value,
                    ordinal=item.ordinal,
                    token_estimate=item.token_estimate,
                    text=item.text,
                    repository_ids=tuple(entry.value for entry in item.repository_ids),
                    primary_repository_id=(
                        item.primary_repository_id.value if item.primary_repository_id else None
                    ),
                    has_embedding=item.embedding is not None,
                )
        raise NotFoundError(
            f"Portfolio retrieval chunk not found: {query.chunk_id.value}",
            reason_code="portfolio_retrieval_chunk_not_found",
        )

    def search(
        self,
        query: SearchPortfolioRetrievalIndexQuery,
    ) -> PortfolioRetrievalSearchResultModel:
        index = self._require_owned_completed(
            query.index_id, query.organization_id, query.workspace_id
        )
        if self._queries is None:
            raise ValidationError(
                "Portfolio retrieval query repository is not configured",
                reason_code="portfolio_retrieval_query_unavailable",
            )
        scope = self._scope_for(index, query=query.query)
        result = self._queries.search(
            query.index_id,
            query.query,
            scope=scope,
            criticality_lookup=self._criticality_lookup(index.portfolio_id),
        )
        return PortfolioRetrievalSearchResultModel(
            hits=tuple(PortfolioRetrievalSearchHitModel.from_hit(item) for item in result.hits),
            mode=result.mode,
            top_k=result.top_k,
        )

    def assemble_context(
        self,
        query: BuildPortfolioRetrievalContextQuery,
    ) -> PortfolioRetrievalContext:
        index = self._require_owned_completed(
            query.index_id, query.organization_id, query.workspace_id
        )
        if self._queries is None:
            raise ValidationError(
                "Portfolio retrieval query repository is not configured",
                reason_code="portfolio_retrieval_query_unavailable",
            )
        scope = self._scope_for(
            index,
            repository_ids=tuple(RepositoryId(item) for item in query.repository_ids),
            exclude_repository_ids=tuple(
                RepositoryId(item) for item in query.exclude_repository_ids
            ),
        )
        domain_query = PortfolioRetrievalQuery(
            query_text=query.query_text,
            mode=query.mode,
            top_k=query.top_k,
            content_types=query.content_types,
            repository_balance_mode=query.repository_balance_mode,
            repository_ids=scope.repository_ids if query.repository_ids else (),
            exclude_repository_ids=scope.exclude_repository_ids,
        )
        result = self._queries.search(
            query.index_id,
            domain_query,
            scope=scope,
            criticality_lookup=self._criticality_lookup(index.portfolio_id),
        )
        hits = result.hits
        unavailable_repos, stale_repos = self._repository_diagnostics(index.portfolio_id)
        assembler = PortfolioRetrievalContextAssembler()
        return assembler.assemble(
            hits,
            max_tokens=query.max_tokens,
            max_repositories=query.max_repositories,
            unavailable_repos=unavailable_repos,
            stale_repos=stale_repos,
        )

    def statistics(
        self,
        query: GetPortfolioRetrievalIndexStatisticsQuery,
    ) -> PortfolioRetrievalIndexStatistics:
        index = self._require_completed(query.index_id)
        content_type_counts: dict[str, int] = {}
        for document in index.documents:
            key = document.content_type.value
            content_type_counts[key] = content_type_counts.get(key, 0) + 1
        embedded = sum(1 for item in index.chunks if item.embedding is not None)
        return PortfolioRetrievalIndexStatistics(
            index_id=index.index_id.value,
            document_count=len(index.documents),
            chunk_count=len(index.chunks),
            embedded_chunk_count=embedded,
            repository_count=len(index.repository_ids),
            content_type_counts=content_type_counts,
        )

    def maybe_auto_index_for_portfolio_snapshot(
        self,
        portfolio_snapshot_id: PortfolioSnapshotId,
    ) -> PortfolioRetrievalBuildResult | None:
        if not portfolio_retrieval_enabled():
            return None
        snapshot = self._portfolio_snapshots.get(portfolio_snapshot_id)
        if snapshot is None or snapshot.status is not PortfolioSnapshotStatus.COMPLETED:
            return None
        try:
            provider = configured_portfolio_embedding_provider()
            model = configured_portfolio_embedding_model()
            dimension = configured_portfolio_embedding_dimension()
        except ValueError as error:
            raise PortfolioRetrievalConfigurationError(
                "Invalid embedding configuration for portfolio retrieval auto-indexing",
                reason_code="invalid_portfolio_embedding_configuration",
            ) from error
        if provider != self._embeddings.provider_id().value:
            return None
        return self.build_index(
            BuildPortfolioRetrievalIndexCommand(
                portfolio_id=snapshot.portfolio_id,
                organization_id=snapshot.organization_id,
                workspace_id=snapshot.workspace_id,
                portfolio_snapshot_id=snapshot.portfolio_snapshot_id,
                embedding_provider=provider,
                embedding_model=model,
                embedding_dimension=dimension,
            )
        )

    def _require_owned_completed_snapshot(
        self,
        command: BuildPortfolioRetrievalIndexCommand,
    ) -> PortfolioSnapshot:
        portfolio = self._portfolios.get(command.portfolio_id)
        if portfolio is None:
            raise NotFoundError(
                f"Portfolio '{command.portfolio_id.value}' was not found",
                reason_code="portfolio_not_found",
            )
        if (
            portfolio.organization_id != command.organization_id
            or portfolio.workspace_id != command.workspace_id
        ):
            raise NotFoundError(
                f"Portfolio '{command.portfolio_id.value}' was not found",
                reason_code="portfolio_not_found",
            )
        if command.portfolio_snapshot_id is not None:
            snapshot = self._portfolio_snapshots.get(command.portfolio_snapshot_id)
        else:
            snapshot = self._portfolio_snapshots.get_latest_completed(command.portfolio_id)
        if snapshot is None:
            raise NotFoundError(
                "Portfolio snapshot not found",
                reason_code="portfolio_snapshot_not_found",
            )
        if (
            snapshot.portfolio_id != command.portfolio_id
            or snapshot.organization_id != command.organization_id
            or snapshot.workspace_id != command.workspace_id
        ):
            raise NotFoundError(
                "Portfolio snapshot not found",
                reason_code="portfolio_snapshot_not_found",
            )
        if snapshot.status is not PortfolioSnapshotStatus.COMPLETED:
            raise PortfolioRetrievalNotReadyError(
                "Portfolio retrieval indexing requires a completed PortfolioSnapshot",
                reason_code="portfolio_snapshot_not_completed",
            )
        return snapshot

    def _require_index(self, index_id) -> PortfolioRetrievalIndex:
        index = self._indexes.get(index_id)
        if index is None:
            raise NotFoundError(
                f"Portfolio retrieval index not found: {index_id.value}",
                reason_code="portfolio_retrieval_index_not_found",
            )
        return index

    def _require_owned_index(
        self,
        index_id,
        organization_id,
        workspace_id,
    ) -> PortfolioRetrievalIndex:
        index = self._require_index(index_id)
        if index.organization_id != organization_id or index.workspace_id != workspace_id:
            raise NotFoundError(
                f"Portfolio retrieval index not found: {index_id.value}",
                reason_code="portfolio_retrieval_index_not_found",
            )
        return index

    def _require_owned_portfolio(self, portfolio_id, organization_id, workspace_id) -> None:
        portfolio = self._portfolios.get(portfolio_id)
        if portfolio is None or (
            portfolio.organization_id != organization_id
            or portfolio.workspace_id != workspace_id
        ):
            raise NotFoundError(
                f"Portfolio '{portfolio_id.value}' was not found",
                reason_code="portfolio_not_found",
            )

    def _require_completed(self, index_id) -> PortfolioRetrievalIndex:
        index = self._require_index(index_id)
        if index.status is not PortfolioRetrievalIndexStatus.COMPLETED:
            raise PortfolioRetrievalNotReadyError(
                f"Portfolio retrieval index {index_id.value} is not completed",
                reason_code="portfolio_retrieval_index_not_completed",
            )
        return index

    def _require_owned_completed(
        self, index_id, organization_id, workspace_id
    ) -> PortfolioRetrievalIndex:
        index = self._require_owned_index(index_id, organization_id, workspace_id)
        if index.status is not PortfolioRetrievalIndexStatus.COMPLETED:
            raise PortfolioRetrievalNotReadyError(
                f"Portfolio retrieval index {index_id.value} is not completed",
                reason_code="portfolio_retrieval_index_not_completed",
            )
        return index

    def _supersede_active_for_portfolio(
        self,
        portfolio_id: PortfolioId,
        *,
        except_index_id=None,
    ) -> None:
        for item in self._indexes.list_by_portfolio(portfolio_id):
            if except_index_id is not None and item.index_id == except_index_id:
                continue
            if item.status is PortfolioRetrievalIndexStatus.COMPLETED:
                item.supersede()
                self._indexes.save(item)

    def _scope_for(
        self,
        index: PortfolioRetrievalIndex,
        *,
        query: PortfolioRetrievalQuery | None = None,
        repository_ids: tuple[RepositoryId, ...] | None = None,
        exclude_repository_ids: tuple[RepositoryId, ...] | None = None,
    ) -> PortfolioRetrievalScope:
        allowed = {item.value: item for item in index.repository_ids}
        requested = (
            query.repository_ids
            if query is not None
            else (repository_ids if repository_ids is not None else ())
        )
        excluded = (
            query.exclude_repository_ids
            if query is not None
            else (exclude_repository_ids if exclude_repository_ids is not None else ())
        )
        for repository_id in requested:
            if repository_id.value not in allowed:
                raise ValidationError(
                    f"Repository '{repository_id.value}' is outside the portfolio retrieval index",
                    reason_code="portfolio_retrieval_repository_outside_portfolio",
                )
        for repository_id in excluded:
            if repository_id.value not in allowed:
                raise ValidationError(
                    f"Repository '{repository_id.value}' is outside the portfolio retrieval index",
                    reason_code="portfolio_retrieval_repository_outside_portfolio",
                )
        scoped_ids = requested if requested else tuple(allowed.values())
        return PortfolioRetrievalScope(
            organization_id=index.organization_id,
            workspace_id=index.workspace_id,
            portfolio_id=index.portfolio_id,
            portfolio_snapshot_id=index.portfolio_snapshot_id,
            repository_ids=scoped_ids,
            exclude_repository_ids=excluded,
        )

    def _criticality_lookup(self, portfolio_id: PortfolioId) -> dict[str, RepositoryCriticality]:
        portfolio = self._portfolios.get(portfolio_id)
        if portfolio is None:
            return {}
        return {
            item.repository_id.value: item.criticality
            for item in portfolio.active_memberships
        }

    def _repository_diagnostics(
        self,
        portfolio_id: PortfolioId,
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        snapshot = self._portfolio_snapshots.get_latest_completed(portfolio_id)
        if snapshot is None:
            return (), ()
        unavailable = tuple(
            sorted(
                item.repository_id.value
                for item in snapshot.repository_selections
                if item.availability_status is RepositoryAvailabilityStatus.UNAVAILABLE
            )
        )
        coverage = snapshot.coverage_summary
        stale = ()
        if isinstance(coverage, PortfolioCoverageSummary):
            stale = tuple(
                sorted(
                    item.repository_id.value
                    for item in coverage.repository_statuses
                    if item.freshness_status is AssessmentFreshnessStatus.STALE
                )
            )
        return unavailable, stale

    def _document_summary(self, item) -> PortfolioRetrievalDocumentSummary:
        return PortfolioRetrievalDocumentSummary(
            document_id=item.document_id.value,
            content_type=item.content_type.value,
            canonical_type=item.canonical_type,
            canonical_id=item.canonical_id,
            title=item.title,
            summary=item.summary,
            repository_ids=tuple(entry.value for entry in item.repository_ids),
            primary_repository_id=(
                item.primary_repository_id.value if item.primary_repository_id else None
            ),
        )

    def _document_details(self, item) -> PortfolioRetrievalDocumentDetails:
        summary = self._document_summary(item)
        return PortfolioRetrievalDocumentDetails(
            document_id=summary.document_id,
            content_type=summary.content_type,
            canonical_type=summary.canonical_type,
            canonical_id=summary.canonical_id,
            title=summary.title,
            summary=summary.summary,
            repository_ids=summary.repository_ids,
            primary_repository_id=summary.primary_repository_id,
            structured_content=dict(item.structured_content),
            metadata=dict(item.metadata),
            checksum=item.checksum,
        )


__all__ = ["PortfolioRetrievalIndexingService"]
