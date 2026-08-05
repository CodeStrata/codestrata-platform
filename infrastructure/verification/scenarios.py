"""Negative / fixture-based scenario checks (no live infra mutation)."""

from __future__ import annotations

from infrastructure.verification.contract import FORBIDDEN_RESOURCE_TYPES, infra_root
from infrastructure.verification.models import CheckResult


def check_scenarios() -> list[CheckResult]:
    root = infra_root()
    module_blob = "\n".join(
        p.read_text(encoding="utf-8")
        for p in sorted((root / "modules" / "community-cloud-api").glob("*.tf"))
    )
    data_lake_dir = root / "modules" / "community-data-lake"
    data_lake_blob = (
        "\n".join(p.read_text(encoding="utf-8") for p in sorted(data_lake_dir.glob("*.tf")))
        if data_lake_dir.is_dir()
        else ""
    )
    # Controlled in-memory fixtures for negative presence assertions.
    fake_dev = "infrastructure/dev/main.tf"
    fake_second_lambda = 'resource "aws_lambda_function" "telemetry" {}'
    fake_rest = 'resource "aws_api_gateway_rest_api" "legacy" {}'
    fake_public_ecr = "aws_ecrpublic_repository"
    return [
        CheckResult(
            name="scenario:dev_absent",
            ok=not (root / "dev").exists() and fake_dev.startswith("infrastructure/"),
            detail="no live dev root",
            category="scenarios",
            scenario="B",
        ),
        CheckResult(
            name="scenario:staging_absent",
            ok=not (root / "staging").exists(),
            detail="no live staging root",
            category="scenarios",
            scenario="C",
        ),
        CheckResult(
            name="scenario:data_lake_foundation_unwired",
            ok=data_lake_dir.is_dir()
            and 'resource "aws_s3_bucket"' in data_lake_blob
            and "var.enable_ingestion_wire == false" in data_lake_blob
            and 'resource "aws_iam_role"' not in data_lake_blob
            and 'resource "aws_s3_bucket"' not in module_blob
            and "community-data-lake" not in module_blob
            and "community_data_lake" not in module_blob,
            detail="foundation module present, unwired, not in community-cloud-api",
            category="scenarios",
            scenario="D",
        ),
        CheckResult(
            name="scenario:single_lambda",
            ok=module_blob.count('resource "aws_lambda_function"') == 1
            and fake_second_lambda not in module_blob,
            detail="one lambda",
            category="scenarios",
            scenario="E",
        ),
        CheckResult(
            name="scenario:http_not_rest",
            ok=fake_rest not in module_blob
            and 'protocol_type = "HTTP"' in module_blob,
            detail="HTTP API",
            category="scenarios",
            scenario="G",
        ),
        CheckResult(
            name="scenario:private_ecr",
            ok=fake_public_ecr not in module_blob
            and 'image_tag_mutability = "IMMUTABLE"' in module_blob,
            detail="private immutable",
            category="scenarios",
            scenario="I",
        ),
        CheckResult(
            name="scenario:forbidden_types_absent",
            ok=all(f'resource "{name}"' not in module_blob for name in FORBIDDEN_RESOURCE_TYPES),
            detail="no forbidden services",
            category="scenarios",
            scenario="N",
        ),
        CheckResult(
            name="scenario:no_test_verifier_in_hcl",
            ok="UnavailableCommunityCredentialVerifier" not in module_blob
            and "cscc_v1_" not in module_blob,
            detail="no verifier/credentials in HCL",
            category="scenarios",
            scenario="W",
        ),
        CheckResult(
            name="scenario:no_auto_approve",
            ok="--auto-approve" not in (root / "scripts" / "plan-production.sh").read_text(
                encoding="utf-8"
            )
            and "tofu apply" not in (root / "scripts" / "plan-production.sh").read_text(
                encoding="utf-8"
            ),
            detail="plan script safe",
            category="scenarios",
            scenario="S",
        ),
    ]
