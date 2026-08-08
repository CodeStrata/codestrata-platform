"""Inventory loader for Slice 14.12 documentation deployment verification."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from verification.documentation_deployment.contract import (
    DOCS_ROOT,
    POLICY_RELATIVE,
    VITEPRESS_OUT,
    WRANGLER_CONFIG,
)


def _read_jsonc(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    stripped = re.sub(r"/\*[\s\S]*?\*/", "", raw)
    stripped = re.sub(r"^\s*//.*$", "", stripped, flags=re.MULTILINE)
    return json.loads(stripped)


@dataclass
class DeploymentInventory:
    monorepo: Path
    docs_root: Path
    policy: dict[str, Any] = field(default_factory=dict)
    package_json: dict[str, Any] = field(default_factory=dict)
    package_lock_text: str = ""
    wrangler_config: dict[str, Any] = field(default_factory=dict)
    wrangler_config_text: str = ""
    vitepress_config_text: str = ""
    deploy_check_text: str = ""
    gitignore_text: str = ""
    deployment_md_excerpt: str = ""
    readme_excerpt: str = ""
    dist_exists: bool = False
    dist_files: list[str] = field(default_factory=list)
    local_wrangler_version: str | None = None
    export_manifest: dict[str, Any] = field(default_factory=dict)

    @property
    def dist_dir(self) -> Path:
        return self.docs_root / VITEPRESS_OUT


def build_inventory(monorepo: Path) -> DeploymentInventory:
    docs = monorepo / DOCS_ROOT
    inv = DeploymentInventory(monorepo=monorepo, docs_root=docs)

    policy_path = monorepo / POLICY_RELATIVE
    if policy_path.is_file():
        inv.policy = json.loads(policy_path.read_text(encoding="utf-8"))

    pkg_path = docs / "package.json"
    if pkg_path.is_file():
        inv.package_json = json.loads(pkg_path.read_text(encoding="utf-8"))

    lock_path = docs / "package-lock.json"
    if lock_path.is_file():
        inv.package_lock_text = lock_path.read_text(encoding="utf-8")

    wrangler_path = docs / WRANGLER_CONFIG
    if wrangler_path.is_file():
        inv.wrangler_config_text = wrangler_path.read_text(encoding="utf-8")
        inv.wrangler_config = _read_jsonc(wrangler_path)

    vp_config = docs / ".vitepress" / "config.ts"
    if vp_config.is_file():
        inv.vitepress_config_text = vp_config.read_text(encoding="utf-8")

    deploy_check = docs / "scripts" / "deploy-check.mjs"
    if deploy_check.is_file():
        inv.deploy_check_text = deploy_check.read_text(encoding="utf-8")

    gitignore = docs / ".gitignore"
    if gitignore.is_file():
        inv.gitignore_text = gitignore.read_text(encoding="utf-8")

    deployment_md = docs / "DEPLOYMENT.md"
    if deployment_md.is_file():
        inv.deployment_md_excerpt = deployment_md.read_text(encoding="utf-8")[:4000]

    readme = docs / "README.md"
    if readme.is_file():
        inv.readme_excerpt = readme.read_text(encoding="utf-8")[:2000]

    dist = inv.dist_dir
    if dist.is_dir():
        inv.dist_exists = True
        inv.dist_files = sorted(
            str(p.relative_to(dist)).replace("\\", "/")
            for p in dist.rglob("*")
            if p.is_file()
        )[:500]

    wrangler_pkg = docs / "node_modules" / "wrangler" / "package.json"
    if wrangler_pkg.is_file():
        inv.local_wrangler_version = json.loads(
            wrangler_pkg.read_text(encoding="utf-8")
        ).get("version")

    manifest_path = monorepo / "public-export-manifest.yaml"
    if manifest_path.is_file():
        try:
            import yaml

            inv.export_manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            inv.export_manifest = {}

    return inv
