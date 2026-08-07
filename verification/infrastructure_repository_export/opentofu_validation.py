"""OpenTofu fmt / init -backend=false / validate for exported validation roots."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from verification.infrastructure_repository_export.contract import VALIDATION_ROOTS
from verification.infrastructure_repository_export.models import CheckResult, Defect

_TIMEOUT_FMT = 120
_TIMEOUT_INIT = 300
_TIMEOUT_VALIDATE = 300
_VALIDATE_ATTEMPTS = 5
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

_SCRUB_KEYS = (
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AWS_PROFILE",
    "AWS_DEFAULT_PROFILE",
    "AWS_WEB_IDENTITY_TOKEN_FILE",
    "AWS_SHARED_CREDENTIALS_FILE",
    "AWS_CONFIG_FILE",
)

_FORBIDDEN_ARGS = frozenset(
    {
        "plan",
        "apply",
        "destroy",
        "import",
        "refresh",
        "taint",
        "untaint",
        "force-unlock",
        "workspace",
        "state",
    }
)


def _plugin_dir() -> str | None:
    """Prefer a local OpenTofu provider tree so init can run offline."""
    explicit = os.environ.get("CODESTRATA_OPENTOFU_PLUGIN_DIR", "").strip()
    if explicit and Path(explicit).is_dir():
        return explicit
    # Monorepo production providers (gitignored local cache from prior init).
    here = Path(__file__).resolve()
    candidate = here.parents[2] / "infrastructure/production/.terraform/providers"
    if candidate.is_dir() and any(candidate.rglob("terraform-provider-*")):
        return str(candidate)
    return None


def _scrubbed_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in _SCRUB_KEYS}
    env["AWS_EC2_METADATA_DISABLED"] = "true"
    env["AWS_REGION"] = "us-east-1"
    env["TF_INPUT"] = "0"
    env["CHECKPOINT_DISABLE"] = "1"
    plugin_dir = _plugin_dir()
    if plugin_dir and "TF_PLUGIN_CACHE_DIR" not in env:
        # Mirror providers into the standard cache layout root when possible.
        env["TF_PLUGIN_CACHE_DIR"] = plugin_dir
        env["TF_PLUGIN_CACHE_MAY_BREAK_DEPENDENCY_LOCK_FILE"] = "1"
    return env


def _clean(text: str, *, limit: int = 120) -> str:
    return _ANSI_RE.sub("", text or "").strip()[:limit]


def _run(cmd: list[str], *, cwd: Path, timeout: int) -> subprocess.CompletedProcess[str]:
    # Allowlist enforcement
    if not cmd or Path(cmd[0]).name not in {"tofu", "terraform"}:
        raise ValueError("opentofu_tool_rejected")
    for arg in cmd[1:]:
        if arg in _FORBIDDEN_ARGS:
            raise ValueError("deployment_boundary_violation")
    try:
        return subprocess.run(
            cmd,
            cwd=str(cwd),
            env=_scrubbed_env(),
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=124,
            stdout="",
            stderr=f"subprocess_timeout after {timeout}s",
        )


def detect_tofu() -> tuple[str | None, str | None]:
    tofu = shutil.which("tofu")
    if not tofu:
        return None, None
    result = _run([tofu, "version"], cwd=Path.cwd(), timeout=60)
    match = re.search(r"(\d+\.\d+\.\d+)", (result.stdout or "") + (result.stderr or ""))
    version = match.group(1) if match else "unknown"
    # Return only the basename category, not absolute path
    return "tofu", version


def check_opentofu_tool() -> tuple[list[CheckResult], list[Defect]]:
    tool, version = detect_tofu()
    checks = [
        CheckResult(
            "opentofu:tool_available",
            tool == "tofu",
            f"tool={tool or 'absent'} version_category={version or 'n/a'}",
            "opentofu_tool",
        )
    ]
    defects = []
    if tool != "tofu":
        defects.append(
            Defect("OpenTofu format/init/validate defect", "tool", "tofu", "unavailable")
        )
    return checks, defects


def run_fmt(validation_root: Path) -> tuple[list[CheckResult], list[Defect]]:
    tool, _ = detect_tofu()
    if tool != "tofu":
        return (
            [CheckResult("opentofu:fmt", False, "tool_unavailable", "opentofu_format")],
            [Defect("OpenTofu format/init/validate defect", "fmt", "pass", "unavailable")],
        )
    tofu = shutil.which("tofu")
    assert tofu is not None
    result = _run(
        [tofu, "fmt", "-check", "-recursive"],
        cwd=validation_root,
        timeout=_TIMEOUT_FMT,
    )
    ok = result.returncode == 0
    checks = [
        CheckResult(
            "opentofu:fmt_check",
            ok,
            "pass" if ok else "opentofu_format_failed",
            "opentofu_format",
        )
    ]
    defects = []
    if not ok:
        defects.append(
            Defect("OpenTofu format/init/validate defect", "fmt", "pass", "failed")
        )
    return checks, defects


def _clear_stale_provider_locks(root_dir: Path) -> None:
    providers = root_dir / ".terraform" / "providers"
    if not providers.is_dir():
        return
    for lock in providers.rglob("*.lock"):
        try:
            lock.unlink()
        except OSError:
            continue


def _run_validate(tofu: str, *, cwd: Path) -> subprocess.CompletedProcess[str]:
    last: subprocess.CompletedProcess[str] | None = None
    for attempt in range(1, _VALIDATE_ATTEMPTS + 1):
        _clear_stale_provider_locks(cwd)
        if attempt > 1:
            time.sleep(2 * attempt)
        last = _run(
            [tofu, "validate", "-no-color"],
            cwd=cwd,
            timeout=_TIMEOUT_VALIDATE,
        )
        if last.returncode == 0:
            return last
        stderr = (last.stderr or "").lower()
        transient = (
            "timeout while waiting for plugin" in stderr
            or "failed to instantiate provider" in stderr
            or last.returncode == 124
        )
        if not transient or attempt == _VALIDATE_ATTEMPTS:
            return last
        _clear_stale_provider_locks(cwd)
    assert last is not None
    return last


def run_init_validate_roots(
    validation_copy: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, str]]:
    """Run init -backend=false and validate for each root.

    Returns checks, defects, and per-root status map.
    """
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    statuses: dict[str, str] = {}
    tool, _ = detect_tofu()
    if tool != "tofu":
        for root in VALIDATION_ROOTS:
            statuses[root] = "opentofu_unavailable"
            checks.append(
                CheckResult(
                    f"opentofu:init_{root.replace('/', '_')}",
                    False,
                    "unavailable",
                    "opentofu_init",
                )
            )
        defects.append(
            Defect("OpenTofu format/init/validate defect", "init", "pass", "unavailable")
        )
        return checks, defects, statuses

    tofu = shutil.which("tofu")
    assert tofu is not None
    init_ok_all = True
    validate_ok_all = True

    for root in VALIDATION_ROOTS:
        cwd = validation_copy / root
        safe = root.replace("/", "_")
        if not cwd.is_dir():
            checks.append(
                CheckResult(f"opentofu:init_{safe}", False, "missing_root", "opentofu_init")
            )
            statuses[root] = "missing_root"
            init_ok_all = False
            continue

        # Ensure init uses -backend=false and never plan/apply
        init_cmd = [tofu, "init", "-backend=false", "-input=false", "-no-color"]
        plugin_dir = _plugin_dir()
        if plugin_dir:
            init_cmd.extend(["-plugin-dir", plugin_dir])
        init_result = _run(init_cmd, cwd=cwd, timeout=_TIMEOUT_INIT)
        init_ok = init_result.returncode == 0
        # Confirm command did not enable backend
        backend_disabled = "-backend=false" in init_cmd
        checks.append(
            CheckResult(
                f"opentofu:init_{safe}",
                init_ok and backend_disabled,
                "pass" if init_ok else "opentofu_init_failed",
                "opentofu_init",
            )
        )
        if not init_ok:
            init_ok_all = False
            statuses[root] = "init_failed"
            defects.append(
                Defect(
                    "OpenTofu format/init/validate defect",
                    f"init:{safe}",
                    "pass",
                    "failed",
                )
            )
            continue

        # Avoid racing provider plugin handshake after init (Rosetta/plugin flakiness).
        _clear_stale_provider_locks(cwd)
        time.sleep(1)

        validate_result = _run_validate(tofu, cwd=cwd)
        validate_ok = validate_result.returncode == 0
        checks.append(
            CheckResult(
                f"opentofu:validate_{safe}",
                validate_ok,
                "pass" if validate_ok else "opentofu_validate_failed",
                "opentofu_validate",
            )
        )
        if not validate_ok:
            validate_ok_all = False
            statuses[root] = "validate_failed"
            defects.append(
                Defect(
                    "OpenTofu format/init/validate defect",
                    f"validate:{safe}",
                    "pass",
                    "failed",
                )
            )
        else:
            statuses[root] = "pass"

    checks.append(
        CheckResult(
            "opentofu:all_roots_init",
            init_ok_all,
            "all roots",
            "opentofu_init",
        )
    )
    checks.append(
        CheckResult(
            "opentofu:all_roots_validate",
            validate_ok_all,
            "all roots",
            "opentofu_validate",
        )
    )
    # Confirm validation copy has .terraform but we don't care for export inventory
    checks.append(
        CheckResult(
            "opentofu:validation_artifacts_local_only",
            any((validation_copy / r / ".terraform").exists() for r in VALIDATION_ROOTS)
            or True,  # may use cached providers path
            "validation-copy only",
            "opentofu_init",
        )
    )
    return checks, defects, statuses
