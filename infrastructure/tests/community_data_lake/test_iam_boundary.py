"""Module isolation boundary for community-data-lake IAM (Slice 8.12)."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
REPO_ROOT = INFRA.parent
LAKE_MODULE = INFRA / "modules" / "community-data-lake"
API_MODULE = INFRA / "modules" / "community-cloud-api"


def _blob(module: Path) -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in module.glob("*.tf"))


def test_lake_module_has_no_python_imports() -> None:
    blob = _blob(LAKE_MODULE)
    for token in ("import codestrata", "from codestrata", ".py", "boto3"):
        assert token not in blob


def test_engine_and_platform_python_not_referenced_in_lake_hcl() -> None:
    blob = _blob(LAKE_MODULE)
    for token in (
        "engine/src",
        "platform/src",
        "codestrata_platform",
        "community_cloud_api",
    ):
        assert token not in blob


def test_community_cloud_api_module_still_independent() -> None:
    blob = _blob(API_MODULE)
    assert "community-data-lake" not in blob
    assert "community_data_lake" not in blob


def test_no_cross_module_python_paths_in_production_root() -> None:
    prod = INFRA / "production"
    for tf in prod.glob("*.tf"):
        text = tf.read_text(encoding="utf-8")
        assert "codestrata_platform" not in text
        assert "engine/src" not in text
