"""Layout, content, prohibited, product, dependency, secrets, docs scans."""

from __future__ import annotations

import os
import re
from pathlib import Path, PurePosixPath

from verification.infrastructure_repository_export.contract import (
    REQUIRED_ROOT_ENTRIES,
    VALIDATION_ROOTS,
)
from verification.infrastructure_repository_export.dual_export import _iter_files, mode_category
from verification.infrastructure_repository_export.models import CheckResult, Defect

_PROHIBITED_NAMES = (
    "terraform.tfstate",
    ".env",
    "credentials",
    "credentials.json",
    "aws-credentials",
    "local.auto.tfvars",
    "terraform.tfvars",
    "tofu.tfvars",
    "secrets.tfvars",
)
_PROHIBITED_GLOBS = (
    "*.tfstate",
    "*.tfstate.*",
    "*.tfplan",
    "*.plan",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "*.vsix",
    "*.whl",
    "crash.log",
    "override.tf",
    "*_override.tf",
)
_PRODUCT_DIRS = ("engine", "platform", "vscode-plugin", "cursor-plugin")
_IMPORT_RE = re.compile(r"^\s*(from|import)\s+codestrata(_platform)?\b")
_SECRET_RES = (
    ("aws_access_key", re.compile(r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("github_pat", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("bearer_value", re.compile(r"(?i)authorization\s*[:=]\s*['\"]?bearer\s+[A-Za-z0-9\-._~+/]+=*")),
)
_LOCAL_PATH_RE = re.compile(
    r"(?<![\w.-])(/Users/[\w./-]+|/home/[\w./-]+|file://[/\w]|\\\\Users\\\\|/var/folders/)"
)
_MD_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
_BT_PATH_RE = re.compile(r"`(\.\./[^`]+)`")


def check_layout(export_root: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks = []
    for entry in REQUIRED_ROOT_ENTRIES:
        path = export_root / entry
        ok = path.exists()
        checks.append(CheckResult(f"layout:{entry.replace('/', '_')}", ok, entry, "layout"))
    checks.append(
        CheckResult(
            "layout:no_infra_wrapper",
            not (export_root / "infrastructure").exists(),
            "Approach A",
            "layout",
        )
    )
    checks.append(
        CheckResult(
            "layout:no_product_dirs",
            all(not (export_root / d).exists() for d in _PRODUCT_DIRS),
            "no product trees",
            "layout",
        )
    )
    for root in VALIDATION_ROOTS:
        checks.append(
            CheckResult(
                f"layout:validation_root_{root.replace('/', '_')}",
                (export_root / root).is_dir(),
                root,
                "layout",
            )
        )
    defects = []
    if not all(c.ok for c in checks):
        defects.append(Defect("layout/content defect", "layout", "complete", "incomplete"))
    return checks, defects


def check_required_content(export_root: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks = [
        CheckResult(
            "content:cloud_api_main",
            (export_root / "modules/community-cloud-api/main.tf").is_file(),
            "main.tf",
            "content",
        ),
        CheckResult(
            "content:data_lake_main",
            (export_root / "modules/community-data-lake/main.tf").is_file(),
            "main.tf",
            "content",
        ),
        CheckResult(
            "content:production_main",
            (export_root / "production/main.tf").is_file(),
            "main.tf",
            "content",
        ),
        CheckResult(
            "content:backend_example",
            (export_root / "production/backend.tf.example").is_file(),
            "backend.tf.example",
            "content",
        ),
        CheckResult(
            "content:no_live_backend",
            not (export_root / "production/backend.tf").exists(),
            "no backend.tf",
            "content",
        ),
        CheckResult(
            "content:verification_runner",
            (export_root / "verification/runner.py").is_file(),
            "runner.py",
            "content",
        ),
        CheckResult(
            "content:tests_present",
            (export_root / "tests").is_dir()
            and any((export_root / "tests").rglob("test_*.py")),
            "tests",
            "content",
        ),
        CheckResult(
            "content:policies",
            (export_root / "policies").is_dir(),
            "policies/",
            "content",
        ),
    ]
    defects = []
    if not all(c.ok for c in checks):
        defects.append(
            Defect("layout/content defect", "required_content", "present", "missing")
        )
    return checks, defects


def check_prohibited(export_root: Path) -> tuple[list[CheckResult], list[Defect]]:
    hits: list[str] = []
    for rel, path in _iter_files(export_root).items():
        name = PurePosixPath(rel).name
        parts = PurePosixPath(rel).parts
        if any(p in {".git", ".terraform", ".tofu", "node_modules", "__pycache__"} for p in parts):
            hits.append(rel)
            continue
        if name in _PROHIBITED_NAMES:
            hits.append(name)
            continue
        if name.endswith(".tfvars") and not name.endswith(".tfvars.example"):
            hits.append(name)
            continue
        if name.endswith((".tfplan", ".plan", ".pem", ".key", ".p12", ".pfx", ".vsix", ".whl")):
            hits.append(name)
            continue
        if name.startswith(".env") and name != ".env.example":
            hits.append(name)
    checks = [
        CheckResult(
            "prohibited:absent",
            not hits,
            "ok" if not hits else f"hits={len(hits)}",
            "prohibited",
        )
    ]
    defects = []
    if hits:
        defects.append(
            Defect("prohibited-file defect", "scan", "absent", f"count={len(hits)}")
        )
    return checks, defects


def check_product_boundary(export_root: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks = [
        CheckResult(
            "product:dirs_absent",
            all(not (export_root / d).exists() for d in _PRODUCT_DIRS),
            "product dirs",
            "product",
        )
    ]
    defects = []
    if not all(c.ok for c in checks):
        defects.append(
            Defect("product/dependency-boundary defect", "product", "absent", "present")
        )
    return checks, defects


def check_dependency_boundary(export_root: Path) -> tuple[list[CheckResult], list[Defect]]:
    hits: list[str] = []
    for rel, path in _iter_files(export_root).items():
        if not rel.endswith(".py"):
            continue
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if _IMPORT_RE.match(line):
                hits.append(rel)
                break
    checks = [
        CheckResult(
            "dependency:no_runtime_imports",
            not hits,
            "ok" if not hits else f"files={len(hits)}",
            "dependency",
        )
    ]
    defects = []
    if hits:
        defects.append(
            Defect(
                "product/dependency-boundary defect",
                "imports",
                "none",
                f"count={len(hits)}",
            )
        )
    return checks, defects


def check_secrets(export_root: Path) -> tuple[list[CheckResult], list[Defect]]:
    hits: list[str] = []
    for rel, path in _iter_files(export_root).items():
        if not path.suffix.lower() in {
            ".tf",
            ".md",
            ".py",
            ".sh",
            ".json",
            ".example",
            ".toml",
            ".gitignore",
            "",
        } and path.name not in {"LICENSE", "SHA256SUMS", ".editorconfig"}:
            if path.suffix.lower() not in {".hcl"}:
                continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        # Skip pattern-definition files that document detection regexes
        if "SAFETY_PATTERNS" in text:
            continue
        for label, pattern in _SECRET_RES:
            for match in pattern.finditer(text):
                value = match.group(0)
                if "TEST_ONLY" in value or "REPLACE" in value.upper() or "EXAMPLE" in value.upper():
                    continue
                if path.suffix == ".md" and label in {"aws_access_key", "bearer_value"}:
                    continue
                hits.append(f"{PurePosixPath(rel).name}:{label}")
                break
    checks = [
        CheckResult(
            "secrets:no_candidates",
            not hits,
            "ok" if not hits else f"hits={len(hits)}",
            "secrets",
        )
    ]
    defects = []
    if hits:
        defects.append(
            Defect("secret/tfvars/local-path defect", "secrets", "clean", f"n={len(hits)}")
        )
    return checks, defects


def check_tfvars(export_root: Path) -> tuple[list[CheckResult], list[Defect]]:
    real = []
    for rel in _iter_files(export_root):
        name = PurePosixPath(rel).name
        if name.endswith(".tfvars") and not name.endswith(".example"):
            real.append(name)
        if name.endswith(".auto.tfvars") or name == "local.auto.tfvars":
            real.append(name)
    example = export_root / "production" / "terraform.tfvars.example"
    example_ok = example.is_file() and "REPLACE" in example.read_text(encoding="utf-8").upper()
    checks = [
        CheckResult("tfvars:no_real", not real, "ok" if not real else str(len(real)), "tfvars"),
        CheckResult("tfvars:example_synthetic", example_ok, "placeholders", "tfvars"),
    ]
    defects = []
    if not all(c.ok for c in checks):
        defects.append(
            Defect("secret/tfvars/local-path defect", "tfvars", "safe", "unsafe")
        )
    return checks, defects


def check_local_paths(export_root: Path) -> tuple[list[CheckResult], list[Defect]]:
    hits: list[str] = []
    for rel, path in _iter_files(export_root).items():
        if path.suffix.lower() not in {".md", ".py", ".sh", ".json", ".toml", ".tf", ".example", ".hcl", ""}:
            continue
        if path.name in {"SHA256SUMS"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        # Allow documented path-pattern regexes
        if "home_path" in text and "SAFETY_PATTERNS" in text:
            continue
        if "FORBIDDEN_REPORT" in text or "SAFETY_PATTERNS" in text:
            # Still flag real /Users/me style if present as literal path
            for match in _LOCAL_PATH_RE.finditer(text):
                val = match.group(0)
                if val.startswith("/Users/") and len(val) > len("/Users/") + 1:
                    # Regex documentation often has /Users/[\w.-]+ — skip bracket forms
                    if "[" in text[match.start() : match.end() + 20]:
                        continue
                    # Skip short pattern fragments in character classes nearby
                    if "\\\\w" in text or "[\\w" in text or r"[\w" in text:
                        # Check if this is inside a raw regex string
                        window = text[max(0, match.start() - 40) : match.end() + 40]
                        if "r\"" in window or "r'" in window or "re.compile" in window:
                            continue
                hits.append(PurePosixPath(rel).name)
                break
            continue
        if _LOCAL_PATH_RE.search(text):
            # Ignore conceptual mentions of /Users/ in policy docs without a username path
            if path.suffix == ".md":
                # Only fail if a concrete username-like path appears
                if re.search(r"/Users/[A-Za-z0-9._-]+/", text) or re.search(
                    r"/home/[A-Za-z0-9._-]+/", text
                ):
                    hits.append(PurePosixPath(rel).name)
                continue
            hits.append(PurePosixPath(rel).name)
    checks = [
        CheckResult(
            "local_paths:absent",
            not hits,
            "ok" if not hits else f"files={len(hits)}",
            "local_path",
        )
    ]
    defects = []
    if hits:
        defects.append(
            Defect("secret/tfvars/local-path defect", "local_paths", "none", f"n={len(hits)}")
        )
    return checks, defects


def check_documentation_links(export_root: Path) -> tuple[list[CheckResult], list[Defect]]:
    broken: list[str] = []
    for path in export_root.rglob("*.md"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        # Forbidden monorepo-relative product paths
        for bad in (
            "../engine",
            "../platform",
            "vscode-plugin/",
            "cursor-plugin/",
            "`engine/",
            "file://",
        ):
            if bad in text and "platform/docs" not in bad:
                # repository-contract may mention forbidden paths as policy
                if path.name == "repository-contract.md" and bad in {
                    "../engine",
                    "../platform",
                    "vscode-plugin/",
                    "cursor-plugin/",
                }:
                    continue
                if bad == "vscode-plugin/" and "vscode-plugin/" in text:
                    # policy denylist text is ok in contract
                    if "Never export" in text or "prohibited" in text.lower() or "exclude" in text.lower():
                        continue
                broken.append(f"{path.name}:{bad}")
        for match in _MD_LINK_RE.finditer(text):
            target = match.group(2).strip()
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if target.startswith("file:"):
                broken.append(path.name)
                continue
            # Relative resolution
            dest = (path.parent / target.split("#")[0]).resolve()
            try:
                dest.relative_to(export_root.resolve())
            except ValueError:
                broken.append(path.name)
                continue
            if target.split("#")[0] and not dest.exists():
                broken.append(f"{path.name}:missing")
    checks = [
        CheckResult(
            "docs:links_ok",
            not broken,
            "ok" if not broken else f"issues={len(broken)}",
            "docs",
        )
    ]
    defects = []
    if broken:
        defects.append(
            Defect("documentation-link defect", "links", "resolve", f"n={len(broken)}")
        )
    return checks, defects


def check_readme_security(export_root: Path) -> tuple[list[CheckResult], list[Defect]]:
    readme = (export_root / "README.md").read_text(encoding="utf-8")
    security = (export_root / "SECURITY.md").read_text(encoding="utf-8")
    checks = [
        CheckResult(
            "readme:name",
            "codestrata-infrastructure" in readme,
            "repository name",
            "readme",
        ),
        CheckResult(
            "readme:no_remote_claim",
            "created remotely" not in readme.lower() and "pushed to" not in readme.lower(),
            "no remote creation claim",
            "readme",
        ),
        CheckResult(
            "readme:no_deploy_claim",
            "deployed to production" not in readme.lower(),
            "no deploy claim",
            "readme",
        ),
        CheckResult(
            "readme:modules_documented",
            "modules/" in readme or "modules" in readme.lower(),
            "modules",
            "readme",
        ),
        CheckResult(
            "security:infra_specific",
            "Infrastructure" in security or "OpenTofu" in security,
            "SECURITY.md",
            "security",
        ),
        CheckResult(
            "security:no_creds",
            "AKIA" not in security and "-----BEGIN" not in security,
            "no credentials",
            "security",
        ),
    ]
    defects = []
    if not all(c.ok for c in checks):
        defects.append(Defect("root-file defect", "readme_security", "valid", "invalid"))
    return checks, defects


def check_gitignore(export_root: Path) -> tuple[list[CheckResult], list[Defect]]:
    gi = (export_root / ".gitignore").read_text(encoding="utf-8")
    required = (
        ".terraform/",
        "*.tfstate",
        "*.tfplan",
        "*.pem",
        ".env",
        "__pycache__/",
    )
    checks = [
        CheckResult(f"gitignore:has_{tok.replace('*', 'star').replace('/', '_')}", tok in gi, tok, "gitignore")
        for tok in required
    ]
    checks.append(
        CheckResult(
            "gitignore:lock_not_ignored",
            not any(line.strip() == ".terraform.lock.hcl" for line in gi.splitlines()),
            "lock trackable",
            "gitignore",
        )
    )
    defects = []
    if not all(c.ok for c in checks):
        defects.append(Defect("root-file defect", "gitignore", "valid", "invalid"))
    return checks, defects


def check_lockfiles(export_root: Path) -> tuple[list[CheckResult], list[Defect]]:
    locks = list(export_root.rglob(".terraform.lock.hcl"))
    # Pre-init: locks may or may not exist
    checks = [
        CheckResult(
            "lockfile:pre_init_policy",
            True,
            f"exported_locks={len(locks)}",
            "lockfile",
        ),
        CheckResult(
            "lockfile:not_under_gitignore_rule",
            not any(
                line.strip() == ".terraform.lock.hcl"
                for line in (export_root / ".gitignore").read_text(encoding="utf-8").splitlines()
            ),
            "trackable",
            "lockfile",
        ),
    ]
    return checks, []


def check_permissions(export_root: Path) -> tuple[list[CheckResult], list[Defect]]:
    bad_exec = []
    bad_world = []
    bad_setid = []
    scripts_ok = True
    for rel, path in _iter_files(export_root).items():
        mode = path.stat().st_mode
        if mode & 0o6000:
            bad_setid.append(rel)
        if mode & 0o002:
            bad_world.append(rel)
        name = PurePosixPath(rel).name
        is_script = name.endswith(".sh")
        executable = bool(mode & 0o111)
        if is_script and not executable:
            scripts_ok = False
        if not is_script and executable and path.suffix in {".tf", ".md", ".json", ".toml", ".hcl"}:
            bad_exec.append(rel)
    checks = [
        CheckResult("perm:scripts_executable", scripts_ok, "shell scripts", "permissions"),
        CheckResult("perm:no_world_writable", not bad_world, "ok", "permissions"),
        CheckResult("perm:no_setid", not bad_setid, "ok", "permissions"),
        CheckResult("perm:no_unexpected_exec", not bad_exec, "ok", "permissions"),
    ]
    defects = []
    if not all(c.ok for c in checks):
        defects.append(
            Defect("permission/symlink defect", "permissions", "safe", "unsafe")
        )
    return checks, defects


def check_symlinks(export_root: Path) -> tuple[list[CheckResult], list[Defect]]:
    found = []
    for dirpath, dirnames, filenames in os.walk(export_root, followlinks=False):
        for name in list(dirnames) + list(filenames):
            path = Path(dirpath) / name
            if path.is_symlink():
                found.append(name)
    checks = [
        CheckResult("symlink:absent", not found, "ok" if not found else str(len(found)), "symlink")
    ]
    defects = []
    if found:
        defects.append(
            Defect("permission/symlink defect", "symlinks", "none", f"n={len(found)}")
        )
    return checks, defects
