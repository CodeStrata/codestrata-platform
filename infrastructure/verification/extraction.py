"""Extraction-readiness and public/private boundary checks."""

from __future__ import annotations

from infrastructure.verification.contract import infra_root, repo_root
from infrastructure.verification.models import CheckResult


def check_extraction() -> list[CheckResult]:
    root = infra_root()
    readme = (root / "README.md").read_text(encoding="utf-8")
    security = (root / "docs" / "security-boundary.md").read_text(encoding="utf-8")
    future = (root / "docs" / "future-data-lake.md").read_text(encoding="utf-8")
    engine = repo_root() / "engine" / "src" / "codestrata"
    engine_hits = []
    for path in engine.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "infrastructure/" in text or "opentofu" in text.lower():
            engine_hits.append(path.name)
    # No Platform package imports from infrastructure verification at runtime.
    module_py = list((root / "modules").rglob("*.py"))
    return [
        CheckResult(
            name="extraction:codestrata_infrastructure_named",
            ok="codestrata-infrastructure" in readme
            or "codestrata-infrastructure" in security,
            detail="extraction target named",
            category="extraction",
        ),
        CheckResult(
            name="extraction:no_app_python_in_modules",
            ok=not module_py,
            detail="modules HCL only",
            category="extraction",
        ),
        CheckResult(
            name="extraction:scripts_resolve_paths",
            ok="REPO_ROOT" in (root / "scripts" / "validate.sh").read_text(encoding="utf-8")
            and "INFRA_ROOT" in (root / "scripts" / "validate.sh").read_text(encoding="utf-8"),
            detail="bounded path discovery",
            category="extraction",
        ),
        CheckResult(
            name="extraction:engine_unaware",
            ok=not engine_hits,
            detail="ok" if not engine_hits else ",".join(engine_hits[:5]),
            category="extraction",
        ),
        CheckResult(
            name="extraction:data_lake_documented_not_implemented",
            ok="modules/data-lake" in future
            and not (root / "modules" / "data-lake").exists(),
            detail="future only",
            category="extraction",
            scenario="D",
        ),
        CheckResult(
            name="extraction:state_separate_from_datalake",
            ok="data lake" in (root / "docs" / "state-management.md").read_text(
                encoding="utf-8"
            ).lower(),
            detail="state vs data lake",
            category="extraction",
        ),
    ]
