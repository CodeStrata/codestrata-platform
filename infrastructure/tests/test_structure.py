"""Infrastructure directory structure (Slice 7.14)."""

from __future__ import annotations

import re
from pathlib import Path

INFRA = Path(__file__).resolve().parents[1]
REPO = INFRA.parent


def test_top_level_infrastructure_exists() -> None:
    assert INFRA.is_dir()
    assert (INFRA / "README.md").is_file()
    assert (INFRA / ".gitignore").is_file()


def test_required_subdirectories() -> None:
    for rel in (
        "docs",
        "modules/community-cloud-api",
        "production",
        "policies",
        "scripts",
        "tests",
    ):
        assert (INFRA / rel).is_dir(), rel


def test_no_dev_or_staging_roots() -> None:
    assert not (INFRA / "dev").exists()
    assert not (INFRA / "staging").exists()


def test_community_data_lake_module_exists() -> None:
    assert (INFRA / "modules" / "community-data-lake").is_dir()
    assert not (INFRA / "modules" / "data-lake").exists()


def test_docs_present() -> None:
    for name in (
        "architecture.md",
        "deployment.md",
        "state-management.md",
        "security-boundary.md",
        "future-data-lake.md",
    ):
        assert (INFRA / "docs" / name).is_file(), name


def test_module_files_present() -> None:
    module = INFRA / "modules" / "community-cloud-api"
    for name in (
        "main.tf",
        "variables.tf",
        "outputs.tf",
        "versions.tf",
        "api_gateway.tf",
        "lambda.tf",
        "iam.tf",
        "ecr.tf",
        "logging.tf",
        "throttling.tf",
        "configuration.tf",
        "validation.tf",
    ):
        assert (module / name).is_file(), name


def test_data_lake_module_files_present() -> None:
    module = INFRA / "modules" / "community-data-lake"
    for name in (
        "main.tf",
        "variables.tf",
        "outputs.tf",
        "versions.tf",
        "locals.tf",
        "storage.tf",
        "encryption.tf",
        "lifecycle.tf",
        "iam.tf",
        "validation.tf",
        "README.md",
    ):
        assert (module / name).is_file(), name


def test_production_root_files() -> None:
    prod = INFRA / "production"
    for name in (
        "main.tf",
        "variables.tf",
        "outputs.tf",
        "providers.tf",
        "versions.tf",
        "backend.tf.example",
        "terraform.tfvars.example",
        "community-data-lake.tf",
    ):
        assert (prod / name).is_file(), name
    assert not (prod / "backend.tf").exists()
    assert not (prod / "terraform.tfvars").exists()


def test_scripts_present_and_non_destructive() -> None:
    scripts = INFRA / "scripts"
    for name in (
        "build-community-cloud-api.sh",
        "validate.sh",
        "plan-production.sh",
        "smoke-health.sh",
    ):
        path = scripts / name
        assert path.is_file(), name
        text = path.read_text(encoding="utf-8")
        # Forbid the apply auto-approve flag; prose may mention the concept.
        assert "-auto-approve" not in text
        # Scripts must not invoke apply (comments/prose may say apply is refused).
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if re.search(r"\b(never|not|no)\b.*\bapply\b", stripped, re.I):
                continue
            assert not re.search(r"\b(tofu|terraform)\s+apply\b", stripped), name


def test_gitignore_protects_state() -> None:
    ignore = (INFRA / ".gitignore").read_text(encoding="utf-8")
    for needle in (".terraform/", "*.tfstate", "*.tfplan", "terraform.tfvars"):
        assert needle in ignore


def test_no_committed_state_or_plans() -> None:
    forbidden_suffixes = (".tfstate", ".tfstate.backup", ".tfplan")
    for path in INFRA.rglob("*"):
        if not path.is_file():
            continue
        name = path.name
        assert not name.endswith(forbidden_suffixes)
        assert name not in {".terraform", "crash.log"}
        if path.suffix == ".tfstate":
            raise AssertionError(path)
