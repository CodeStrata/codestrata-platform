"""Partition shape / ACCEPTED_ROOT source audit."""

from __future__ import annotations

from pathlib import Path

from verification.community_data_lake_insights.contract import PARTITIONS_PY
from verification.community_data_lake_insights.helpers import check, read_text
from verification.community_data_lake_insights.models import CheckResult, Defect


def check_partitions(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    text = read_text(monorepo / PARTITIONS_PY)
    summary = {
        "accepted_root": "raw" if 'ACCEPTED_ROOT = "raw"' in text else None,
        "quarantine_root": "quarantine" if "QUARANTINE_ROOT" in text else None,
        "installation_id_in_template": "installation_id" in text
        and "stream=" in text
        and "installation" in text.lower(),
        "hive_stream_date_schema": False,
    }

    accepted_ok = 'ACCEPTED_ROOT = "raw"' in text
    checks.append(
        check("partitions:accepted_root_raw", accepted_ok, "ACCEPTED_ROOT=raw", "partitions")
    )
    if not accepted_ok:
        defects.append(
            Defect(
                "accepted_root",
                "partitions:accepted_root_raw",
                'ACCEPTED_ROOT = "raw"',
                "missing",
            )
        )

    quarantine_ok = 'QUARANTINE_ROOT = "quarantine"' in text
    checks.append(
        check(
            "partitions:quarantine_root",
            quarantine_ok,
            "QUARANTINE_ROOT=quarantine",
            "partitions",
        )
    )

    hive_ok = (
        "stream={stream}" in text
        and "schema_version={schema_version}" in text
        and "year={year}" in text
        and "month={month}" in text
        and "day={day}" in text
    )
    summary["hive_stream_date_schema"] = hive_ok
    checks.append(
        check(
            "partitions:hive_shape",
            hive_ok,
            "stream/schema_version/year/month/day",
            "partitions",
        )
    )
    if not hive_ok:
        defects.append(
            Defect(
                "partition_shape",
                "partitions:hive_shape",
                "hive stream/date/schema",
                "missing",
            )
        )

    # installation_id must not appear in partition template construction
    # Forbidden substrings list may mention "installation" as blocked token — that is OK.
    template_has_installation_id = (
        "installation_id=" in text or "/installation_id/" in text
    )
    summary["installation_id_in_template"] = template_has_installation_id
    checks.append(
        check(
            "partitions:no_installation_id_in_template",
            not template_has_installation_id,
            "installation_id absent from key template",
            "partitions",
        )
    )
    if template_has_installation_id:
        defects.append(
            Defect(
                "installation_id_in_key",
                "partitions:no_installation_id_in_template",
                "absent",
                "present in template",
            )
        )
    return checks, defects, summary
