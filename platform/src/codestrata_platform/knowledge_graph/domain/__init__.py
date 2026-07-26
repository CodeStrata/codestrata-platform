"""Enterprise Knowledge Graph domain package.

This is distinct from ``codestrata.domain.engineering_knowledge`` (technology concepts).
Enterprise models describe organizations, applications, ownership, and
cross-repository architecture context declared in YAML manifests.
"""

from __future__ import annotations

from codestrata_platform.knowledge_graph.domain.entities import (
    EnterpriseEntity,
    EnterpriseKnowledgeGraph,
    EnterpriseProvenance,
    EnterpriseRelationship,
)
from codestrata_platform.knowledge_graph.domain.enums import (
    ApplicationKind,
    EnterpriseCriticality,
    EnterpriseEntityKind,
    EnterpriseLifecycle,
    EnterpriseProvenanceCategory,
    EnterpriseRelationshipKind,
    EnvironmentKind,
    InitiativeStatus,
    ServiceKind,
    StandardStatus,
    UnknownFieldPolicy,
)
from codestrata_platform.knowledge_graph.domain.errors import (
    EnterpriseDomainError,
    EnterpriseHierarchyCycleError,
    EnterpriseIdentityError,
    EnterpriseRelationshipConstraintError,
)
from codestrata_platform.knowledge_graph.domain.identifiers import (
    EnterpriseEntityId,
    EnterpriseRelationshipId,
    build_entity_id,
    build_relationship_id,
    normalize_local_id,
)
from codestrata_platform.knowledge_graph.domain.manifests import (
    SUPPORTED_API_VERSION,
    EnterpriseManifestCollection,
    EnterpriseManifestDocument,
    ManifestMetadata,
)
from codestrata_platform.knowledge_graph.domain.relationships import (
    HIERARCHY_RELATIONSHIPS,
    validate_relationship_kinds,
)

__all__ = [
    "SUPPORTED_API_VERSION",
    "ApplicationKind",
    "EnterpriseCriticality",
    "EnterpriseDomainError",
    "EnterpriseEntity",
    "EnterpriseEntityId",
    "EnterpriseEntityKind",
    "EnterpriseHierarchyCycleError",
    "EnterpriseIdentityError",
    "EnterpriseKnowledgeGraph",
    "EnterpriseLifecycle",
    "EnterpriseManifestCollection",
    "EnterpriseManifestDocument",
    "EnterpriseProvenance",
    "EnterpriseProvenanceCategory",
    "EnterpriseRelationship",
    "EnterpriseRelationshipConstraintError",
    "EnterpriseRelationshipId",
    "EnterpriseRelationshipKind",
    "EnvironmentKind",
    "HIERARCHY_RELATIONSHIPS",
    "InitiativeStatus",
    "ManifestMetadata",
    "ServiceKind",
    "StandardStatus",
    "UnknownFieldPolicy",
    "build_entity_id",
    "build_relationship_id",
    "normalize_local_id",
    "validate_relationship_kinds",
]
