"""Response validation: enrichment validation functions exist."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_ai_providers.contract import VALIDATION_PY
from verification.community_ai_providers.helpers import check, hard_defect, read_text
from verification.community_ai_providers.models import CheckResult, Defect


def check_response_validation(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    path = monorepo / VALIDATION_PY
    text = read_text(path) if path.is_file() else ""
    has_validate = "def validate_ai_enrichment_result" in text
    has_error = "AiEnrichmentValidationError" in text
    checks.append(
        check(
            "response_validation:validate_fn",
            has_validate,
            "validate_ai_enrichment_result",
            "response_validation",
        )
    )
    checks.append(
        check(
            "response_validation:error_type",
            has_error,
            "AiEnrichmentValidationError",
            "response_validation",
        )
    )
    if not has_validate:
        defects.append(
            hard_defect(
                "missing_validation",
                "response_validation:validate_fn",
                "present",
                "absent",
            )
        )

    # Parsing layer also exists.
    parsing = monorepo / "engine/src/codestrata/ai/enrichment/parsing.py"
    checks.append(
        check(
            "response_validation:parsing_module",
            parsing.is_file(),
            "enrichment/parsing.py",
            "response_validation",
        )
    )

    summary = {
        "validate_ai_enrichment_result": has_validate,
        "referential_id_checks": "allowed_finding_ids / allowed_recommendation_ids",
        "untrusted_provider_output": True,
    }
    return checks, defects, summary
