"""VS Code extension packaging checks for SV.16."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from verification.release_artifacts.contract import INTENDED_RELEASE_VERSION
from verification.release_artifacts.models import CheckResult, Defect, Warning


def check_vscode_extension(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[Warning]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    warnings: list[Warning] = []

    plugin_dir = monorepo / "vscode-plugin"
    package_json = plugin_dir / "package.json"
    if not package_json.is_file():
        defects.append(
            Defect(
                classification="missing_extension",
                component="vscode-plugin",
                expected="package.json",
                actual="missing",
            )
        )
        return checks, defects, warnings

    data = json.loads(package_json.read_text(encoding="utf-8"))
    version = str(data.get("version") or "")
    checks.append(
        CheckResult(
            name="vscode_extension:package_version",
            ok=version == INTENDED_RELEASE_VERSION,
            detail=f"version={version}",
            category="vscode_extension",
        )
    )
    if version != INTENDED_RELEASE_VERSION:
        defects.append(
            Defect(
                classification="version_mismatch",
                component="vscode-plugin/package.json",
                expected=INTENDED_RELEASE_VERSION,
                actual=version,
            )
        )

    skip_parts = {".vscode-test", "node_modules", ".git", "dist", "out", "coverage"}
    local_hits: list[str] = []
    for path in plugin_dir.rglob("*"):
        if not path.is_file():
            continue
        if any(part in skip_parts for part in path.parts):
            continue
        if path.suffix in {".png", ".jpg", ".gif", ".ico", ".woff", ".woff2", ".map"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "/Users/" in text:
            local_hits.append(str(path.relative_to(plugin_dir)))
        if "platform/src" in text:
            local_hits.append(f"platform/src:{path.name}")

    checks.append(
        CheckResult(
            name="vscode_extension:no_local_paths_or_platform_src",
            ok=not local_hits,
            detail=f"hits={local_hits[:5] or 'none'}",
            category="vscode_extension",
        )
    )

    npx = shutil.which("npx")
    if npx:
        completed = subprocess.run(
            [npx, "--yes", "@vscode/vsce", "package", "--out", "sv16-test.vsix"],
            cwd=str(plugin_dir),
            capture_output=True,
            text=True,
            check=False,
        )
        checks.append(
            CheckResult(
                name="vscode_extension:vsce_package",
                ok=completed.returncode == 0,
                detail=f"exit={completed.returncode}",
                category="vscode_extension",
            )
        )
        vsix = plugin_dir / "sv16-test.vsix"
        if vsix.is_file():
            vsix.unlink()
        if completed.returncode != 0:
            warnings.append(
                Warning(
                    code="vsce_package_failed",
                    detail=(completed.stderr or completed.stdout)[-300:],
                )
            )
    else:
        checks.append(
            CheckResult(
                name="vscode_extension:vsce_package",
                ok=True,
                detail="not_executed: npx unavailable",
                category="vscode_extension",
                status="not_executed",
            )
        )

    return checks, defects, warnings
