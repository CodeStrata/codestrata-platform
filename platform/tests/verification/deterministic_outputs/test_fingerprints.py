"""Tests for fingerprints."""

from __future__ import annotations

from verification.deterministic_outputs.fingerprints import (
    contains_forbidden_environment,
    fingerprint_mapping,
    stable_json_bytes,
)


def test_stable_json_sorts_keys() -> None:
    assert stable_json_bytes({"b": 1, "a": 2}) == stable_json_bytes({"a": 2, "b": 1})


def test_fingerprint_mapping_excludes_volatile() -> None:
    left = fingerprint_mapping({"id": "x", "generated_at": "t1"}, exclude=("generated_at",))
    right = fingerprint_mapping({"id": "x", "generated_at": "t2"}, exclude=("generated_at",))
    assert left == right


def test_repo_relative_users_path_not_forbidden() -> None:
    text = '{"path": "app/Users/Models/User.php", "scope": "database/factories/users/models"}'
    assert contains_forbidden_environment(text) == []


def test_home_runner_ci_path_not_forbidden() -> None:
    text = "Harness privacy scan refined (CI /home/runner paths in OSS evidence)"
    assert contains_forbidden_environment(text) == []


def test_operator_home_path_is_forbidden() -> None:
    text = '{"repo_root": "/Users/developer/clone/project"}'
    assert "operator_home_path" in contains_forbidden_environment(text)
