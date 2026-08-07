"""Classification re-export (Slice 12.5)."""

from __future__ import annotations

from verification.infrastructure_repository_contract.inventory import (
    CLASSIFIED_ENTRIES,
    build_classification,
    check_classification,
)

__all__ = ["CLASSIFIED_ENTRIES", "build_classification", "check_classification"]
