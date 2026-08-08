"""Generated dist scope checks."""

from __future__ import annotations

from verification.documentation_deployment.inventory import DeploymentInventory
from verification.documentation_deployment.models import CheckResult

FORBIDDEN_FRAGMENTS = (
    "platform/",
    "data-lake/",
    "community-cloud/",
    "enterprise/",
    "commercial/",
    "internal/",
    "product-discovery/",
)


def check_generated_scope(inv: DeploymentInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    dist = inv.dist_dir

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, "generated_scope"))

    add(
        "generated_scope:dist_present",
        dist.is_dir(),
        "present" if dist.is_dir() else "missing",
    )

    leaked = [frag for frag in FORBIDDEN_FRAGMENTS if any(frag in f for f in inv.dist_files)]
    add(
        "generated_scope:no_forbidden_paths",
        not leaked,
        "clean" if not leaked else leaked[0],
    )

    sitemap_path = dist / "sitemap.xml"
    if sitemap_path.is_file():
        sitemap = sitemap_path.read_text(encoding="utf-8")
        sitemap_leaks = [frag for frag in FORBIDDEN_FRAGMENTS if frag in sitemap]
        add(
            "generated_scope:sitemap_clean",
            not sitemap_leaks,
            "clean" if not sitemap_leaks else sitemap_leaks[0],
        )
    else:
        add("generated_scope:sitemap_clean", False, "missing")

    return checks
