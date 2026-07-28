"""Executive Presentation application package."""

from __future__ import annotations

from codestrata_platform.application.executive_presentation.adapter import (
    ExecutivePresentationAdapter,
    project_executive_presentation,
    score_status_for_metric,
)
from codestrata_platform.application.executive_presentation.services import (
    ExecutivePresentationService,
)

__all__ = [
    "ExecutivePresentationAdapter",
    "ExecutivePresentationService",
    "project_executive_presentation",
    "score_status_for_metric",
]
