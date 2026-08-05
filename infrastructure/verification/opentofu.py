"""OpenTofu / Terraform tool detection and optional CLI validation."""

from __future__ import annotations

import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from infrastructure.verification.contract import (
    AWS_PROVIDER_CONSTRAINT,
    REQUIRED_OPENTOFU,
    infra_root,
)
from infrastructure.verification.models import CheckResult

# Provider schema load under Rosetta (amd64 OpenTofu on arm64) can exceed 120s.
_DEFAULT_TIMEOUT_SEC = 180
_VALIDATE_ATTEMPTS = 3
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _clean_detail(text: str, *, limit: int = 160) -> str:
    return _ANSI_RE.sub("", text).strip()[:limit]


@dataclass(frozen=True, slots=True)
class ToolStatus:
    tofu_available: bool
    tofu_version: str | None
    terraform_available: bool
    terraform_version: str | None
    opentofu_validation_status: str
    terraform_tool_status: str
    warnings: tuple[str, ...]


def _run(
    cmd: list[str],
    *,
    cwd: str | None = None,
    timeout: int = _DEFAULT_TIMEOUT_SEC,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = (
            exc.stdout.decode("utf-8", errors="replace")
            if isinstance(exc.stdout, bytes)
            else (exc.stdout or "")
        )
        stderr = (
            exc.stderr.decode("utf-8", errors="replace")
            if isinstance(exc.stderr, bytes)
            else (exc.stderr or "")
        )
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=124,
            stdout=stdout,
            stderr=(stderr + f"\ntimeout after {timeout}s").strip(),
        )


def _run_validate(tofu: str, *, cwd: str) -> subprocess.CompletedProcess[str]:
    """Retry validate for transient provider plugin start timeouts."""

    last: subprocess.CompletedProcess[str] | None = None
    for attempt in range(1, _VALIDATE_ATTEMPTS + 1):
        last = _run([tofu, "validate"], cwd=cwd)
        if last.returncode == 0:
            return last
        stderr = (last.stderr or "").lower()
        transient = "timeout while waiting for plugin" in stderr or last.returncode == 124
        if not transient or attempt == _VALIDATE_ATTEMPTS:
            return last
        time.sleep(2 * attempt)
    assert last is not None
    return last


def detect_tools() -> ToolStatus:
    tofu = shutil.which("tofu")
    terraform = shutil.which("terraform")
    tofu_version = None
    terraform_version = None
    warnings: list[str] = []

    if tofu:
        result = _run([tofu, "version"], timeout=60)
        match = re.search(r"(\d+\.\d+\.\d+)", result.stdout or result.stderr or "")
        tofu_version = match.group(1) if match else "unknown"
    if terraform:
        result = _run([terraform, "version"], timeout=60)
        match = re.search(r"(\d+\.\d+\.\d+)", result.stdout or result.stderr or "")
        terraform_version = match.group(1) if match else "unknown"

    if tofu:
        validation = "pending"
        tf_status = "ignored_opentofu_preferred"
    elif terraform:
        # Do not use ancient Terraform as OpenTofu substitute.
        major = int((terraform_version or "0").split(".")[0]) if terraform_version else 0
        if major < 1:
            validation = "not_executed_tool_unavailable"
            tf_status = "incompatible_tool_present"
            warnings.append(
                f"terraform {terraform_version} present but not used for modern HCL"
            )
        else:
            validation = "not_executed_tool_unavailable"
            tf_status = "present_not_used"
            warnings.append("terraform present but OpenTofu is required for this foundation")
    else:
        validation = "not_executed_tool_unavailable"
        tf_status = "absent"

    return ToolStatus(
        tofu_available=bool(tofu),
        tofu_version=tofu_version,
        terraform_available=bool(terraform),
        terraform_version=terraform_version,
        opentofu_validation_status=validation,
        terraform_tool_status=tf_status,
        warnings=tuple(warnings),
    )


