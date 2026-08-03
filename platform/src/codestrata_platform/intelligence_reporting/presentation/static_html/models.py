"""View-model aliases for static HTML rendering (projection is source of truth)."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.website_export.models import (
    WebsiteSafeExportDocument,
)

# HTML renders WebsiteSafeExportDocument directly — no separate business model.
HtmlExportViewModel = WebsiteSafeExportDocument

__all__ = ["HtmlExportViewModel", "WebsiteSafeExportDocument"]
