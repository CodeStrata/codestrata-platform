"""SV.6 input verification."""

from __future__ import annotations

from verification.website_export.contract import (
    EXPECTED_SV6_DATASET_ID,
    EXPECTED_SV6_INTERP_BUNDLE,
    EXPECTED_SV6_REPORT_ID,
)
from verification.website_export.inputs import verify_source_eir


def test_verified_inputs(verified_export) -> None:
    report = verified_export.report
    assert report.report_id.value == EXPECTED_SV6_REPORT_ID
    assert report.dataset.dataset_id.value == EXPECTED_SV6_DATASET_ID
    assert report.interpretation_policy_bundle_id == EXPECTED_SV6_INTERP_BUNDLE
    results = verify_source_eir(report)
    assert all(item.ok for item in results), [r for r in results if not r.ok]
