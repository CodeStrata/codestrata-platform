"""Reusable community-cloud-api module contract checks."""

from __future__ import annotations

import re

from infrastructure.verification.contract import (
    AUTHENTICATION_MODE,
    DEPLOYMENT_MODE,
    FORBIDDEN_RESOURCE_TYPES,
    RATE_LIMIT_MODE,
    REQUIRED_OUTPUTS,
    REQUIRED_VARIABLES,
    infra_root,
)
from infrastructure.verification.models import CheckResult


def _module_text() -> str:
    module = infra_root() / "modules" / "community-cloud-api"
    parts: list[str] = []
    for path in sorted(module.glob("*.tf")):
        parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def check_module_contract() -> list[CheckResult]:
    text = _module_text()
    variables = (infra_root() / "modules" / "community-cloud-api" / "variables.tf").read_text(
        encoding="utf-8"
    )
    outputs = (infra_root() / "modules" / "community-cloud-api" / "outputs.tf").read_text(
        encoding="utf-8"
    )
    missing_vars = [name for name in REQUIRED_VARIABLES if f'variable "{name}"' not in variables]
    missing_outs = [name for name in REQUIRED_OUTPUTS if f'output "{name}"' not in outputs]
    forbidden_present = [name for name in FORBIDDEN_RESOURCE_TYPES if f'resource "{name}"' in text]
    lambda_count = len(re.findall(r'resource\s+"aws_lambda_function"', text))
    return [
        CheckResult(
            name="module:required_variables",
            ok=not missing_vars,
            detail="ok" if not missing_vars else ",".join(missing_vars[:8]),
            category="module",
        ),
        CheckResult(
            name="module:required_outputs",
            ok=not missing_outs,
            detail="ok" if not missing_outs else ",".join(missing_outs[:8]),
            category="module",
        ),
        CheckResult(
            name="module:no_forbidden_resources",
            ok=not forbidden_present,
            detail="ok" if not forbidden_present else ",".join(forbidden_present),
            category="module",
            scenario="D",
        ),
        CheckResult(
            name="module:one_lambda",
            ok=lambda_count == 1,
            detail=f"count={lambda_count}",
            category="module",
            scenario="E",
        ),
        CheckResult(
            name="module:deployment_mode_default",
            ok=DEPLOYMENT_MODE in variables,
            detail=DEPLOYMENT_MODE,
            category="module",
        ),
        CheckResult(
            name="module:auth_mode_default",
            ok=AUTHENTICATION_MODE in variables,
            detail=AUTHENTICATION_MODE,
            category="module",
        ),
        CheckResult(
            name="module:rate_limit_mode_default",
            ok=RATE_LIMIT_MODE in variables,
            detail=RATE_LIMIT_MODE,
            category="module",
        ),
        CheckResult(
            name="module:ingestion_disabled_default",
            ok='variable "enable_ingestion"' in variables
            and "default     = false" in variables,
            detail="enable_ingestion=false",
            category="module",
        ),
        CheckResult(
            name="module:no_secret_outputs",
            ok=all(
                token not in outputs.lower()
                for token in ("password", "secret", "token", "credential", "fingerprint")
            ),
            detail="safe outputs",
            category="module",
        ),
        CheckResult(
            name="module:no_account_hardcoding",
            ok=not re.search(r"\b\d{12}\b", text),
            detail="no hardcoded account id",
            category="module",
        ),
    ]
