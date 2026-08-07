"""Filesystem inventory helpers for Epic 13 completion."""

from __future__ import annotations

import json
from pathlib import Path


def read_text(monorepo: Path, relative: str) -> str:
    return (monorepo / relative).read_text(encoding="utf-8")


def exists(monorepo: Path, relative: str) -> bool:
    return (monorepo / relative).exists()


def package_json(monorepo: Path) -> dict:
    return json.loads(read_text(monorepo, "vscode-plugin/package.json"))


def list_dir_names(monorepo: Path, relative: str) -> list[str]:
    path = monorepo / relative
    if not path.is_dir():
        return []
    return sorted(p.name for p in path.iterdir())


def vscode_src_tree(monorepo: Path) -> str:
    """Concatenation of key VS Code extension TypeScript sources (bounded)."""
    roots = [
        "vscode-plugin/src/extension.ts",
        "vscode-plugin/src/communityWorkflow",
        "vscode-plugin/src/cliDiscovery",
        "vscode-plugin/src/cliInstallation",
        "vscode-plugin/src/repositoryInitialization",
        "vscode-plugin/src/assessmentExecution",
        "vscode-plugin/src/assessmentProgress",
        "vscode-plugin/src/reportOpening",
        "vscode-plugin/src/failureRecovery",
        "vscode-plugin/src/telemetryConsentIntegration",
        "vscode-plugin/src/sourceLocality",
        "vscode-plugin/src/cliCompatibility",
        "vscode-plugin/src/marketplaceBranding",
        "vscode-plugin/src/marketplaceDocs",
        "vscode-plugin/src/cleanInstall",
        "vscode-plugin/src/telemetry",
        "vscode-plugin/src/onboarding",
        "vscode-plugin/src/engine",
    ]
    parts: list[str] = []
    for rel in roots:
        path = monorepo / rel
        if path.is_file() and path.suffix == ".ts":
            parts.append(path.read_text(encoding="utf-8"))
        elif path.is_dir():
            for ts in sorted(path.rglob("*.ts")):
                if "test" in ts.parts:
                    continue
                parts.append(ts.read_text(encoding="utf-8"))
    return "\n".join(parts)


def policy_version_in_file(text: str, policy_id: str, expected: str) -> bool:
    if policy_id not in text:
        return False
    # Prefer explicit VERSION constants near the policy id.
    markers = (
        f'POLICY_VERSION = "{expected}"',
        f'policy_version: "{expected}"',
        f'POLICY_VERSION = "{expected}" as const',
        f'"{expected}" as const',
    )
    return any(m in text for m in markers) or (
        f'"{policy_id}"' in text and f'"{expected}"' in text
    )
