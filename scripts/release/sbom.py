"""Generate CycloneDX-compatible SBOM JSON without requiring cyclonedx-bom."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .dependencies import build_dependency_inventory

ROOT = Path(__file__).resolve().parents[2]


def _purl(ecosystem: str, name: str, version: str | None) -> str:
    eco = "pypi" if ecosystem == "python" else "npm"
    if version:
        return f"pkg:{eco}/{name}@{version}"
    return f"pkg:{eco}/{name}"


def _component_from_python(item: dict[str, Any]) -> dict[str, Any]:
    name = str(item.get("name") or item["component"])
    version = str(item.get("version") or "0.0.0")
    components = [
        {
            "type": "library",
            "name": name,
            "version": version,
            "purl": _purl("python", name, version),
            "scope": "required",
        }
    ]
    for dep in item.get("direct") or []:
        # Strip extras / markers for display name
        bare = str(dep).split(";", 1)[0].strip()
        pkg = bare
        for sep in ("==", ">=", "<=", "~=", "!=", ">", "<"):
            if sep in bare:
                pkg = bare.split(sep, 1)[0].strip()
                break
        components.append(
            {
                "type": "library",
                "name": pkg,
                "version": None,
                "purl": _purl("python", pkg, None),
                "scope": "required",
                "description": f"declared: {dep}",
            }
        )
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(UTC).replace(microsecond=0).isoformat().replace(
                "+00:00", "Z"
            ),
            "component": {
                "type": "application",
                "name": name,
                "version": version,
                "purl": _purl("python", name, version),
            },
            "tools": [{"name": "codestrata-release-sbom", "version": "1.0.0"}],
        },
        "components": components,
    }


def _component_from_node(item: dict[str, Any]) -> dict[str, Any]:
    name = str(item.get("name") or item["component"])
    version = str(item.get("version") or "0.0.0")
    components = [
        {
            "type": "library",
            "name": pkg,
            "version": ver,
            "purl": _purl("node", pkg, str(ver) if ver else None),
            "scope": scope,
        }
        for scope, mapping in (
            ("required", item.get("dependencies") or {}),
            ("optional", item.get("optionalDependencies") or {}),
            ("excluded", item.get("devDependencies") or {}),
        )
        for pkg, ver in mapping.items()
    ]
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(UTC).replace(microsecond=0).isoformat().replace(
                "+00:00", "Z"
            ),
            "component": {
                "type": "application",
                "name": name,
                "version": version,
                "purl": _purl("node", name, version),
            },
            "tools": [{"name": "codestrata-release-sbom", "version": "1.0.0"}],
        },
        "components": components,
    }


def generate_sboms(destination_dir: Path, root: Path = ROOT) -> dict[str, Path]:
    destination_dir.mkdir(parents=True, exist_ok=True)
    inventory = build_dependency_inventory(root)
    written: dict[str, Path] = {}
    combined_components: list[dict[str, Any]] = []
    for item in inventory["components"]:
        if item["ecosystem"] == "python":
            bom = _component_from_python(item)
        else:
            bom = _component_from_node(item)
        path = destination_dir / f"sbom-{item['component']}.cdx.json"
        path.write_text(json.dumps(bom, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written[item["component"]] = path
        combined_components.extend(bom.get("components") or [])

    combined = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(UTC).replace(microsecond=0).isoformat().replace(
                "+00:00", "Z"
            ),
            "component": {
                "type": "application",
                "name": "codestrata-community-release",
                "version": "aggregate",
            },
            "tools": [{"name": "codestrata-release-sbom", "version": "1.0.0"}],
        },
        "components": combined_components,
    }
    combined_path = destination_dir / "sbom-combined.cdx.json"
    combined_path.write_text(
        json.dumps(combined, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    written["combined"] = combined_path
    return written


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
