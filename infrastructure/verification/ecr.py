"""ECR static verification."""

from __future__ import annotations

from infrastructure.verification.contract import infra_root
from infrastructure.verification.models import CheckResult


def check_ecr() -> list[CheckResult]:
    text = (infra_root() / "modules" / "community-cloud-api" / "ecr.tf").read_text(
        encoding="utf-8"
    )
    return [
        CheckResult(
            name="ecr:one_private_repo",
            ok=text.count('resource "aws_ecr_repository"') == 1,
            detail="one repository",
            category="ecr",
        ),
        CheckResult(
            name="ecr:immutable_tags",
            ok='image_tag_mutability = "IMMUTABLE"' in text,
            detail="IMMUTABLE",
            category="ecr",
            scenario="J",
        ),
        CheckResult(
            name="ecr:scan_on_push",
            ok="scan_on_push = true" in text,
            detail="scan_on_push",
            category="ecr",
            scenario="K",
        ),
        CheckResult(
            name="ecr:encryption",
            ok='encryption_type = "AES256"' in text,
            detail="AES256",
            category="ecr",
        ),
        CheckResult(
            name="ecr:lifecycle_policy",
            ok='resource "aws_ecr_lifecycle_policy"' in text
            and "imageCountMoreThan" in text,
            detail="bounded lifecycle",
            category="ecr",
        ),
        CheckResult(
            name="ecr:not_public",
            ok="aws_ecrpublic" not in text.lower() and "force_delete = false" in text,
            detail="private",
            category="ecr",
            scenario="I",
        ),
        CheckResult(
            name="ecr:not_data_lake",
            ok="data-lake" not in text.lower() and "telemetry" not in text.lower(),
            detail="image store only",
            category="ecr",
        ),
    ]
