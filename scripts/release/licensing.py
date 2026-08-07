"""Licensing / required legal-file checks for staged Community exports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parents[2]

# Approved public license identifier — do not invent terms.
APPROVED_LICENSE = "MIT"

REQUIRED_PER_EXPORT_DEFAULTS = ("LICENSE", "SECURITY.md", "README.md")


def _read_engine_license(root: Path) -> str | None:
    try:
        import tomllib
    except ImportError:  # pragma: no cover
        import tomli as tomllib  # type: ignore

    data = tomllib.loads((root / "engine" / "pyproject.toml").read_text(encoding="utf-8"))
    license_field = (data.get("project") or {}).get("license")
    if isinstance(license_field, dict):
        if license_field.get("text"):
            return str(license_field["text"])
        if license_field.get("file"):
            # SPDX inferred from LICENSE file presence + approved project license.
            return APPROVED_LICENSE
    if isinstance(license_field, str):
        return license_field
    return None


def check_licensing(
    staging: Path,
    *,
    root: Path = ROOT,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if manifest is None:
        if yaml is None:
            raise RuntimeError("PyYAML is required")
        manifest = yaml.safe_load(
            (root / "public-export-manifest.yaml").read_text(encoding="utf-8")
        )
    release = (manifest or {}).get("release") or {}
    required = list(release.get("required_legal_files") or REQUIRED_PER_EXPORT_DEFAULTS)

    issues: list[str] = []
    per_export: list[dict[str, Any]] = []
    for export in (manifest or {}).get("exports") or []:
        name = str(export["name"])
        dest = staging / name
        missing = [item for item in required if not (dest / item).is_file()]
        # NOTICE is required for engine when listed in require_files
        validation = export.get("validation") or {}
        for req in validation.get("require_files") or []:
            if req in {"LICENSE", "NOTICE", "SECURITY.md", "CODE_OF_CONDUCT.md"}:
                if not (dest / req).is_file() and req not in missing:
                    missing.append(req)
        entry = {"export": name, "missing": missing, "ok": not missing}
        per_export.append(entry)
        if missing:
            issues.append(f"{name}: missing {missing}")

    license_meta = _read_engine_license(root)
    if license_meta and APPROVED_LICENSE not in str(license_meta):
        issues.append(
            f"Engine package license {license_meta!r} does not match approved {APPROVED_LICENSE}"
        )

    # Extension package.json license fields (VS Code only after Slice 12.2)
    for rel in ("vscode-plugin/package.json",):
        path = root / rel
        if not path.is_file():
            continue
        import json

        data = json.loads(path.read_text(encoding="utf-8"))
        lic = data.get("license")
        if lic and lic != APPROVED_LICENSE:
            issues.append(f"{rel}: license {lic!r} != {APPROVED_LICENSE}")
        if not lic:
            issues.append(f"{rel}: missing license field")

    return {
        "approved_license": APPROVED_LICENSE,
        "engine_license": license_meta,
        "exports": per_export,
        "issues": issues,
        "passed": len(issues) == 0,
        "notes": [
            "Do not invent license terms; use the approved project license.",
            "Flag missing legal decisions rather than fabricating NOTICE content.",
        ],
    }
