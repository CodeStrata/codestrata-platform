"""Report serialization determinism."""

from __future__ import annotations

import json

from verification.documentation_deployment.contract import SCHEMA_NAME, SCHEMA_VERSION
from verification.documentation_deployment.models import CheckResult, DocumentationDeploymentReport


def check_determinism(report: DocumentationDeploymentReport) -> list[CheckResult]:
    checks: list[CheckResult] = []

    first = json.dumps(report.to_dict(), indent=2, sort_keys=True)
    second = json.dumps(report.to_dict(), indent=2, sort_keys=True)

    checks.append(
        CheckResult(
            "determinism:serialization_stable",
            first == second,
            "stable",
            "determinism",
        )
    )
    checks.append(
        CheckResult(
            "determinism:no_absolute_paths",
            "/Users/" not in first and "/home/" not in first,
            "clean",
            "determinism",
        )
    )
    checks.append(
        CheckResult(
            "determinism:schema_identity",
            report.schema_name == SCHEMA_NAME and report.schema_version == SCHEMA_VERSION,
            f"{SCHEMA_NAME}:{SCHEMA_VERSION}",
            "determinism",
        )
    )
    return checks
