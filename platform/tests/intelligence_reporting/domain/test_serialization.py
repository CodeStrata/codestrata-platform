"""Deterministic serialization tests for commercial intelligence reporting."""

from __future__ import annotations

import pytest

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.domain.serialization import (
    from_stable_dict,
    to_stable_dict,
)
from codestrata_platform.intelligence_reporting.domain.technology import Ratio
from tests.intelligence_reporting.domain.conftest import make_report


def test_stable_dict_round_trip() -> None:
    report = make_report()
    payload = to_stable_dict(report)
    restored = from_stable_dict(payload)
    assert to_stable_dict(restored) == payload
    assert payload["schema_version"] == "1.0"
    assert payload["report_id"].startswith("eir:")
    assert payload["dataset"]["dataset_id"].startswith("dataset:")


def test_sorted_keys_and_collections() -> None:
    report = make_report()
    payload = to_stable_dict(report)
    assert list(payload.keys()) == sorted(payload.keys())
    included = payload["dataset"]["included_repository_ids"]
    assert included == sorted(included)


def test_decimal_ratio_serializes_as_string() -> None:
    ratio = Ratio.of(1, 2)
    assert ratio.value == "0.5000"
    payload = to_stable_dict(ratio)
    assert payload["value"] == "0.5000"


def test_rejects_absolute_paths_in_domain_strings() -> None:
    report = make_report()
    with pytest.raises(InvalidValueError, match="absolute path|unsafe|filesystem"):
        from codestrata_platform.intelligence_reporting.domain.report import (
            EngineeringIntelligenceReport,
        )

        EngineeringIntelligenceReport.create(
            title="/Users/secret/report",
            report_scope=report.report_scope,
            dataset=report.dataset,
        )
