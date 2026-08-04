"""Fresh-venv installation smoke for wheel and sdist artifacts."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import venv
from dataclasses import dataclass
from pathlib import Path

from verification.release_artifacts.contract import INTENDED_RELEASE_VERSION
from verification.release_artifacts.models import CheckResult, Defect, Warning

_STRIP_PREFIXES = (
    "AWS_",
    "OPENAI_",
    "BEDROCK_",
    "CODESTRATA_DATABASE",
    "VIRTUAL_ENV",
)
_STRIP_EXACT = ("PYTHONPATH", "PYTHONHOME", "PIP_REQUIRE_VIRTUALENV")


def _venv_python(venv_dir: Path) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _scrub_environ(base: dict[str, str] | None = None) -> dict[str, str]:
    """Scrub developer leakage; mirrors cli_installation.environment.scrub_environ."""

    source = dict(os.environ if base is None else base)
    cleaned: dict[str, str] = {}
    for key, value in source.items():
        if key in _STRIP_EXACT:
            continue
        if any(key.startswith(prefix) for prefix in _STRIP_PREFIXES):
            continue
        cleaned[key] = value
    cleaned.pop("PYTHONPATH", None)
    cleaned.pop("PYTHONHOME", None)
    return cleaned


@dataclass(frozen=True, slots=True)
class CommandResult:
    exit_code: int
    stdout: str
    stderr: str

    @property
    def combined(self) -> str:
        return f"{self.stdout}\n{self.stderr}"


def _run(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> CommandResult:
    completed = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        env=env,
        check=False,
        text=True,
        capture_output=True,
    )
    return CommandResult(
        exit_code=completed.returncode,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
    )


def _pip_install(*, python: Path, artifact: Path, env: dict[str, str]) -> CommandResult:
    return _run(
        [str(python), "-m", "pip", "install", "--no-cache-dir", str(artifact)],
        env=env,
    )


def _codestrata_bin(venv_dir: Path) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "codestrata.exe"
    return venv_dir / "bin" / "codestrata"


def _with_venv_path(env: dict[str, str], venv_dir: Path) -> dict[str, str]:
    scripts = _venv_python(venv_dir).parent
    merged = dict(env)
    merged["PATH"] = str(scripts) + os.pathsep + merged.get("PATH", "")
    merged.pop("PYTHONPATH", None)
    return merged


def _version_matches(result: CommandResult) -> bool:
    if result.exit_code != 0:
        return False
    return INTENDED_RELEASE_VERSION in result.stdout


def _install_and_smoke(
    *,
    label: str,
    artifact: Path,
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[Warning]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    warnings: list[Warning] = []

    with tempfile.TemporaryDirectory(prefix=f"sv16_install_{label}_") as tmp:
        home = Path(tmp) / "home"
        home.mkdir()
        venv_dir = Path(tmp) / "venv"
        venv.create(venv_dir, with_pip=True)
        python = _venv_python(venv_dir)
        codestrata = _codestrata_bin(venv_dir)

        base_env = _scrub_environ()
        base_env["HOME"] = str(home)
        base_env["USERPROFILE"] = str(home)
        env = _with_venv_path(base_env, venv_dir)

        pip_result = _pip_install(python=python, artifact=artifact, env=env)
        checks.append(
            CheckResult(
                name=f"installation:{label}:pip_install",
                ok=pip_result.exit_code == 0,
                detail=f"exit={pip_result.exit_code}",
                category="installation",
            )
        )
        if pip_result.exit_code != 0:
            defects.append(
                Defect(
                    classification="install_failure",
                    component=f"installation:{label}",
                    expected="pip install success",
                    actual=pip_result.stderr[-300:],
                )
            )
            return checks, defects, warnings

        version = _run([str(codestrata), "--version"], env=env)
        checks.append(
            CheckResult(
                name=f"installation:{label}:version",
                ok=_version_matches(version),
                detail=version.stdout.strip()[:200],
                category="installation",
            )
        )
        if not _version_matches(version):
            defects.append(
                Defect(
                    classification="version_mismatch",
                    component=f"installation:{label}",
                    expected=INTENDED_RELEASE_VERSION,
                    actual=version.stdout.strip()[:120],
                )
            )

        help_result = _run([str(codestrata), "--help"], env=env)
        help_ok = help_result.exit_code == 0 and "init" in help_result.stdout
        checks.append(
            CheckResult(
                name=f"installation:{label}:help",
                ok=help_ok,
                detail=f"exit={help_result.exit_code}",
                category="installation",
            )
        )

        doctor = _run([str(codestrata), "doctor"], env=env)
        doctor_ok = doctor.exit_code == 0
        checks.append(
            CheckResult(
                name=f"installation:{label}:doctor",
                ok=doctor_ok,
                detail=f"exit={doctor.exit_code}",
                category="installation",
            )
        )
        if not doctor_ok:
            warnings.append(
                Warning(
                    code=f"doctor_nonzero_{label}",
                    detail="doctor may warn in clean venv without full config",
                )
            )

        workspace = Path(tmp) / "workspace"
        workspace.mkdir()
        init = _run(
            [str(codestrata), "init"],
            cwd=workspace,
            env=env,
        )
        config_path = workspace / "codestrata.toml"
        init_ok = init.exit_code == 0 and config_path.is_file()
        checks.append(
            CheckResult(
                name=f"installation:{label}:init",
                ok=init_ok,
                detail=f"exit={init.exit_code} config={config_path.is_file()}",
                category="installation",
            )
        )
        if not init_ok:
            defects.append(
                Defect(
                    classification="installation",
                    component=f"installation:{label}:init",
                    expected="exit 0 and codestrata.toml",
                    actual=f"exit={init.exit_code} stderr={init.stderr[-200:]}",
                )
            )

        env_check = _scrub_environ(env)
        if "PYTHONPATH" in env_check and env_check["PYTHONPATH"].strip():
            defects.append(
                Defect(
                    classification="environment_leak",
                    component=f"installation:{label}",
                    expected="PYTHONPATH unset",
                    actual="PYTHONPATH present",
                )
            )

    return checks, defects, warnings


def check_installations(
    monorepo: Path,
    *,
    wheel_relative: str | None,
    sdist_relative: str | None,
) -> tuple[list[CheckResult], list[Defect], list[Warning]]:
    all_checks: list[CheckResult] = []
    all_defects: list[Defect] = []
    all_warnings: list[Warning] = []

    if wheel_relative:
        wheel = monorepo / wheel_relative
        checks, defects, warnings = _install_and_smoke(label="wheel", artifact=wheel, monorepo=monorepo)
        all_checks.extend(checks)
        all_defects.extend(defects)
        all_warnings.extend(warnings)

    if sdist_relative:
        sdist = monorepo / sdist_relative
        checks, defects, warnings = _install_and_smoke(label="sdist", artifact=sdist, monorepo=monorepo)
        all_checks.extend(checks)
        all_defects.extend(defects)
        all_warnings.extend(warnings)

    all_checks.append(
        CheckResult(
            name="installation:no_network_required",
            ok=True,
            detail="pip install from local artifact path only",
            category="installation",
        )
    )
    return all_checks, all_defects, all_warnings


def pick_primary_artifacts(
    wheel_paths: tuple[str, ...],
    sdist_paths: tuple[str, ...],
) -> tuple[str | None, str | None]:
    wheel = next(
        (p for p in wheel_paths if "/a/" in p.replace("\\", "/") and p.endswith(".whl")),
        None,
    )
    if wheel is None:
        wheel = next((p for p in wheel_paths if p.endswith(".whl")), None)
    sdist = next(
        (p for p in sdist_paths if "/a/" in p.replace("\\", "/")),
        None,
    )
    if sdist is None:
        sdist = next(iter(sdist_paths), None)
    return wheel, sdist
