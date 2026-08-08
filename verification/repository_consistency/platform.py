"""Platform package classification consistency."""

from __future__ import annotations

from pathlib import Path

from verification.repository_consistency.inventory import add_check, load_json
from verification.repository_consistency.models import CheckResult, Defect

REGISTER = "platform/policies/platform_package_register.json"
EXPECTED_CLASSES = {
    "ACTIVE_COMMUNITY_BACKEND",
    "ACTIVE_INTERNAL_INSIGHTS_BACKEND",
    "COMMERCIAL_PROTOTYPE",
    "SHARED_INFRA_HELPER",
    "OWNER_REVIEW_REQUIRED",
    "MOVE_CANDIDATE",
    "REMOVE_CANDIDATE",
}


def check_platform(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, int], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / REGISTER
    add_check(checks, defects, "platform:register_exists", path.is_file(), REGISTER, "platform")
    if not path.is_file():
        return checks, defects, {}, []
    data = load_json(path)
    packages = data.get("packages", [])
    counts: dict[str, int] = {}
    owner: list[str] = []
    seen_names: set[str] = set()
    for pkg in packages:
        name = pkg.get("package", "")
        cls = pkg.get("classification", "")
        counts[cls] = counts.get(cls, 0) + 1
        add_check(
            checks,
            defects,
            f"platform:class:{name}",
            cls in EXPECTED_CLASSES and bool(cls),
            cls or "missing",
            "platform",
            classification="unclassified_platform_package",
        )
        add_check(
            checks,
            defects,
            f"platform:unique:{name}",
            name not in seen_names,
            name,
            "platform",
        )
        seen_names.add(name)
        if cls in {"COMMERCIAL_PROTOTYPE", "OWNER_REVIEW_REQUIRED"} or pkg.get("decision") == "OWNER_REVIEW_REQUIRED":
            owner.append(name)
        # path exists
        rel = pkg.get("path", "")
        if rel:
            add_check(
                checks,
                defects,
                f"platform:path:{name}",
                (monorepo / rel).exists(),
                rel,
                "platform",
            )

    # Discover major packages under codestrata_platform
    root = monorepo / "platform/src/codestrata_platform"
    if root.is_dir():
        discovered = sorted(
            p.name
            for p in root.iterdir()
            if p.is_dir() and not p.name.startswith("_") and p.name != "__pycache__"
        )
        registered = {p.get("package") for p in packages}
        missing = [n for n in discovered if n not in registered]
        # allow common non-package dirs
        allow = {"tests", "py.typed"}
        missing = [n for n in missing if n not in allow and (root / n / "__init__.py").exists()]
        add_check(
            checks,
            defects,
            "platform:no_unclassified_discovered",
            not missing,
            ",".join(missing) or "none",
            "platform",
            classification="unclassified_platform_package",
        )

    # Community backend not mixed as commercial
    for pkg in packages:
        if pkg.get("classification") == "ACTIVE_COMMUNITY_BACKEND":
            add_check(
                checks,
                defects,
                f"platform:community_not_commercial:{pkg.get('package')}",
                pkg.get("commercial_relevance") in {None, "none", ""},
                str(pkg.get("commercial_relevance")),
                "platform",
            )
    return checks, defects, counts, owner
