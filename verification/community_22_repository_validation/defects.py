"""Defect aggregation helpers."""

from __future__ import annotations

from verification.community_22_repository_validation.models import Defect


def summarize_defects(defects: list[Defect]) -> dict[str, int]:
    by_classification: dict[str, int] = {}
    for defect in defects:
        by_classification[defect.classification] = by_classification.get(defect.classification, 0) + 1
    return by_classification
