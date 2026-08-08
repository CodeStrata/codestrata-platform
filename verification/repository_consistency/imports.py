"""Runtime import boundary static scan."""

from __future__ import annotations

import re
from pathlib import Path

from verification.repository_consistency.inventory import add_check
from verification.repository_consistency.models import CheckResult, Defect

IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+(\S+)", re.M)
JS_IMPORT_RE = re.compile(
    r"""(?:from|import|require\()\s*['"]([^'"]+)['"]""",
)


def _py_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    out = []
    for p in root.rglob("*.py"):
        parts = set(p.parts)
        if "tests" in parts or "verification" in parts or "__pycache__" in parts:
            continue
        out.append(p)
    return out


def _scan_py(files: list[Path], needle: str) -> list[str]:
    hits = []
    for p in files:
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("#"):
                continue
            if '"""' in s or "'''" in s:
                # skip simple docstring lines
                continue
            m = IMPORT_RE.match(line)
            if m and needle in m.group(1):
                hits.append(p.as_posix())
                break
    return hits


def check_imports(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[dict[str, str]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    results: list[dict[str, str]] = []

    engine_hits = _scan_py(_py_files(monorepo / "engine/src"), "codestrata_platform")
    add_check(
        checks,
        defects,
        "imports:engine_no_platform",
        not engine_hits,
        ",".join(engine_hits[:5]) or "ok",
        "imports",
    )
    results.append({"rule": "engine->platform", "ok": str(not engine_hits)})

    # Insights should not import Platform Python
    insights_py = _py_files(monorepo / "insights")
    insights_hits = _scan_py(insights_py, "codestrata_platform")
    add_check(
        checks,
        defects,
        "imports:insights_no_platform_py",
        not insights_hits,
        ",".join(insights_hits[:5]) or "ok",
        "imports",
        classification="insights_requires_platform_source",
    )
    results.append({"rule": "insights->platform_py", "ok": str(not insights_hits)})

    infra_hits = _scan_py(_py_files(monorepo / "infrastructure"), "codestrata")
    # allow infrastructure.verification adapters; filter engine runtime
    engine_runtime = [h for h in infra_hits if "engine" in h or "codestrata." in Path(h).read_text(encoding="utf-8", errors="ignore")[:500]]
    # simpler: look for from codestrata or import codestrata (engine package)
    real = []
    for p in _py_files(monorepo / "infrastructure"):
        if "tests" in p.parts or "verification" in p.parts:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for line in text.splitlines():
            if line.strip().startswith("#"):
                continue
            if re.match(r"^\s*(from|import)\s+codestrata(\.|$|\s)", line):
                real.append(p.relative_to(monorepo).as_posix())
                break
    add_check(
        checks,
        defects,
        "imports:infra_no_engine_runtime",
        not real,
        ",".join(real[:5]) or "ok",
        "imports",
    )
    results.append({"rule": "infrastructure->engine", "ok": str(not real)})

    # Docs no platform runtime
    docs_hits = []
    docs_root = monorepo / "docs"
    if docs_root.is_dir():
        for p in list(docs_root.rglob("*.py")) + list(docs_root.rglob("*.{ts,js,mjs}")):
            pass
        for p in docs_root.rglob("*"):
            if p.suffix not in {".py", ".ts", ".js", ".mjs"}:
                continue
            if "node_modules" in p.parts:
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            if "codestrata_platform" in text and ("import" in text or "from " in text):
                # only real imports
                if re.search(r"(?m)^\s*(from|import)\s+codestrata_platform", text):
                    docs_hits.append(p.relative_to(monorepo).as_posix())
    add_check(
        checks,
        defects,
        "imports:docs_no_platform_runtime",
        not docs_hits,
        ",".join(docs_hits[:5]) or "ok",
        "imports",
    )

    # VS Code should not bundle engine source via relative monorepo import
    vs_hits = []
    vs = monorepo / "vscode-plugin/src"
    if vs.is_dir():
        for p in vs.rglob("*.{ts,js}"):
            pass
        for p in vs.rglob("*"):
            if p.suffix not in {".ts", ".js"}:
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            if re.search(r"""from\s+['\"]\.\./\.\./engine""", text) or "engine/src/codestrata" in text:
                vs_hits.append(p.relative_to(monorepo).as_posix())
    add_check(
        checks,
        defects,
        "imports:vscode_no_bundled_engine_src",
        not vs_hits,
        ",".join(vs_hits[:5]) or "ok",
        "imports",
    )

    # Platform should not import Insights frontend runtime
    plat_hits = []
    for p in _py_files(monorepo / "platform/src"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"(?m)^\s*(from|import)\s+insights\b", text):
            plat_hits.append(p.relative_to(monorepo).as_posix())
    add_check(
        checks,
        defects,
        "imports:platform_no_insights_frontend",
        not plat_hits,
        ",".join(plat_hits[:5]) or "ok",
        "imports",
    )
    _ = engine_runtime
    return checks, defects, results
