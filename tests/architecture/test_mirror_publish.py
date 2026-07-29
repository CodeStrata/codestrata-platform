"""Focused tests for guarded repository mirror publishing."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"


@pytest.fixture(scope="module")
def publish_mod():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    from release import mirror_publish

    return mirror_publish


@pytest.fixture(scope="module")
def cli_mod():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(
        "publish_repository_mirrors_cli",
        SCRIPTS / "publish-repository-mirrors.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def staging_export(tmp_path: Path, publish_mod):
    from release.extraction import tree_fingerprint

    staging = tmp_path / "staging" / "codestrata-examples"
    staging.mkdir(parents=True)
    (staging / "README.md").write_text("# examples\n", encoding="utf-8")
    (staging / "LICENSE").write_text("MIT\n", encoding="utf-8")
    fingerprint = {
        key: value
        for key, value in tree_fingerprint(staging).items()
        if key != publish_mod.SNAPSHOT_NAME
    }
    digest = hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode()).hexdigest()
    source_commit = "abc123deadbeef"
    snapshot = {
        "export_name": "codestrata-examples",
        "source_commit": source_commit,
        "content_fingerprint": digest,
        "file_count": len(fingerprint),
    }
    (staging / publish_mod.SNAPSHOT_NAME).write_text(
        json.dumps(snapshot, indent=2) + "\n", encoding="utf-8"
    )
    return staging, source_commit


def _examples_export() -> dict:
    return {
        "name": "codestrata-examples",
        "owner": "CodeStrata",
        "repository": "codestrata-examples",
        "destination_repository": "codestrata-examples",
        "visibility": "public",
        "source_root": "examples",
    }


def test_manifest_owner_repository_and_visibility() -> None:
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    from release.inventory import (
        destination_full_name,
        destination_owner,
        destination_repository,
        export_visibility,
        load_export_manifest,
    )

    manifest = load_export_manifest(REPO_ROOT)
    by_name = {item["name"]: item for item in manifest["exports"]}
    assert destination_owner(by_name["codestrata-engine"]) == "CodeStrata"
    assert destination_repository(by_name["codestrata-engine"]) == "codestrata-engine"
    assert destination_full_name(by_name["codestrata-docs"]) == "CodeStrata/codestrata-docs"
    assert export_visibility(by_name["codestrata-engine"]) == "public"
    assert export_visibility(by_name["codestrata-examples"]) == "public"
    assert export_visibility(by_name["codestrata-vscode"]) == "private"
    assert export_visibility(by_name["codestrata-cursor"]) == "private"
    assert export_visibility(by_name["codestrata-docs"]) == "private"
    for item in manifest["exports"]:
        assert item.get("owner") == "CodeStrata"
        assert item.get("repository")


def test_select_requires_repo_or_all(publish_mod) -> None:
    manifest = {"exports": [_examples_export()]}
    with pytest.raises(publish_mod.PublishError, match="select repositories"):
        publish_mod.select_exports(manifest, repos=None, publish_all=False)


def test_select_selected_only(publish_mod) -> None:
    manifest = {
        "exports": [
            _examples_export(),
            {
                "name": "codestrata-docs",
                "owner": "CodeStrata",
                "repository": "codestrata-docs",
                "visibility": "private",
            },
        ]
    }
    selected = publish_mod.select_exports(
        manifest, repos=["codestrata-examples"], publish_all=False
    )
    assert [item["name"] for item in selected] == ["codestrata-examples"]


def test_select_all(publish_mod) -> None:
    manifest = {
        "exports": [
            _examples_export(),
            {
                "name": "codestrata-docs",
                "owner": "CodeStrata",
                "repository": "codestrata-docs",
                "visibility": "private",
            },
        ]
    }
    selected = publish_mod.select_exports(manifest, repos=None, publish_all=True)
    assert len(selected) == 2


def test_missing_staging_directory(tmp_path: Path, publish_mod) -> None:
    with pytest.raises(publish_mod.PublishError, match="missing staging directory"):
        publish_mod.build_plan(
            root=REPO_ROOT,
            export=_examples_export(),
            staging_root=tmp_path / "staging",
            source_commit="abc",
            dry_run=True,
            remote_exists_fn=lambda *_: True,
            remote_empty_fn=lambda *_: True,
            visibility_lookup=lambda *_: "public",
        )


def test_snapshot_mismatch(publish_mod, staging_export) -> None:
    staging, _source_commit = staging_export
    with pytest.raises(publish_mod.PublishError, match="does not match current HEAD"):
        publish_mod.build_plan(
            root=REPO_ROOT,
            export=_examples_export(),
            staging_root=staging.parent,
            source_commit="different",
            dry_run=True,
            remote_exists_fn=lambda *_: True,
            remote_empty_fn=lambda *_: True,
            visibility_lookup=lambda *_: "public",
        )


def test_snapshot_exclusion_from_publishable_files(publish_mod, staging_export) -> None:
    staging, _ = staging_export
    files = publish_mod.iter_publishable_files(staging)
    names = {path.name for path in files}
    assert publish_mod.SNAPSHOT_NAME not in names
    assert "README.md" in names


def test_incorrect_visibility_public(publish_mod, staging_export) -> None:
    staging, source_commit = staging_export
    with pytest.raises(publish_mod.PublishError, match="expected public"):
        publish_mod.build_plan(
            root=REPO_ROOT,
            export=_examples_export(),
            staging_root=staging.parent,
            source_commit=source_commit,
            dry_run=True,
            remote_exists_fn=lambda *_: True,
            remote_empty_fn=lambda *_: True,
            visibility_lookup=lambda *_: "private",
        )


def test_private_visibility_unverifiable(publish_mod) -> None:
    with pytest.raises(publish_mod.PublishError, match="cannot verify private"):
        publish_mod.verify_visibility(
            owner="CodeStrata",
            repository="codestrata-docs",
            expected="private",
            lookup=lambda *_: None,
        )


def test_missing_remote_repository(publish_mod, staging_export) -> None:
    staging, source_commit = staging_export
    with pytest.raises(publish_mod.PublishError, match="remote repository missing"):
        publish_mod.build_plan(
            root=REPO_ROOT,
            export=_examples_export(),
            staging_root=staging.parent,
            source_commit=source_commit,
            dry_run=True,
            remote_exists_fn=lambda *_: False,
            remote_empty_fn=lambda *_: True,
            visibility_lookup=lambda *_: "public",
        )


def test_existing_repository_normal_update_plan(publish_mod, staging_export) -> None:
    staging, source_commit = staging_export
    plan = publish_mod.build_plan(
        root=REPO_ROOT,
        export=_examples_export(),
        staging_root=staging.parent,
        source_commit=source_commit,
        dry_run=True,
        remote_exists_fn=lambda *_: True,
        remote_empty_fn=lambda *_: False,
        visibility_lookup=lambda *_: "public",
    )
    assert plan.action == "dry-run-update"
    assert plan.full_name == "CodeStrata/codestrata-examples"
    assert "force_push=forbidden" in plan.notes


def test_bootstrap_plan_for_empty_remote(publish_mod, staging_export) -> None:
    staging, source_commit = staging_export
    plan = publish_mod.build_plan(
        root=REPO_ROOT,
        export=_examples_export(),
        staging_root=staging.parent,
        source_commit=source_commit,
        dry_run=False,
        remote_exists_fn=lambda *_: True,
        remote_empty_fn=lambda *_: True,
        visibility_lookup=lambda *_: "public",
    )
    assert plan.action == "bootstrap"


def test_cli_rejects_force(cli_mod) -> None:
    assert cli_mod.main(["--force", "--all"]) == 2


def test_cli_push_requires_confirm(cli_mod) -> None:
    assert cli_mod.main(["--all", "--push"]) == 2


def test_cli_default_requires_selection(cli_mod, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli_mod, "source_is_clean", lambda _root: True)
    assert cli_mod.main([]) == 1


def test_cli_dry_run_selected(cli_mod, monkeypatch: pytest.MonkeyPatch, staging_export) -> None:
    import release.mirror_publish as mp

    staging, source_commit = staging_export
    monkeypatch.setattr(cli_mod, "source_is_clean", lambda _root: True)
    monkeypatch.setattr(cli_mod, "current_source_commit", lambda _root: source_commit)
    monkeypatch.setattr(
        cli_mod,
        "build_plan",
        lambda **kwargs: mp.build_plan(
            **kwargs,
            remote_exists_fn=lambda *_: True,
            remote_empty_fn=lambda *_: False,
            visibility_lookup=lambda *_: "public",
        ),
    )
    code = cli_mod.main(
        [
            "--staging",
            str(staging.parent),
            "--repo",
            "codestrata-examples",
        ]
    )
    assert code == 0


def test_cli_all_dry_run(cli_mod, monkeypatch: pytest.MonkeyPatch, staging_export) -> None:
    import release.mirror_publish as mp

    staging, source_commit = staging_export
    # Only examples staging exists; restrict manifest selection via --repo path...
    # For --all, fake select_exports to return one export.
    monkeypatch.setattr(cli_mod, "source_is_clean", lambda _root: True)
    monkeypatch.setattr(cli_mod, "current_source_commit", lambda _root: source_commit)
    monkeypatch.setattr(
        cli_mod,
        "select_exports",
        lambda manifest, repos, publish_all: [_examples_export()] if publish_all else [],
    )
    monkeypatch.setattr(
        cli_mod,
        "build_plan",
        lambda **kwargs: mp.build_plan(
            **kwargs,
            remote_exists_fn=lambda *_: True,
            remote_empty_fn=lambda *_: True,
            visibility_lookup=lambda *_: "public",
        ),
    )
    assert cli_mod.main(["--staging", str(staging.parent), "--all"]) == 0


def test_copy_excludes_snapshot(tmp_path: Path, publish_mod, staging_export) -> None:
    staging, _ = staging_export
    worktree = tmp_path / "work"
    worktree.mkdir()
    (worktree / ".git").mkdir()
    publish_mod.copy_staging_into_worktree(staging, worktree)
    assert not (worktree / publish_mod.SNAPSHOT_NAME).exists()
    assert (worktree / "README.md").is_file()
    assert (worktree / ".git").is_dir()


def test_dirty_source_guard(cli_mod, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli_mod, "source_is_clean", lambda _root: False)
    assert cli_mod.main(["--repo", "codestrata-examples"]) == 1
