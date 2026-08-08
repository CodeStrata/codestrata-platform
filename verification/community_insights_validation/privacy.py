"""Privacy boundary checks."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.community_insights_validation._common import add_check, ensure_platform_importable
from verification.community_insights_validation.contract import (
    FRONTEND_SOURCE_FILES,
    PRIVACY_FORBIDDEN_FIELDS,
    PRIVACY_UI_FILES,
)
from verification.community_insights_validation.fixtures import build_fixtures, bounded_reader, metric_window
from verification.community_insights_validation.inventory import read_text
from verification.community_insights_validation.models import CheckResult, Defect


def _ui_source(monorepo: Path) -> str:
    return "\n".join(read_text(monorepo, rel) for rel in PRIVACY_UI_FILES)


def _frontend_source(monorepo: Path) -> str:
    return "\n".join(read_text(monorepo, rel) for rel in FRONTEND_SOURCE_FILES)


def check_privacy(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ui_source = _ui_source(monorepo)
    frontend_source = _frontend_source(monorepo)
    fx = build_fixtures()

    for field in PRIVACY_FORBIDDEN_FIELDS:
        pattern = re.compile(rf"\b{re.escape(field)}\b")
        add_check(
            checks,
            defects,
            f"privacy:ui_no_{field}",
            not pattern.search(ui_source),
            "absent",
            "privacy",
        )

    for poison in fx.poison_strings:
        add_check(
            checks,
            defects,
            f"privacy:frontend_no_{poison[:12]}",
            poison not in frontend_source,
            "absent",
            "privacy",
        )

    ensure_platform_importable(monorepo)
    from codestrata_platform.community_cloud_api.insights.models import MetricRequest
    from codestrata_platform.community_cloud_api.insights.service import aggregate_metric

    reader, _ = bounded_reader(monorepo)
    start, end = metric_window()
    result = aggregate_metric(
        MetricRequest("cli_version_adoption", start, end),
        reader=reader,
    )
    dumped = json.dumps(result.to_stable_dict())
    for poison in fx.poison_strings:
        add_check(
            checks,
            defects,
            f"privacy:metric_no_{poison[:12]}",
            poison not in dumped,
            "absent",
            "privacy",
        )
    return checks, defects