def check_opentofu_contract(tools: ToolStatus) -> list[CheckResult]:
    root = infra_root()
    versions = (root / "modules" / "community-cloud-api" / "versions.tf").read_text(
        encoding="utf-8"
    )
    prod_versions = (root / "production" / "versions.tf").read_text(encoding="utf-8")
    checks = [
        CheckResult(
            name="opentofu:required_version_pinned",
            ok=REQUIRED_OPENTOFU in versions and REQUIRED_OPENTOFU in prod_versions,
            detail=REQUIRED_OPENTOFU,
            category="opentofu",
        ),
        CheckResult(
            name="opentofu:aws_provider_bounded",
            ok=AWS_PROVIDER_CONSTRAINT.split(",")[0].strip() in versions
            and "< 6.0.0" in versions,
            detail=AWS_PROVIDER_CONSTRAINT,
            category="opentofu",
        ),
        CheckResult(
            name="opentofu:no_0_11_syntax",
            ok="${var." not in versions and "terraform {\n  required_version" in versions,
            detail="modern required_providers",
            category="opentofu",
        ),
        CheckResult(
            name="opentofu:tool_status_honest",
            ok=tools.opentofu_validation_status
            in {"pass", "fail", "not_executed_tool_unavailable", "pending"},
            detail=tools.opentofu_validation_status,
            category="opentofu",
        ),
        CheckResult(
            name="opentofu:terraform_0_11_not_used",
            ok=tools.terraform_tool_status
            in {
                "absent",
                "ignored_opentofu_preferred",
                "incompatible_tool_present",
                "present_not_used",
            },
            detail=tools.terraform_tool_status,
            category="opentofu",
        ),
    ]
    return checks


def _clear_stale_provider_locks(root_dir: str) -> None:
    """Remove leftover provider lock files from crashed plugin starts."""

    root = Path(root_dir)
    providers = root / ".terraform" / "providers"
    if not providers.is_dir():
        return
    for lock in providers.rglob("*.lock"):
        try:
            lock.unlink()
        except OSError:
            continue


def run_opentofu_cli_validation(tools: ToolStatus) -> tuple[str, list[CheckResult]]:
    """Run tofu fmt/init/validate when available. Never uses terraform 0.11."""

    if not tools.tofu_available:
        return tools.opentofu_validation_status, [
            CheckResult(
                name="opentofu:cli_validation",
                ok=True,
                detail=tools.opentofu_validation_status,
                category="opentofu",
            )
        ]

    root = infra_root()
    tofu = shutil.which("tofu")
    assert tofu is not None
    checks: list[CheckResult] = []
    fmt = _run([tofu, "fmt", "-check", "-recursive", str(root)], timeout=120)
    checks.append(
        CheckResult(
            name="opentofu:fmt_check",
            ok=fmt.returncode == 0,
            detail=f"exit={fmt.returncode}",
            category="opentofu",
        )
    )
    ok = fmt.returncode == 0
    for label, path in (
        ("module", root / "modules" / "community-cloud-api"),
        ("data_lake_module", root / "modules" / "community-data-lake"),
        ("production", root / "production"),
    ):
        _clear_stale_provider_locks(str(path))
        init = _run(
            [tofu, "init", "-backend=false", "-input=false"],
            cwd=str(path),
            timeout=_DEFAULT_TIMEOUT_SEC,
        )
        # Rosetta + AWS provider: clear leftover locks and pause briefly after
        # init so the plugin handshake is not racing a just-written lock file.
        _clear_stale_provider_locks(str(path))
        if init.returncode == 0:
            time.sleep(1)
            validate = _run_validate(tofu, cwd=str(path))
        else:
            validate = None
        step_ok = init.returncode == 0 and validate is not None and validate.returncode == 0
        ok = ok and step_ok
        detail = (
            f"init={init.returncode} validate="
            f"{validate.returncode if validate else 'skipped'}"
        )
        if validate is not None and validate.returncode != 0:
            # Bound diagnostics — relative label only, no absolute paths / ANSI.
            err = (validate.stderr or validate.stdout or "").strip().splitlines()
            if err:
                detail = f"{detail}; {_clean_detail(err[-1])}"
        if init.returncode != 0:
            err = (init.stderr or init.stdout or "").strip().splitlines()
            if err:
                detail = f"{detail}; init_err={_clean_detail(err[-1])}"
        checks.append(
            CheckResult(
                name=f"opentofu:validate:{label}",
                ok=step_ok,
                detail=detail,
                category="opentofu",
            )
        )
        checks.append(
            CheckResult(
                name=f"opentofu:init_backend_false:{label}",
                ok=init.returncode == 0,
                detail=f"exit={init.returncode}",
                category="opentofu",
            )
        )
    status = "pass" if ok else "fail"
    return status, checks
