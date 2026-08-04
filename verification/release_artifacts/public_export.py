"""Public export boundary checks for SV.16."""

from __future__ import annotations

import subprocess
from pathlib import Path

from verification.release_artifacts.models import CheckResult, Defect, Warning

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


def _parse_manifest(manifest_path: Path) -> dict:
    if yaml is None:
        raise RuntimeError("PyYAML required for manifest parsing")
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("invalid manifest")
    return data


def _manifest_forbidden_roots(manifest: dict) -> list[str]:
    roots: list[str] = []
    for key in ("never_export_source_roots", "forbidden_paths", "forbidden_source_roots"):
        value = manifest.get(key)
        if isinstance(value, list):
            roots.extend(str(item) for item in value)
    return roots


def check_public_export(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[Warning]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    warnings: list[Warning] = []

    script = monorepo / "scripts" / "validate-public-exports.py"
    manifest = monorepo / "public-export-manifest.yaml"

    if script.is_file():
        completed = subprocess.run(
            [str(monorepo / ".venv" / "bin" / "python"), str(script), "--check-only"],
            cwd=str(monorepo),
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode == 2 and "unrecognized arguments" in (completed.stderr or ""):
            completed = subprocess.run(
                [str(monorepo / ".venv" / "bin" / "python"), str(script), "--dry-run"],
                cwd=str(monorepo),
                capture_output=True,
                text=True,
                check=False,
            )
        checks.append(
            CheckResult(
                name="public_export:validate_script",
                ok=completed.returncode == 0,
                detail=f"exit={completed.returncode}",
                category="public_export",
            )
        )
        if completed.returncode != 0:
            warnings.append(
                Warning(
                    code="validate_public_exports_nonzero",
                    detail=(completed.stderr or completed.stdout)[-400:],
                )
            )
    elif manifest.is_file():
        try:
            data = _parse_manifest(manifest)
            roots = _manifest_forbidden_roots(data)
            has_platform = any("platform" in root for root in roots)
            has_infra = any("infrastructure" in root for root in roots)
            checks.extend(
                [
                    CheckResult(
                        name="public_export:manifest_platform_forbidden",
                        ok=has_platform,
                        detail=f"roots={len(roots)}",
                        category="public_export",
                    ),
                    CheckResult(
                        name="public_export:manifest_infrastructure_forbidden",
                        ok=has_infra,
                        detail=f"roots={len(roots)}",
                        category="public_export",
                    ),
                ]
            )
        except Exception as exc:  # noqa: BLE001
            defects.append(
                Defect(
                    classification="manifest_parse",
                    component="public-export-manifest.yaml",
                    expected="parseable manifest",
                    actual=str(exc),
                )
            )
    else:
        defects.append(
            Defect(
                classification="missing_manifest",
                component="public_export",
                expected="validate-public-exports.py or manifest",
                actual="missing",
            )
        )

    return checks, defects, warnings
