"""Generated Infrastructure-specific root files."""

from __future__ import annotations

from pathlib import Path

from repository_export.models import PlannedFile
from repository_export.permissions import approved_mode_for
from repository_export.policy import MODE_FILE, REPOSITORY_NAME


def generated_gitignore() -> str:
    return """# Local OpenTofu / Terraform artifacts — never commit
.terraform/
*.tfstate
*.tfstate.*
*.tfplan
*.plan
crash.log
crash.*.log
override.tf
override.tf.json
*_override.tf
*_override.tf.json

# Variable files with real values
*.auto.tfvars
*.auto.tfvars.json
terraform.tfvars
tofu.tfvars
secrets.tfvars
*.secrets.tfvars

# Credentials and keys
*.pem
*.key
*.p12
*.pfx
.env
.env.*
!.env.example
credentials
credentials.json
aws-credentials

# Build / packaging outputs
build/
dist/
*.zip
*.tar
*.tar.gz
image-id.txt
image-digest.txt

# Verification / local reports (generated)
reports/

# OS / editor / caches
.DS_Store
.idea/
.vscode/
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
.venv/
venv/

# NOTE: .terraform.lock.hcl is intentionally tracked for reproducible providers.
"""


def generated_security_md() -> str:
    return f"""# Security Policy — {REPOSITORY_NAME}

This private repository contains OpenTofu modules, production compositions,
infrastructure validation, and deployment documentation for CodeStrata-hosted
services.

## Reporting

Report security issues through the CodeStrata private security channel used for
Infrastructure and Community Cloud hosting controls. Do not file public issues
that include credentials, state, or account identifiers.

## Boundaries

- No Terraform / OpenTofu state is stored in this repository
- No deployment credentials are stored in this repository
- Backend configuration examples are secret-free templates only
- Provider lock files may be tracked; plugin caches (`.terraform/`) are not
- Application runtime code (Engine, Platform, editor extensions) is out of scope

## Validation posture

Local validation uses `tofu init -backend=false` and `tofu validate` without
plan/apply/destroy and without production credentials.
"""


def generated_editorconfig() -> str:
    return """root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
indent_style = space
indent_size = 2
trim_trailing_whitespace = true

[*.py]
indent_size = 4

[*.md]
trim_trailing_whitespace = false
"""


def generated_pyproject() -> str:
    return """[project]
name = "codestrata-infrastructure"
version = "0.0.0"
description = "Private CodeStrata Infrastructure (OpenTofu modules and validation)"
requires-python = ">=3.12"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
cache_dir = ".pytest_cache"
"""


def load_license(source_root: Path) -> bytes:
    for candidate in (
        source_root / "docs" / "LICENSE",
        source_root / "engine" / "LICENSE",
    ):
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8").encode("utf-8")
    raise FileNotFoundError("approved LICENSE not found")


def adapt_readme(source_text: str) -> str:
    from repository_export.transform import rewrite_documentation_links

    text = rewrite_documentation_links(source_text)
    header = (
        f"# {REPOSITORY_NAME}\n\n"
        "Private Infrastructure repository for CodeStrata-hosted services.\n"
        "This tree is produced by a deterministic one-way export from the main\n"
        "monorepo while the main repository remains authoritative pre-cutover.\n"
        "This export does not create a remote, commit, push, tag, or deploy.\n\n"
        "---\n\n"
    )
    # Drop leading H1 from source to avoid double title if present
    lines = text.splitlines()
    if lines and lines[0].startswith("# "):
        text = "\n".join(lines[1:]).lstrip("\n")
    return header + text + ("\n" if not text.endswith("\n") else "")


def build_generated_root_files(
    *,
    source_root: Path,
    readme_source: bytes | None,
) -> list[PlannedFile]:
    files: list[PlannedFile] = []

    def add(path: str, content: str | bytes, classification: str = "generated_root_file") -> None:
        data = content.encode("utf-8") if isinstance(content, str) else content
        if not data.endswith(b"\n"):
            data += b"\n"
        files.append(
            PlannedFile(
                destination_path=path,
                content=data,
                mode=approved_mode_for(path),
                classification=classification,  # type: ignore[arg-type]
            )
        )

    if readme_source is not None:
        add("README.md", adapt_readme(readme_source.decode("utf-8")), "transformed_export")
    add("SECURITY.md", generated_security_md())
    add("LICENSE", load_license(source_root))
    add(".gitignore", generated_gitignore())
    add(".editorconfig", generated_editorconfig())
    add("pyproject.toml", generated_pyproject())
    return files
