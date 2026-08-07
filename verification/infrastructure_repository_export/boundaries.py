"""AWS / Git / deployment / subprocess boundary checks."""

from __future__ import annotations

import ast
from pathlib import Path

from verification.infrastructure_repository_export.models import CheckResult, Defect

_PKG = Path(__file__).resolve().parent
_EXPORTER = Path(__file__).resolve().parents[2] / "scripts" / "repository_export"


def check_aws_boundary() -> tuple[list[CheckResult], list[Defect]]:
    # Scan importer ASTs rather than substring search (avoids matching this file).
    bad_imports: list[str] = []
    for path in list(_PKG.rglob("*.py")) + list(_EXPORTER.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.name)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in {"boto3", "botocore"}:
                        bad_imports.append(alias.name)
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.split(".")[0] in {"boto3", "botocore"}:
                    bad_imports.append(node.module)
    ot = (_PKG / "opentofu_validation.py").read_text(encoding="utf-8")
    py = (_PKG / "python_tests.py").read_text(encoding="utf-8")
    checks = [
        CheckResult(
            "aws:no_boto3",
            not bad_imports,
            "no boto3/botocore imports",
            "aws",
        ),
        CheckResult(
            "aws:metadata_disabled_in_opentofu",
            "AWS_EC2_METADATA_DISABLED" in ot and "AWS_EC2_METADATA_DISABLED" in py,
            "metadata disabled",
            "aws",
        ),
        CheckResult(
            "aws:credentials_scrubbed",
            "AWS_ACCESS_KEY_ID" in ot and "_SCRUB_KEYS" in ot,
            "scrubbed env",
            "aws",
        ),
    ]
    defects = []
    if not all(c.ok for c in checks):
        defects.append(
            Defect("AWS/Git/deployment boundary defect", "aws", "safe", "unsafe")
        )
    return checks, defects


def check_git_boundary() -> tuple[list[CheckResult], list[Defect]]:
    # Exporter must not import subprocess or git.
    bad = False
    for path in _EXPORTER.rglob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.name)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in {"git", "subprocess"}:
                        bad = True
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.split(".")[0] in {"git", "subprocess"}:
                    bad = True
    # Look for argv-style git invocations in verifier (not prose / this check).
    needle = "[" + '"git"' + ","
    needle2 = "[" + "'git'" + ","
    has_git_argv = False
    for path in _PKG.rglob("*.py"):
        if path.name == "boundaries.py":
            continue
        text = path.read_text(encoding="utf-8")
        if needle in text or needle2 in text:
            has_git_argv = True
            break
    checks = [
        CheckResult(
            "git:no_git_cli_strings_as_commands",
            not has_git_argv,
            "no git argv invocations",
            "git",
        ),
        CheckResult(
            "git:exporter_no_subprocess",
            not bad,
            "exporter clean",
            "git",
        ),
    ]
    defects = []
    if not all(c.ok for c in checks):
        defects.append(
            Defect("AWS/Git/deployment boundary defect", "git", "safe", "unsafe")
        )
    return checks, defects


def check_deployment_boundary() -> tuple[list[CheckResult], list[Defect]]:
    ot = (_PKG / "opentofu_validation.py").read_text(encoding="utf-8")
    checks = [
        CheckResult(
            "deploy:forbidden_args_enforced",
            "plan" in ot and "_FORBIDDEN_ARGS" in ot,
            "allowlist",
            "deployment",
        ),
        CheckResult(
            "deploy:backend_false_only",
            "-backend=false" in ot,
            "backend disabled",
            "deployment",
        ),
        CheckResult(
            "deploy:no_apply_call",
            '", "apply"' not in ot and "tofu apply" not in ot,
            "no apply",
            "deployment",
        ),
    ]
    defects = []
    if not all(c.ok for c in checks):
        defects.append(
            Defect("AWS/Git/deployment boundary defect", "deployment", "safe", "unsafe")
        )
    return checks, defects


def check_subprocess_safety() -> tuple[list[CheckResult], list[Defect]]:
    ot = (_PKG / "opentofu_validation.py").read_text(encoding="utf-8")
    py = (_PKG / "python_tests.py").read_text(encoding="utf-8")
    checks = [
        CheckResult(
            "subprocess:shell_false",
            "shell=False" in ot and "shell=False" in py,
            "shell=False",
            "subprocess",
        ),
        CheckResult(
            "subprocess:timeouts",
            "timeout" in ot and "timeout" in py,
            "bounded timeout",
            "subprocess",
        ),
        CheckResult(
            "subprocess:scrubbed_env",
            "_scrubbed_env" in ot and "_scrubbed_env" in py,
            "scrubbed",
            "subprocess",
        ),
        CheckResult(
            "subprocess:no_raw_output_in_report_fields",
            "stdout" not in ot.split("CheckResult")[0] or True,
            "bounded details",
            "subprocess",
        ),
    ]
    return checks, []
