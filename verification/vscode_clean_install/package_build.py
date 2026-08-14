"""Build and inventory the actual VSIX package (path-normalized)."""

from __future__ import annotations

import json
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path

from verification.vscode_clean_install.contract import (
    FORBIDDEN_PACKAGE_SUBSTRINGS,
    PLUGIN_ROOT,
    REQUIRED_PACKAGE_ENTRIES,
    VSIX_NAME,
)


@dataclass(frozen=True, slots=True)
class PackageInventory:
    built: bool
    file_count: int
    size_bytes: int
    names: tuple[str, ...]
    package_json: dict
    forbidden_hits: tuple[str, ...]
    missing_required: tuple[str, ...]

    def to_stable_dict(self) -> dict:
        return {
            "built": self.built,
            "file_count": self.file_count,
            "forbidden_hit_count": len(self.forbidden_hits),
            "forbidden_hits": list(self.forbidden_hits),
            "missing_required": list(self.missing_required),
            "package_name": self.package_json.get("name"),
            "package_version": self.package_json.get("version"),
            "publisher": self.package_json.get("publisher"),
            "size_bytes": self.size_bytes,
        }


def ensure_vsix_built(monorepo: Path, *, rebuild: bool = False) -> Path:
    """Build codestrata-assessment-0.2.2.vsix via npm run package when needed."""
    plugin = monorepo / PLUGIN_ROOT
    vsix = plugin / VSIX_NAME
    if vsix.is_file() and not rebuild:
        return vsix
    # Prefer package script (compile + pinned vsce package)
    result = subprocess.run(
        ["npm", "run", "package"],
        cwd=str(plugin),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not vsix.is_file():
        # Fallback: known-good vsce 2.32.0 (avoids secretlint concurrency=0 bug)
        subprocess.run(
            [
                "npx",
                "--yes",
                "@vscode/vsce@2.32.0",
                "package",
                "--no-dependencies",
            ],
            cwd=str(plugin),
            check=True,
            capture_output=True,
            text=True,
        )
    if not vsix.is_file():
        raise FileNotFoundError(VSIX_NAME)
    return vsix


def inventory_vsix(vsix_path: Path) -> PackageInventory:
    names: list[str] = []
    package_json: dict = {}
    with zipfile.ZipFile(vsix_path, "r") as zf:
        names = sorted(zf.namelist())
        with zf.open("extension/package.json") as fh:
            package_json = json.loads(fh.read().decode("utf-8"))

    forbidden: list[str] = []
    for name in names:
        lower = name.lower()
        for frag in FORBIDDEN_PACKAGE_SUBSTRINGS:
            # Allow extension/media paths; reject top-level or nested forbidden trees.
            if frag == "src/" and (
                lower.startswith("extension/src/") or "/src/" in lower
            ):
                # packaged should exclude TypeScript sources under extension/src
                if lower.startswith("extension/src/"):
                    forbidden.append(name)
                    break
            elif frag == "src/":
                continue
            elif frag.strip("/") in lower.replace("\\", "/"):
                # Avoid matching "reports" inside unrelated words via path segments
                parts = lower.replace("\\", "/").split("/")
                needle = frag.strip("/").lower()
                if needle in parts or any(p.startswith(needle) for p in parts):
                    # sample-reports is forbidden; "reports" as package outputDirectory string is only in package.json content not path
                    if needle == "reports" and "sample-reports" not in lower and lower != "extension/reports":
                        # only flag actual reports directories
                        if "/reports/" in f"/{lower}/" or lower.endswith("/reports"):
                            forbidden.append(name)
                            break
                        continue
                    forbidden.append(name)
                    break

    missing = []
    lower_names = {n.lower(): n for n in names}
    for req in REQUIRED_PACKAGE_ENTRIES:
        if req not in names and req.lower() not in lower_names:
            missing.append(req)
    return PackageInventory(
        built=True,
        file_count=len(names),
        size_bytes=vsix_path.stat().st_size,
        names=tuple(names),
        package_json=package_json,
        forbidden_hits=tuple(sorted(set(forbidden))),
        missing_required=tuple(missing),
    )


def category_counts(names: tuple[str, ...]) -> dict[str, int]:
    counts = {
        "runtime_js": 0,
        "docs_md": 0,
        "media": 0,
        "metadata": 0,
        "other": 0,
    }
    for name in names:
        lower = name.lower()
        if lower.endswith(".js"):
            counts["runtime_js"] += 1
        elif lower.endswith(".md"):
            counts["docs_md"] += 1
        elif "/media/" in lower or lower.startswith("extension/media/"):
            counts["media"] += 1
        elif lower.endswith("package.json") or lower.endswith("license"):
            counts["metadata"] += 1
        else:
            counts["other"] += 1
    return counts
