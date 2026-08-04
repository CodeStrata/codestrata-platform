"""Platform / export boundary for infrastructure/."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[1]
REPO = INFRA.parent


def test_infrastructure_is_private_export_forbidden() -> None:
    manifest = (REPO / "public-export-manifest.yaml").read_text(encoding="utf-8")
    assert "infrastructure/" in manifest
    assert "infrastructure" in manifest


def test_no_application_source_copied_into_infrastructure() -> None:
    allowed_roots = {
        INFRA / "tests",
        INFRA / "verification",
    }
    for path in INFRA.rglob("*.py"):
        # Root package marker for `python -m infrastructure.verification`.
        if path == INFRA / "__init__.py":
            continue
        if any(
            path == root or root in path.parents or path.parent == root
            for root in allowed_roots
        ):
            continue
        # Only tests + SV.9 verification may contain Python under infrastructure/
        raise AssertionError(f"unexpected application python: {path.relative_to(INFRA)}")


def test_scripts_resolve_repo_root_safely() -> None:
    build = (INFRA / "scripts" / "build-community-cloud-api.sh").read_text(
        encoding="utf-8"
    )
    assert "REPO_ROOT=" in build
    assert "dirname" in build
    assert "/Users/" not in build


def test_dockerfile_is_platform_owned() -> None:
    dockerfile = (
        REPO / "platform" / "deployment" / "community-cloud-api" / "Dockerfile"
    )
    assert dockerfile.is_file()
    text = dockerfile.read_text(encoding="utf-8")
    assert "lambda/python" in text
    assert "codestrata_platform.community_cloud_api.deployment.lambda_handler.handler" in text
    assert "CODESTRATA_INGESTION_ENABLED=false" in text


def test_architecture_docs_mention_extraction() -> None:
    readme = (INFRA / "README.md").read_text(encoding="utf-8")
    assert "codestrata-infrastructure" in readme
    assert "production infrastructure foundation" in readme.lower() or (
        "production infrastructure foundation" in readme
    )
