"""Docker packaging structural checks (no build/push by default)."""

from __future__ import annotations

from pathlib import Path

from verification.release_artifacts.models import CheckResult, Warning

_DOCKERFILE = Path("platform/deployment/community-cloud-api/Dockerfile")
_DOCKERIGNORE = Path("platform/deployment/community-cloud-api/.dockerignore")


def check_docker_packaging(monorepo: Path) -> tuple[list[CheckResult], list[Warning]]:
    checks: list[CheckResult] = []
    warnings: list[Warning] = []

    dockerfile = monorepo / _DOCKERFILE
    dockerignore = monorepo / _DOCKERIGNORE

    checks.append(
        CheckResult(
            name="docker:dockerfile_present",
            ok=dockerfile.is_file(),
            detail=str(_DOCKERFILE),
            category="docker_packaging",
        )
    )
    checks.append(
        CheckResult(
            name="docker:dockerignore_present",
            ok=dockerignore.is_file(),
            detail=str(_DOCKERIGNORE),
            category="docker_packaging",
        )
    )

    if dockerfile.is_file():
        text = dockerfile.read_text(encoding="utf-8")
        checks.extend(
            [
                CheckResult(
                    name="docker:uses_lambda_base",
                    ok="lambda/python" in text,
                    detail="AWS Lambda Python base image",
                    category="docker_packaging",
                ),
                CheckResult(
                    name="docker:copies_engine_and_platform",
                    ok="engine/src" in text and "platform/src" in text,
                    detail="runtime trees only",
                    category="docker_packaging",
                ),
                CheckResult(
                    name="docker:docker_build",
                    ok=True,
                    detail="not_executed: structural review only",
                    category="docker_packaging",
                    status="not_executed",
                ),
            ]
        )

    if dockerignore.is_file():
        ignore_text = dockerignore.read_text(encoding="utf-8")
        for marker in ("docs", "governance", "reports", "validation", ".git"):
            checks.append(
                CheckResult(
                    name=f"docker:dockerignore_excludes_{marker.replace('.', '')}",
                    ok=marker in ignore_text,
                    detail=f"marker={marker}",
                    category="docker_packaging",
                )
            )

    if not dockerfile.is_file():
        warnings.append(
            Warning(
                code="dockerfile_missing",
                detail="Community Cloud API Dockerfile not found",
            )
        )

    return checks, warnings
