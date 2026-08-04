"""Lambda configuration static verification."""

from __future__ import annotations

from infrastructure.verification.contract import LAMBDA_ARCHITECTURE_DEFAULT, infra_root
from infrastructure.verification.models import CheckResult


def check_lambda_config() -> list[CheckResult]:
    text = (infra_root() / "modules" / "community-cloud-api" / "lambda.tf").read_text(
        encoding="utf-8"
    )
    config = (
        infra_root() / "modules" / "community-cloud-api" / "configuration.tf"
    ).read_text(encoding="utf-8")
    return [
        CheckResult(
            name="lambda:one_function",
            ok=text.count('resource "aws_lambda_function"') == 1,
            detail="one function",
            category="lambda",
            scenario="E",
        ),
        CheckResult(
            name="lambda:container_image",
            ok="package_type" in text and '"Image"' in text,
            detail="Image",
            category="lambda",
        ),
        CheckResult(
            name="lambda:architecture_supported",
            ok=LAMBDA_ARCHITECTURE_DEFAULT in text or "architectures" in text,
            detail=LAMBDA_ARCHITECTURE_DEFAULT,
            category="lambda",
        ),
        CheckResult(
            name="lambda:no_vpc",
            ok="vpc_config" not in text,
            detail="no VPC",
            category="lambda",
        ),
        CheckResult(
            name="lambda:env_allowlisted",
            ok=all(
                key in config
                for key in (
                    "CODESTRATA_DEPLOYMENT_MODE",
                    "CODESTRATA_AUTHENTICATION_ENABLED",
                    "CODESTRATA_RATE_LIMIT_ENABLED",
                    "CODESTRATA_INGESTION_ENABLED",
                )
            ),
            detail="foundation env keys",
            category="lambda",
        ),
        CheckResult(
            name="lambda:ingestion_env_false",
            ok="CODESTRATA_INGESTION_ENABLED" in config
            and "enable_ingestion" in config,
            detail="ingestion from enable_ingestion",
            category="lambda",
        ),
        CheckResult(
            name="lambda:no_endpoint_specific_functions",
            ok="telemetry" not in text.lower() or "function" in text.lower(),
            detail="single shared function",
            category="lambda",
            scenario="F",
        ),
    ]
