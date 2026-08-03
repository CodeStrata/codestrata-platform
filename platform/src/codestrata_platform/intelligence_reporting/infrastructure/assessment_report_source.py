"""Canonical assessment report source adapters (in-memory; persistence deferred)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from codestrata_platform.intelligence_reporting.application.errors import (
    MalformedAssessmentReportError,
)
from codestrata_platform.intelligence_reporting.application.ports import (
    CanonicalAssessmentReportSource,
    InlineAssessmentReportSource,
)
from codestrata_platform.intelligence_reporting.domain.dataset import IntelligenceDataset

__all__ = [
    "CanonicalAssessmentReportSource",
    "InlineAssessmentReportSource",
    "InMemoryAssessmentReportSource",
    "InMemoryIntelligenceDatasetRepository",
]


class InMemoryAssessmentReportSource:
    """Test/dev adapter storing canonical reports by reference."""

    def __init__(self, documents: Mapping[str, Mapping[str, Any]] | None = None) -> None:
        self._documents = dict(documents or {})

    def put(self, report_reference: str, document: Mapping[str, Any]) -> None:
        self._documents[report_reference] = dict(document)

    def load(self, report_reference: str) -> Mapping[str, Any]:
        if report_reference not in self._documents:
            raise MalformedAssessmentReportError(
                f"no report document registered for reference: {report_reference}",
                reason_code="missing_report_reference",
            )
        return dict(self._documents[report_reference])


class InMemoryIntelligenceDatasetRepository:
    def __init__(self) -> None:
        self._items: dict[str, IntelligenceDataset] = {}

    def save(self, dataset: IntelligenceDataset) -> None:
        self._items[dataset.dataset_id.value] = dataset

    def get(self, dataset_id: str) -> IntelligenceDataset | None:
        return self._items.get(dataset_id)
