"""Safety and determinism unit coverage for SV.13 helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from codestrata.security.customer_safe_text import ensure_customer_safe_report_document
from verification.system_defect_fixes.safety import check_engine_redaction_makes_legacy_safe


@pytest.fixture(scope="module")
def monorepo() -> Path:
    return Path(__file__).resolve().parents[4]


@pytest.mark.parametrize("repository_id", ["dubbo", "juice-shop", "nodegoat"])
def test_legacy_report_becomes_safe(monorepo: Path, repository_id: str) -> None:
    base = monorepo / "engine" / "reports" / "verification" / "sv10" / "artifacts" / repository_id
    if not base.is_dir():
        pytest.skip("SV.10 artifacts not present")
    report_path = next(base.glob("*/report.json"))
    raw = json.loads(report_path.read_text(encoding="utf-8"))
    check = check_engine_redaction_makes_legacy_safe(raw)
    assert check.ok, check.detail
    safe = ensure_customer_safe_report_document(raw)
    before = [f.get("id") for f in raw["assessment"]["findings"]]
    after = [f.get("id") for f in safe["assessment"]["findings"]]
    assert before == after
