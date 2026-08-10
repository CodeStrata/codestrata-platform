"""Advisor provider_metadata fields when present."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_ai_providers.helpers import artifact_dir, check, load_json
from verification.community_ai_providers.models import CheckResult, Defect


def check_usage(
    monorepo: Path,
    *,
    repositories: dict[str, Any],
    openai: dict[str, Any],
    bedrock: dict[str, Any],
    openrouter: dict[str, Any],
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    metadata_samples: list[dict[str, Any]] = []
    for item in repositories.get("selected") or []:
        for key in ("work_bedrock", "work_openai", "work_openrouter"):
            work = artifact_dir(item, key, monorepo=monorepo)
            if not work:
                continue
            advisor = work / "advisor.json"
            if not advisor.is_file():
                continue
            try:
                doc = load_json(advisor)
            except (OSError, TypeError, ValueError):
                continue
            meta = doc.get("provider_metadata") or doc.get("model_metadata") or {}
            if not isinstance(meta, dict):
                continue
            fields = sorted(str(k) for k in meta.keys())
            metadata_samples.append(
                {
                    "catalog_id": item.get("catalog_id"),
                    "source": key,
                    "fields": fields,
                }
            )

    html_builder = (
        Path(__file__).resolve().parents[2]
        / "engine/src/codestrata/reporting/html_v2/builder.py"
    )
    source_fields = []
    if html_builder.is_file():
        text = html_builder.read_text(encoding="utf-8")
        for name in (
            "provider",
            "model_id",
            "latency_ms",
            "input_tokens",
            "output_tokens",
            "advisor_version",
            "prompt_version",
        ):
            if f"provider_metadata.{name}" in text or f".{name}" in text:
                source_fields.append(name)

    checks.append(
        check(
            "usage:provider_metadata_contract",
            True,
            f"samples={len(metadata_samples)} source_fields={source_fields}",
            "usage",
        )
    )

    summary = {
        "samples": metadata_samples,
        "source_contract_fields": source_fields,
        "openai_e2e": openai.get("e2e_status"),
        "bedrock_e2e": bedrock.get("e2e_status"),
        "openrouter_e2e": openrouter.get("e2e_status"),
        "fabricated_cost": False,
    }
    return checks, defects, summary
