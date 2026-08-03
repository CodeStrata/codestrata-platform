"""Application ports for commercial intelligence dataset ingestion."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from codestrata_platform.intelligence_reporting.application.errors import (
    MalformedAssessmentReportError,
)
from codestrata_platform.intelligence_reporting.domain.dataset import IntelligenceDataset


class CanonicalAssessmentReportSource(Protocol):
    """Load a canonical Engine assessment report document by reference."""

    def load(self, report_reference: str) -> Mapping[str, Any]:
        """Return the full canonical report document (not embedded into dataset)."""


class InlineAssessmentReportSource:
    """Default source that only supports inline report_document on inputs."""

    def load(self, report_reference: str) -> Mapping[str, Any]:
        raise MalformedAssessmentReportError(
            f"no report document registered for reference: {report_reference}",
            reason_code="missing_report_reference",
        )


class IntelligenceDatasetRepository(Protocol):
    """Persistence port — production implementation deferred."""

    def save(self, dataset: IntelligenceDataset) -> None: ...

    def get(self, dataset_id: str) -> IntelligenceDataset | None: ...
