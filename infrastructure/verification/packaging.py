"""Dockerfile / packaging structural verification."""

from __future__ import annotations

from infrastructure.verification.contract import repo_root
from infrastructure.verification.models import CheckResult


def check_packaging() -> list[CheckResult]:
    root = repo_root()
    dockerfile = (
        root / "platform" / "deployment" / "community-cloud-api" / "Dockerfile"
    ).read_text(encoding="utf-8")
    dockerignore = (
        root / "platform" / "deployment" / "community-cloud-api" / ".dockerignore"
    ).read_text(encoding="utf-8")
    return [
        CheckResult(
            name="packaging:dockerfile_present",
            ok=(root / "platform/deployment/community-cloud-api/Dockerfile").is_file(),
            detail="Dockerfile",
            category="packaging",
        ),
        CheckResult(
            name="packaging:lambda_python_base",
            ok="public.ecr.aws/lambda/python" in dockerfile and "3.12" in dockerfile,
            detail="lambda python 3.12",
            category="packaging",
        ),
        CheckResult(
            name="packaging:platform_lambda_extra",
            ok="platform[lambda]" in dockerfile,
            detail="mangum extra",
            category="packaging",
        ),
        CheckResult(
            name="packaging:handler_cmd",
            ok="codestrata_platform.community_cloud_api.deployment.lambda_handler.handler"
            in dockerfile,
            detail="handler CMD",
            category="packaging",
        ),
        CheckResult(
            name="packaging:fail_closed_env",
            ok=all(
                token in dockerfile
                for token in (
                    "production_foundation",
                    "CODESTRATA_AUTHENTICATION_ENABLED=true",
                    "CODESTRATA_INGESTION_ENABLED=false",
                    "enabled_verifier_unavailable",
                )
            ),
            detail="foundation ENV",
            category="packaging",
        ),
        CheckResult(
            name="packaging:dockerignore_excludes",
            ok=all(
                token in dockerignore
                for token in ("infrastructure", "tests", ".env", "*.tfstate")
            ),
            detail="excludes tests/infra/state",
            category="packaging",
        ),
        CheckResult(
            name="packaging:no_credentials_in_dockerfile",
            ok=all(
                token not in dockerfile
                for token in ("AKIA", "AWS_SECRET", "cscc_v1_", "SECRET_KEY=")
            ),
            detail="no secrets",
            category="packaging",
            scenario="O",
        ),
        CheckResult(
            name="packaging:runtime_src_only",
            ok="engine/src" in dockerfile and "platform/src" in dockerfile,
            detail="src copies only",
            category="packaging",
        ),
    ]
