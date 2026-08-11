"""State management and gitignore verification."""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.verification.contract import infra_root, repo_root
from infrastructure.verification.models import CheckResult


def is_empty_s3_backend(path: Path) -> bool:
    """True when backend.tf is an empty S3 backend block with no identifiers."""

    if not path.is_file():
        return False
    stripped = re.sub(r"#.*", "", path.read_text(encoding="utf-8"))
    if not re.search(
        r'terraform\s*\{\s*backend\s+"s3"\s*\{\s*\}\s*\}',
        stripped,
        re.DOTALL,
    ):
        return False
    lowered = stripped.lower()
    return not any(
        token in lowered
        for token in ("bucket", "key", "access_key", "secret", "profile", "dynamodb")
    )


def check_state() -> list[CheckResult]:
    root = infra_root()
    gitignore = (root / ".gitignore").read_text(encoding="utf-8")
    backend = (root / "production" / "backend.tf.example").read_text(encoding="utf-8")
    state_docs = (root / "docs" / "state-management.md").read_text(encoding="utf-8")
    committed_state = list(root.rglob("*.tfstate")) + list(root.rglob("*.tfplan"))
    # Ignore anything under .terraform if present locally but untracked.
    committed_state = [
        p
        for p in committed_state
        if ".terraform" not in p.parts and "reports" not in p.parts
    ]
    return [
        CheckResult(
            name="state:gitignore_tfstate",
            ok="*.tfstate" in gitignore and "*.tfstate.*" in gitignore,
            detail="tfstate ignored",
            category="state",
            scenario="Q",
        ),
        CheckResult(
            name="state:gitignore_plans",
            ok="*.tfplan" in gitignore,
            detail="plans ignored",
            category="state",
            scenario="R",
        ),
        CheckResult(
            name="state:gitignore_terraform_dir",
            ok=".terraform/" in gitignore,
            detail=".terraform ignored",
            category="state",
        ),
        CheckResult(
            name="state:gitignore_tfvars",
            ok="terraform.tfvars" in gitignore and "secrets.tfvars" in gitignore,
            detail="tfvars ignored",
            category="state",
        ),
        CheckResult(
            name="state:no_committed_state_or_plans",
            ok=not committed_state,
            detail="ok" if not committed_state else str(len(committed_state)),
            category="state",
            scenario="Q",
        ),
        CheckResult(
            name="state:backend_example_encrypted",
            ok="encrypt" in backend.lower() and "REPLACE_WITH" in backend,
            detail="encrypted remote example",
            category="state",
        ),
        CheckResult(
            name="state:docs_cover_locking",
            ok=all(
                token in state_docs.lower()
                for token in ("locking", "encrypt", "data lake", "environment")
            ),
            detail="state-management.md",
            category="state",
        ),
        CheckResult(
            name="state:backend_tf_empty_s3",
            ok=is_empty_s3_backend(root / "production" / "backend.tf"),
            detail="empty s3 backend (no bucket/key/credentials)",
            category="state",
        ),
        CheckResult(
            name="state:no_populated_backend_tf",
            ok=all(
                is_empty_s3_backend(path)
                for path in (repo_root() / "infrastructure").rglob("backend.tf")
                if path.is_file()
            ),
            detail="no populated backend.tf",
            category="state",
        ),
    ]
