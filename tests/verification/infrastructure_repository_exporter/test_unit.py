"""Focused unit tests for Infrastructure exporter (Slice 12.6)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from repository_export.destination_layout import validate_destination  # noqa: E402
from repository_export.errors import (  # noqa: E402
    DestinationInsideSource,
    UnsafeDestination,
)
from repository_export.path_rules import approach_a_map, normalize_destination_path  # noqa: E402
from repository_export.permissions import approved_mode_for  # noqa: E402
from repository_export.policy import MODE_EXECUTABLE, MODE_FILE  # noqa: E402
from repository_export.prohibited_files import is_fail_closed_name, is_real_tfvars  # noqa: E402
from repository_export.root_files import generated_gitignore  # noqa: E402
from repository_export.transform import (  # noqa: E402
    generated_boundary_test,
    rewrite_documentation_links,
    rewrite_python_imports,
)


def test_approach_a_mapping() -> None:
    assert (
        approach_a_map("infrastructure/modules/community-cloud-api/main.tf")
        == "modules/community-cloud-api/main.tf"
    )
    assert approach_a_map("infrastructure/README.md") == "README.md"
    assert approach_a_map("infrastructure/__init__.py") is None


def test_path_traversal_rejected() -> None:
    with pytest.raises(Exception):
        normalize_destination_path("../etc/passwd")


def test_prohibited_names() -> None:
    assert is_fail_closed_name("terraform.tfstate")
    assert is_fail_closed_name("run.tfplan")
    assert is_fail_closed_name(".env")
    assert is_real_tfvars("terraform.tfvars")
    assert not is_real_tfvars("terraform.tfvars.example")


def test_destination_inside_source_rejected() -> None:
    with pytest.raises(DestinationInsideSource):
        validate_destination(source_root=ROOT, destination=ROOT / "infrastructure")
    with pytest.raises(DestinationInsideSource):
        validate_destination(source_root=ROOT, destination=ROOT)


def test_gitignore_allows_lockfile() -> None:
    gi = generated_gitignore()
    assert ".terraform/" in gi
    assert not any(line.strip() == ".terraform.lock.hcl" for line in gi.splitlines())


def test_permissions() -> None:
    assert approved_mode_for("scripts/validate.sh") == MODE_EXECUTABLE
    assert approved_mode_for("modules/x/main.tf") == MODE_FILE


def test_import_and_doc_rewrite() -> None:
    src = "from infrastructure.verification.runner import x\n"
    assert "from verification.runner" in rewrite_python_imports(src)
    doc = "See `platform/docs/community-cloud-api/data-lake.md`."
    assert "platform/docs" not in rewrite_documentation_links(doc)
    assert "codestrata_platform" not in generated_boundary_test().split("forbidden")[0]


def test_missing_destination_rejected(tmp_path: Path) -> None:
    _ = tmp_path
    with pytest.raises(UnsafeDestination):
        validate_destination(source_root=ROOT, destination=Path(""))
