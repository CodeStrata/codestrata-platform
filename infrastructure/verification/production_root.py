"""Production root verification."""

from __future__ import annotations

from infrastructure.verification.contract import (
    AUTHENTICATION_MODE,
    DEPLOYMENT_MODE,
    ENVIRONMENT_NAME,
    RATE_LIMIT_MODE,
    infra_root,
)
from infrastructure.verification.models import CheckResult


def check_production_root() -> list[CheckResult]:
    root = infra_root() / "production"
    main = (root / "main.tf").read_text(encoding="utf-8")
    return [
        CheckResult(
            name="production:environment_name",
            ok=f'environment_name         = "{ENVIRONMENT_NAME}"' in main
            or f'environment_name = "{ENVIRONMENT_NAME}"' in main,
            detail=ENVIRONMENT_NAME,
            category="production",
        ),
        CheckResult(
            name="production:one_module",
            ok=main.count("module ") == 1 and "community_cloud_api" in main,
            detail="community_cloud_api",
            category="production",
        ),
        CheckResult(
            name="production:deployment_mode",
            ok=DEPLOYMENT_MODE in main,
            detail=DEPLOYMENT_MODE,
            category="production",
        ),
        CheckResult(
            name="production:auth_mode",
            ok=AUTHENTICATION_MODE in main,
            detail=AUTHENTICATION_MODE,
            category="production",
        ),
        CheckResult(
            name="production:rate_limit_mode",
            ok=RATE_LIMIT_MODE in main,
            detail=RATE_LIMIT_MODE,
            category="production",
        ),
        CheckResult(
            name="production:ingestion_disabled",
            ok="enable_ingestion         = false" in main
            or "enable_ingestion = false" in main,
            detail="enable_ingestion=false",
            category="production",
        ),
        CheckResult(
            name="production:backend_example_only",
            ok=(root / "backend.tf.example").is_file()
            and not (root / "backend.tf").exists(),
            detail="backend.tf.example",
            category="production",
        ),
        CheckResult(
            name="production:no_tfvars_committed",
            ok=not (root / "terraform.tfvars").exists()
            and (root / "terraform.tfvars.example").is_file(),
            detail="example only",
            category="production",
        ),
        CheckResult(
            name="production:no_workspace_switching",
            ok="terraform.workspace" not in main,
            detail="no workspace env switching",
            category="production",
        ),
    ]
