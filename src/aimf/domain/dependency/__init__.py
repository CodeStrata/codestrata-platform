"""Dependency Intelligence domain (Phase 4.4.1).

Domain foundation only: taxonomy, pack identity, and assessment section
contracts. No production dependency rules, evidence collectors, or report
integration yet.
"""

from aimf.domain.dependency.ids import (
    PACK_DESCRIPTION,
    PACK_ID,
    PACK_TITLE,
    PACK_VERSION,
    RULE_ID_PREFIX,
    TAXONOMY_NAMESPACE,
)
from aimf.domain.dependency.taxonomy import (
    DEPENDENCY_ROLES,
    DependencyRole,
    coerce_dependency_role,
)

__all__ = [
    "DEPENDENCY_ROLES",
    "PACK_DESCRIPTION",
    "PACK_ID",
    "PACK_TITLE",
    "PACK_VERSION",
    "RULE_ID_PREFIX",
    "TAXONOMY_NAMESPACE",
    "DependencyRole",
    "coerce_dependency_role",
]
