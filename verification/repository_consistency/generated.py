"""Generated vs source consistency."""

from __future__ import annotations

from pathlib import Path

from verification.repository_consistency.inventory import add_check, load_json
from verification.repository_consistency.models import CheckResult, Defect

GEN_REG = "platform/policies/repository_generated_artifact_register.json"


def _gitignore_texts(monorepo: Path) -> str:
    parts: list[str] = []
    for rel in (".gitignore", "infrastructure/.gitignore"):
        p = monorepo / rel
        if p.is_file():
            parts.append(p.read_text(encoding="utf-8"))
    return "\n".join(parts)


def check_generated(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / GEN_REG
    add_check(checks, defects, "generated:register_exists", path.is_file(), GEN_REG, "generated")
    gi = _gitignore_texts(monorepo)

    required_ignores = [
        (".codestrata/", "codestrata_state"),
        (".terraform/", "terraform_cache"),
        ("__pycache__", "pycache"),
        ("*.vsix", "vsix"),
    ]
    for pattern, label in required_ignores:
        add_check(
            checks,
            defects,
            f"generated:gitignore:{label}",
            pattern in gi,
            pattern,
            "generated",
        )

    # .terraform.lock.hcl NOT ignored (may be explicitly un-ignored via comment/policy)
    lock_ignored = False
    for line in gi.splitlines():
        s = line.strip()
        if s.startswith("#"):
            continue
        if s in {".terraform.lock.hcl", "**/.terraform.lock.hcl", "*.terraform.lock.hcl"}:
            lock_ignored = True
    infra_gi = monorepo / "infrastructure/.gitignore"
    if infra_gi.is_file() and "Do not ignore .terraform.lock.hcl" in infra_gi.read_text(encoding="utf-8"):
        lock_ignored = False
    add_check(
        checks,
        defects,
        "generated:terraform_lock_not_ignored",
        not lock_ignored,
        "lock_ignored" if lock_ignored else "ok",
        "generated",
        classification="generated_as_source",
    )

    # fixtures tracked
    fixtures = monorepo / "test-fixtures"
    add_check(
        checks,
        defects,
        "generated:fixtures_present",
        fixtures.is_dir(),
        "test-fixtures",
        "generated",
    )

    # no top-level dist as source authority
    add_check(
        checks,
        defects,
        "generated:no_top_level_dist",
        not (monorepo / "dist").exists(),
        "dist",
        "generated",
    )

    if path.is_file():
        data = load_json(path)
        add_check(
            checks,
            defects,
            "generated:register_schema",
            "generated" in str(data.get("schema", "")).lower(),
            str(data.get("schema")),
            "generated",
        )
    return checks, defects
