"""Package and product boundary checks."""

from __future__ import annotations

from pathlib import Path

from verification.privacy_first_telemetry.models import CheckResult, Defect
from verification.privacy_first_telemetry.vscode_inputs import VsCodeTelemetryInventory


def _scan_imports(root: Path, patterns: tuple[str, ...]) -> list[str]:
    hits: list[str] = []
    if not root.is_dir():
        return hits
    for path in sorted(root.rglob("*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in patterns:
            if pattern in text:
                hits.append(f"{path.name}:{pattern}")
    return hits


def _scan_ts_imports(root: Path, patterns: tuple[str, ...]) -> list[str]:
    hits: list[str] = []
    if not root.is_dir():
        return hits
    for path in sorted(root.rglob("*.ts")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in patterns:
            if pattern in text:
                hits.append(f"{path.name}:{pattern}")
    return hits


def check_boundaries(
    monorepo: Path,
    vscode: VsCodeTelemetryInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    engine_tel = monorepo / "engine" / "src" / "codestrata" / "telemetry"
    engine_hits = _scan_imports(
        engine_tel,
        (
            "vscode-plugin",
            "codestrata_platform",
            "community_data_lake",
            "boto3",
            "botocore",
        ),
    )
    # Allow documenting deferred platform mapping in comments/docs strings carefully —
    # fail only on import statements.
    import_hits = []
    for path in sorted(engine_tel.rglob("*.py")):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if stripped.startswith("import ") or stripped.startswith("from "):
                if any(
                    token in stripped
                    for token in (
                        "codestrata_platform",
                        "vscode",
                        "boto3",
                        "botocore",
                        "community_data_lake",
                    )
                ):
                    import_hits.append(f"{path.name}:{stripped[:80]}")

    checks.append(
        CheckResult(
            name="engine_no_platform_vscode_aws_imports",
            ok=not import_hits,
            detail=f"hits={import_hits[:5]}" if import_hits else "clean",
            category="boundary",
            client="engine",
        )
    )

    vscode_hits = _scan_ts_imports(
        vscode.telemetry_dir,
        (
            "codestrata.telemetry",
            "codestrata_platform",
            "from 'aws",
            'from "aws',
            "community_data_lake",
            "@aws-sdk",
        ),
    )
    checks.append(
        CheckResult(
            name="vscode_no_engine_platform_aws_imports",
            ok=not vscode_hits,
            detail=f"hits={vscode_hits}" if vscode_hits else "clean",
            category="boundary",
            client="vscode",
        )
    )

    cursor_tel = monorepo / "cursor-plugin" / "src" / "telemetry"
    checks.append(
        CheckResult(
            name="cursor_no_telemetry_runtime",
            ok=not cursor_tel.exists(),
            detail="cursor-plugin/src/telemetry absent",
            category="boundary",
            client="cursor",
        )
    )

    # Verification package must not live inside product packages.
    checks.append(
        CheckResult(
            name="verification_outside_product_runtimes",
            ok=(monorepo / "verification" / "privacy_first_telemetry").is_dir()
            and not (monorepo / "engine" / "src" / "codestrata" / "verification" / "privacy_first_telemetry").exists(),
            detail="verification/privacy_first_telemetry is top-level",
            category="boundary",
            client="both",
        )
    )

    # No shared runtime schema package.
    shared_schema = monorepo / "shared" / "telemetry"
    checks.append(
        CheckResult(
            name="no_shared_runtime_schema_package",
            ok=not shared_schema.exists(),
            detail="no shared/telemetry runtime schema package",
            category="boundary",
            client="both",
        )
    )

    # VS Code package must not depend on Engine Python packages via npm.
    import json

    pkg = monorepo / "vscode-plugin" / "package.json"
    deps_ok = False
    if pkg.is_file():
        data = json.loads(pkg.read_text(encoding="utf-8"))
        all_deps = {}
        all_deps.update(data.get("dependencies") or {})
        all_deps.update(data.get("devDependencies") or {})
        deps_ok = not any("codestrata" in k for k in all_deps)
    checks.append(
        CheckResult(
            name="vscode_npm_deps_exclude_engine",
            ok=deps_ok,
            detail="npm dependencies exclude Engine packages",
            category="boundary",
            client="vscode",
        )
    )

    _ = engine_hits
    for check in checks:
        if not check.ok:
            defects.append(
                Defect(
                    classification="boundary",
                    component=check.client,
                    expected="pass",
                    actual=check.name,
                    detail=check.detail,
                )
            )
    return checks, defects
