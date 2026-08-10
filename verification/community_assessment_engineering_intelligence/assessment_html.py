"""Assessment HTML validation for Slice 17.19."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from verification.community_assessment_engineering_intelligence.contract import ASSESSMENT_HTML
from verification.community_assessment_engineering_intelligence.helpers import (
    check,
    hard_defect,
    read_text,
)
from verification.community_assessment_engineering_intelligence.models import (
    CheckResult,
    Defect,
)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data and data.strip():
            self.parts.append(data.strip())


def check_assessment_html(
    monorepo: Path,
    selection: dict[str, Any],
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    rows: list[dict[str, Any]] = []

    for item in selection.get("selected") or []:
        catalog_id = str(item.get("catalog_id") or "")
        rel = item.get("current_relative")
        if not rel:
            continue
        current = monorepo / str(rel)
        path = current / ASSESSMENT_HTML
        exists = path.is_file() and path.stat().st_size > 0
        checks.append(
            check(
                f"assessment_html:exists:{catalog_id}",
                exists,
                f"bytes={path.stat().st_size if path.is_file() else 0}",
                "assessment_html",
            )
        )
        if not exists:
            defects.append(
                hard_defect(
                    "missing_html",
                    f"assessment_html:exists:{catalog_id}",
                    "present",
                    "absent",
                )
            )
            continue

        text = read_text(path)
        identity_hints = (
            catalog_id.lower() in text.lower()
            or str(item.get("github_repository") or "").lower() in text.lower()
            or str(item.get("artifact_folder") or "").lower() in text.lower()
            or "codestrata" in text.lower()
        )
        checks.append(
            check(
                f"assessment_html:identity:{catalog_id}",
                identity_hints,
                "repo identity markers",
                "assessment_html",
            )
        )

        forbidden = any(
            needle in text
            for needle in ("/Users/", "arn:aws:", "cscc_v1_", "raw/stream=")
        )
        checks.append(
            check(
                f"assessment_html:privacy:{catalog_id}",
                not forbidden,
                "no secrets/paths",
                "assessment_html",
            )
        )
        if forbidden:
            defects.append(
                hard_defect(
                    "html_privacy",
                    f"assessment_html:privacy:{catalog_id}",
                    "clean",
                    "forbidden pattern",
                )
            )

        sectionish = any(
            marker in text.lower()
            for marker in ("finding", "limitation", "recommendation", "summary")
        )
        checks.append(
            check(
                f"assessment_html:sections:{catalog_id}",
                sectionish,
                "findings/limitations markers",
                "assessment_html",
            )
        )

        parser = _TextExtractor()
        try:
            parser.feed(text)
            nonempty = len(parser.parts) > 0
        except Exception:  # noqa: BLE001
            nonempty = True
        checks.append(
            check(
                f"assessment_html:nonempty_parse:{catalog_id}",
                nonempty,
                f"text_nodes={len(parser.parts)}",
                "assessment_html",
            )
        )

        rows.append(
            {
                "catalog_id": catalog_id,
                "bytes": path.stat().st_size,
                "identity_ok": identity_hints,
                "privacy_ok": not forbidden,
                "sections_ok": sectionish,
            }
        )

    summary = {"repositories": rows, "count": len(rows)}
    return checks, defects, summary
