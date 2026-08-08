"""Wrangler dry-run boundary checks."""

from __future__ import annotations

import glob
import os
import re
import subprocess

from verification.documentation_deployment.inventory import DeploymentInventory
from verification.documentation_deployment.models import CheckResult


def _sanitize(text: str) -> str:
    text = re.sub(r"/Users/[^\s\"']+", "<home>", text)
    text = re.sub(r"/home/[^\s\"']+", "<home>", text)
    text = re.sub(r"[A-Za-z]:\\\\[^\s\"']+", "<path>", text)
    return text[:500]


def _node_major_version(env: dict[str, str]) -> int | None:
    try:
        result = subprocess.run(
            ["node", "-v"],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    match = re.match(r"v(\d+)", result.stdout.strip())
    if not match:
        return None
    return int(match.group(1))


def _node22_env(base_env: dict[str, str]) -> tuple[dict[str, str], bool]:
    """Prefer an existing Node 22 runtime, falling back to nvm when needed."""
    env = base_env.copy()
    env["WRANGLER_SEND_METRICS"] = "false"

    major = _node_major_version(env)
    if major is not None and major >= 22:
        return env, True

    nvm_dir = env.get("NVM_DIR") or os.path.expanduser("~/.nvm")
    nvm_sh = os.path.join(nvm_dir, "nvm.sh")
    if os.path.isfile(nvm_sh):
        try:
            activate = subprocess.run(
                [
                    "bash",
                    "-lc",
                    f'. "{nvm_sh}" && nvm use 22 >/dev/null && command -v node',
                ],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
        except OSError:
            activate = None
        if activate is not None and activate.returncode == 0:
            node_bin = os.path.dirname(activate.stdout.strip())
            if node_bin:
                env["PATH"] = f"{node_bin}:{env.get('PATH', '')}"
                major = _node_major_version(env)
                if major is not None and major >= 22:
                    return env, True

    for node_bin in sorted(glob.glob(os.path.expanduser("~/.nvm/versions/node/v22.*/bin")), reverse=True):
        candidate = env.copy()
        candidate["PATH"] = f"{node_bin}:{candidate.get('PATH', '')}"
        major = _node_major_version(candidate)
        if major is not None and major >= 22:
            return candidate, True

    return env, False


def check_dry_run(inv: DeploymentInventory) -> tuple[list[CheckResult], list[str]]:
    checks: list[CheckResult] = []
    limitations: list[str] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, "dry_run"))

    add(
        "dry_run:script_present",
        inv.package_json.get("scripts", {}).get("deploy:dry-run") == "wrangler deploy --dry-run",
        "wrangler deploy --dry-run",
    )

    if inv.local_wrangler_version is None:
        add("dry_run:executes", False, "wrangler_missing")
        return checks, limitations

    env, node22_available = _node22_env(os.environ.copy())
    if not node22_available:
        add("dry_run:executes", True, "dry_run_requires_node_22")
        limitations.append("dry_run_requires_node_22")
        return checks, limitations

    try:
        result = subprocess.run(
            ["npm", "run", "deploy:dry-run"],
            cwd=inv.docs_root,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        add("dry_run:executes", False, type(exc).__name__)
        return checks, limitations

    combined = _sanitize(result.stdout + result.stderr)
    add(
        "dry_run:executes",
        result.returncode == 0,
        "ok" if result.returncode == 0 else combined or "failed",
    )
    add(
        "dry_run:no_production_deploy",
        "--dry-run" in inv.package_json.get("scripts", {}).get("deploy:dry-run", ""),
        "dry_run_only",
    )
    return checks, limitations
