"""OpenTofu boundary tests for SV.16."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from verification.release_artifacts.opentofu import check_opentofu


def test_opentofu_unavailable_is_blocked_without_waiver() -> None:
    fake_tools = MagicMock()
    fake_tools.tofu_available = False
    fake_tools.terraform_available = True
    fake_tools.terraform_version = "1.9.0"
    fake_tools.opentofu_validation_status = "not_executed_tool_unavailable"

    with patch("verification.release_artifacts.opentofu.detect_tools", return_value=fake_tools):
        with patch("verification.release_artifacts.opentofu.check_opentofu_contract", return_value=[]):
            checks, _defects, blockers, status = check_opentofu(waiver=False)

    assert status == "BLOCKED"
    assert any(b.code == "opentofu_unavailable" for b in blockers)
    assert any(c.name == "opentofu:terraform_not_substitute" for c in checks)


def test_opentofu_never_plan_or_apply_check() -> None:
    fake_tools = MagicMock()
    fake_tools.tofu_available = True
    fake_tools.tofu_version = "1.9.0"
    fake_tools.terraform_available = False
    fake_tools.opentofu_validation_status = "pending"

    with patch("verification.release_artifacts.opentofu.detect_tools", return_value=fake_tools):
        with patch("verification.release_artifacts.opentofu.check_opentofu_contract", return_value=[]):
            with patch(
                "verification.release_artifacts.opentofu.run_opentofu_cli_validation",
                return_value=("pass", []),
            ):
                checks, _defects, blockers, _status = check_opentofu(waiver=False)

    assert not blockers
    assert any(c.name == "opentofu:no_plan_or_apply" and c.ok for c in checks)
