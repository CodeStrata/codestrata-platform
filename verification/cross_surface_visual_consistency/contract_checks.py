"""Contract checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add
from verification.cross_surface_visual_consistency.contract import CONSISTENCY_CONTRACT
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_contract(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    contract = inv.consistency_contract

    add(
        checks,
        "contract:id_version",
        contract.get("contract_id") == "codestrata-cross-surface-consistency-contract"
        and contract.get("contract_version") == "1.0",
        "contract_1_0",
        "contract",
    )
    add(
        checks,
        "contract:matrix_defined",
        bool(contract.get("matrix", {}).get("rows"))
        and bool(contract.get("matrix", {}).get("columns")),
        "matrix_present",
        "contract",
    )
    add(
        checks,
        "contract:adaptations",
        len(contract.get("adaptations") or []) >= 8,
        f"{len(contract.get('adaptations') or [])}_adaptations",
        "contract",
    )
    add(
        checks,
        "contract:public_token_mirrors",
        "docs/public/design-tokens/tokens.css"
        in (contract.get("public_token_mirrors") or []),
        "mirrors_defined",
        "contract",
    )
    add(
        checks,
        "contract:file_present",
        (inv.monorepo / CONSISTENCY_CONTRACT).is_file(),
        "on_disk",
        "contract",
    )
    add(
        checks,
        "contract:must_match_design_system",
        contract.get("must_match_design_system_tokens") is True,
        "token_match_required",
        "contract",
    )
    return checks
