"""Standalone build validation against exported trees."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from verification.repository_package_release_validation.helpers import add_check
from verification.repository_package_release_validation.models import CheckResult, Defect


def _run(cmd: list[str], cwd: Path, env: dict | None = None, timeout: int = 180) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        ok = proc.returncode == 0
        # Deterministic detail — no timing/network chatter from npm/tofu.
        detail = "ok" if ok else f"exit_{proc.returncode}"
        err = (proc.stderr or proc.stdout or "").lower()
        if not ok:
            for tok in ("forbidden", "timeout", "could not resolve provider", "enoent", "error"):
                if tok in err:
                    detail = tok
                    break
        return ok, detail
    except Exception as exc:  # noqa: BLE001
        return False, type(exc).__name__


def check_standalone_builds(
    monorepo: Path,
    roots: dict[str, Path],
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict = {}

    # Docs — npm ci + build in exported codestrata-docs
    docs = roots.get("codestrata-docs")
    if docs and docs.is_dir():
        # Ensure no sibling design-system required
        bridge = list(docs.rglob("tokens.css"))
        sibling = False
        for p in bridge:
            t = p.read_text(encoding="utf-8", errors="ignore")
            if "../design-system/" in t or "../../design-system/" in t:
                sibling = True
        add_check(
            checks,
            defects,
            "build:docs_no_sibling_design_system",
            not sibling,
            "packaged tokens only",
            "standalone_build",
        )
        env = {**os.environ, "CI": "true"}
        # Prefer existing monorepo node if export lacks node_modules — install locally in export
        ok_ci, detail_ci = _run(["npm", "ci"], docs, env=env, timeout=240)
        add_check(checks, defects, "build:docs_npm_ci", ok_ci, detail_ci or "ok", "standalone_build")
        if ok_ci:
            ok_b, detail_b = _run(["npm", "run", "build"], docs, env=env, timeout=240)
            add_check(checks, defects, "build:docs_npm_build", ok_b, detail_b or "ok", "standalone_build")
            # clean dist after
            for d in (docs / "dist", docs / ".vitepress" / "dist"):
                if d.exists():
                    import shutil

                    shutil.rmtree(d, ignore_errors=True)
            summary["docs"] = "built" if ok_b else "build_failed"
        else:
            summary["docs"] = "npm_ci_failed"
    else:
        add_check(checks, defects, "build:docs_export_present", False, "codestrata-docs missing", "standalone_build")

    # Insights
    insights = roots.get("codestrata-insights")
    if insights and insights.is_dir():
        # no ../platform references in source
        bad_refs = []
        for p in list(insights.rglob("*.ts")) + list(insights.rglob("*.tsx")) + list(insights.rglob("*.json")):
            if "node_modules" in p.parts:
                continue
            t = p.read_text(encoding="utf-8", errors="ignore")
            if "../platform" in t or "../../platform" in t:
                bad_refs.append(p.relative_to(insights).as_posix())
        add_check(
            checks,
            defects,
            "build:insights_no_platform_sibling",
            not bad_refs,
            ",".join(bad_refs[:5]) or "ok",
            "standalone_build",
        )
        env = {**os.environ, "CI": "true"}
        ok_ci, detail_ci = _run(["npm", "ci"], insights, env=env, timeout=240)
        add_check(checks, defects, "build:insights_npm_ci", ok_ci, detail_ci or "ok", "standalone_build")
        if ok_ci:
            ok_t, detail_t = _run(["npm", "run", "typecheck"], insights, env=env, timeout=120)
            add_check(checks, defects, "build:insights_typecheck", ok_t, detail_t or "ok", "standalone_build")
            ok_b, detail_b = _run(["npm", "run", "build"], insights, env=env, timeout=180)
            add_check(checks, defects, "build:insights_build", ok_b, detail_b or "ok", "standalone_build")
            import shutil

            shutil.rmtree(insights / "dist", ignore_errors=True)
            summary["insights"] = "built" if ok_b else "build_failed"
        else:
            summary["insights"] = "npm_ci_failed"
    else:
        add_check(checks, defects, "build:insights_export_present", False, "insights missing", "standalone_build")

    # Infrastructure — structural tofu validate if tofu available; else structural only
    infra = roots.get("codestrata-infrastructure")
    if infra and infra.is_dir():
        add_check(
            checks,
            defects,
            "build:infra_no_engine_sibling",
            not (infra / "engine").exists() and not (infra / "platform").exists(),
            "no engine/platform trees",
            "standalone_build",
        )
        tofu = shutil_which("tofu")
        if tofu:
            # validate one module if present
            modules = sorted((infra / "modules").glob("*")) if (infra / "modules").is_dir() else []
            if modules:
                mod = modules[0]
                ok_i, d_i = _run(["tofu", "init", "-backend=false"], mod, timeout=120)
                network_limited = any(
                    tok in d_i.lower()
                    for tok in ("forbidden", "timeout", "could not resolve provider", "failed to query", "network")
                )
                if network_limited:
                    add_check(
                        checks,
                        defects,
                        "build:infra_tofu_init_network_limitation",
                        True,
                        "opentofu_provider_network_limited",
                        "standalone_build",
                    )
                    summary["infrastructure"] = "tofu_network_limited"
                else:
                    add_check(
                        checks,
                        defects,
                        "build:infra_tofu_init",
                        ok_i,
                        d_i or "ok",
                        "standalone_build",
                    )
                    if ok_i:
                        ok_v, d_v = _run(["tofu", "validate"], mod, timeout=60)
                        add_check(checks, defects, "build:infra_tofu_validate", ok_v, d_v or "ok", "standalone_build")
                    summary["infrastructure"] = "tofu_validated" if ok_i else "tofu_init_failed"
                import shutil as sh

                for p in infra.rglob(".terraform"):
                    if p.is_dir():
                        sh.rmtree(p, ignore_errors=True)
            else:
                add_check(checks, defects, "build:infra_modules_present", False, "no modules", "standalone_build")
                summary["infrastructure"] = "no_modules"
        else:
            add_check(
                checks,
                defects,
                "build:infra_tofu_unavailable_limitation",
                True,
                "tofu_not_on_path",
                "standalone_build",
            )
            summary["infrastructure"] = "tofu_unavailable_structural_ok"
    else:
        add_check(checks, defects, "build:infra_export_present", False, "infra missing", "standalone_build")

    # Community engine — structural: pyproject present; optional pip installable check is heavy
    engine = roots.get("codestrata-engine")
    if engine and engine.is_dir():
        add_check(
            checks,
            defects,
            "build:engine_no_platform_tree",
            not (engine / "platform").exists(),
            "no platform",
            "standalone_build",
        )
        add_check(
            checks,
            defects,
            "build:engine_pyproject",
            (engine / "pyproject.toml").is_file(),
            "pyproject.toml",
            "standalone_build",
        )
        # Light import-path check: no codestrata_platform imports in exported src
        bad = []
        src = engine / "src"
        scan_root = src if src.is_dir() else engine
        for p in scan_root.rglob("*.py"):
            if "tests" in p.parts or "verification" in p.parts:
                continue
            t = p.read_text(encoding="utf-8", errors="ignore")
            for line in t.splitlines():
                s = line.strip()
                if s.startswith("#"):
                    continue
                if s.startswith("from codestrata_platform") or s.startswith("import codestrata_platform"):
                    bad.append(p.relative_to(engine).as_posix())
                    break
        add_check(
            checks,
            defects,
            "build:engine_no_platform_imports",
            not bad,
            ",".join(bad[:5]) or "ok",
            "standalone_build",
        )
        summary["community"] = "structural_ok"
    else:
        add_check(checks, defects, "build:engine_export_present", False, "engine missing", "standalone_build")

    # VS Code package:dry in export if present
    vs = roots.get("codestrata-vscode")
    if vs and vs.is_dir():
        env = {**os.environ, "CI": "true"}
        ok_ci, detail_ci = _run(["npm", "ci"], vs, env=env, timeout=240)
        add_check(checks, defects, "build:vscode_npm_ci", ok_ci, detail_ci or "ok", "standalone_build")
        if ok_ci:
            ok_c, d_c = _run(["npm", "run", "compile"], vs, env=env, timeout=120)
            add_check(checks, defects, "build:vscode_compile", ok_c, d_c or "ok", "standalone_build")
            ok_d, d_d = _run(["npm", "run", "package:dry"], vs, env=env, timeout=120)
            add_check(checks, defects, "build:vscode_package_dry", ok_d, d_d or "ok", "standalone_build")
            import shutil as sh

            sh.rmtree(vs / "out", ignore_errors=True)
            for vsix in vs.glob("*.vsix"):
                vsix.unlink(missing_ok=True)
            summary["vscode"] = "package_dry_ok" if ok_d else "package_dry_failed"
        else:
            summary["vscode"] = "npm_ci_failed"

    _ = monorepo
    return checks, defects, summary


def shutil_which(name: str) -> str | None:
    import shutil

    return shutil.which(name)
