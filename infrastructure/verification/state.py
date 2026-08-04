"""State management and gitignore verification."""

from __future__ import annotations

from infrastructure.verification.contract import infra_root, repo_root
from infrastructure.verification.models import CheckResult


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
            name="state:no_backend_tf_committed",
            ok=not (root / "production" / "backend.tf").exists(),
            detail="example only",
            category="state",
        ),
        CheckResult(
            name="state:repo_has_no_live_backend",
            ok=not any((repo_root() / "infrastructure").rglob("backend.tf")),
            detail="no live backend.tf",
            category="state",
        ),
    ]
