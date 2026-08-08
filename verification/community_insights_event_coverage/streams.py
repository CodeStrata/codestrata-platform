"""Stream inventory helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_insights_event_coverage.contract import STREAMS
from verification.community_insights_event_coverage.inventory import exists
from verification.community_insights_event_coverage.schemas import STREAM_SCHEMA_MAP


def invent_streams(monorepo: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in STREAM_SCHEMA_MAP:
        present = exists(monorepo, row["module"]) if row["stream"] != "lake_envelope" else exists(
            monorepo, "platform/src/codestrata_platform/community_cloud_api/data_lake/envelopes.py"
        )
        rows.append({**row, "module_present": present})
    return rows


def expected_stream_names() -> tuple[str, ...]:
    return STREAMS
