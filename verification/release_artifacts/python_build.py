"""Build Engine wheel and sdist twice for release artifact verification."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from verification.release_artifacts.contract import ARTIFACTS_SUBDIR, SV16_OUTPUT_RELATIVE
from verification.release_artifacts.models import CheckResult, Defect


@dataclass(frozen=True, slots=True)
class BuildArtifacts:
    wheel_paths: tuple[str, ...]
    sdist_paths: tuple[str, ...]
    output_relative: str


def _monorepo_python(monorepo: Path) -> Path:
    candidate = monorepo / ".venv" / "bin" / "python"
    if candidate.is_file():
        return candidate
    raise FileNotFoundError(f"missing monorepo venv python: {candidate}")


def _run_build(*, engine_dir: Path, python: Path, dist_dir: Path) -> None:
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [str(python), "-m", "build", "--outdir", str(dist_dir)],
        cwd=str(engine_dir),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"python -m build failed: exit={completed.returncode}\n"
            f"{completed.stderr[-2000:]}"
        )


def _copy_artifacts(
    *,
    dist_dir: Path,
    dest_dir: Path,
    monorepo: Path,
    label: str,
) -> tuple[list[str], list[str]]:
    """Copy build outputs into ``dest_dir/<label>/`` preserving valid filenames."""

    wheels: list[str] = []
    sdists: list[str] = []
    labeled = dest_dir / label
    labeled.mkdir(parents=True, exist_ok=True)
    for path in sorted(dist_dir.iterdir()):
        if not path.is_file():
            continue
        name = path.name
        if name.endswith(".whl"):
            target = labeled / name
            shutil.copy2(path, target)
            wheels.append(str(target.relative_to(monorepo)))
        elif name.endswith(".tar.gz") or name.endswith(".zip"):
            if "codestrata" not in name:
                continue
            target = labeled / name
            shutil.copy2(path, target)
            sdists.append(str(target.relative_to(monorepo)))
    return wheels, sdists


def build_engine_artifacts(monorepo: Path) -> tuple[BuildArtifacts, list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    engine_dir = monorepo / "engine"
    output_dir = monorepo / SV16_OUTPUT_RELATIVE / ARTIFACTS_SUBDIR
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        python = _monorepo_python(monorepo)
    except FileNotFoundError as exc:
        defects.append(
            Defect(
                classification="build_environment",
                component="python_build",
                expected=".venv/bin/python",
                actual=str(exc),
            )
        )
        checks.append(
            CheckResult(
                name="python_build:venv_python",
                ok=False,
                detail=str(exc),
                category="python_build",
            )
        )
        return (
            BuildArtifacts(wheel_paths=(), sdist_paths=(), output_relative=SV16_OUTPUT_RELATIVE),
            checks,
            defects,
        )

    checks.append(
        CheckResult(
            name="python_build:venv_python",
            ok=True,
            detail="using monorepo .venv/bin/python",
            category="python_build",
        )
    )

    dist_a = engine_dir / "dist" / "sv16_build_a"
    dist_b = engine_dir / "dist" / "sv16_build_b"
    try:
        _run_build(engine_dir=engine_dir, python=python, dist_dir=dist_a)
        _run_build(engine_dir=engine_dir, python=python, dist_dir=dist_b)
    except RuntimeError as exc:
        defects.append(
            Defect(
                classification="build_failure",
                component="python_build",
                expected="successful wheel+sdist build",
                actual=str(exc)[:500],
            )
        )
        checks.append(
            CheckResult(
                name="python_build:build_twice",
                ok=False,
                detail=str(exc)[:500],
                category="python_build",
            )
        )
        return (
            BuildArtifacts(wheel_paths=(), sdist_paths=(), output_relative=SV16_OUTPUT_RELATIVE),
            checks,
            defects,
        )

    wheels_a, sdists_a = _copy_artifacts(
        dist_dir=dist_a, dest_dir=output_dir, monorepo=monorepo, label="a"
    )
    wheels_b, sdists_b = _copy_artifacts(
        dist_dir=dist_b, dest_dir=output_dir, monorepo=monorepo, label="b"
    )
    wheel_paths = tuple(sorted(set(wheels_a + wheels_b)))
    sdist_paths = tuple(sorted(set(sdists_a + sdists_b)))

    checks.extend(
        [
            CheckResult(
                name="python_build:wheel_produced",
                ok=bool(wheel_paths),
                detail=f"wheels={len(wheel_paths)}",
                category="python_build",
            ),
            CheckResult(
                name="python_build:sdist_produced",
                ok=bool(sdist_paths),
                detail=f"sdists={len(sdist_paths)}",
                category="python_build",
            ),
            CheckResult(
                name="python_build:copied_to_sv16",
                ok=output_dir.is_dir(),
                detail=f"output={SV16_OUTPUT_RELATIVE}/{ARTIFACTS_SUBDIR}",
                category="python_build",
            ),
        ]
    )
    return (
        BuildArtifacts(
            wheel_paths=wheel_paths,
            sdist_paths=sdist_paths,
            output_relative=SV16_OUTPUT_RELATIVE,
        ),
        checks,
        defects,
    )
