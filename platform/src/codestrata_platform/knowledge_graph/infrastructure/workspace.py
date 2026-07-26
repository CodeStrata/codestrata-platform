"""Create starter enterprise YAML workspaces."""

from __future__ import annotations

from pathlib import Path

from codestrata_platform.knowledge_graph.application.errors import EnterpriseSecurityError

_ROOT = """apiVersion: codestrata.io/v1alpha1
kind: Enterprise
metadata:
  id: example
  name: Example Enterprise
  description: Starter enterprise architecture model
spec:
  schemaVersion: "1.0"
  defaultOrganization: example
  repositoryResolution:
    requireRegisteredRepository: true
  validation:
    unknownReferences: error
"""

_MINIMAL_ORG = """apiVersion: codestrata.io/v1alpha1
kind: Organization
metadata:
  id: example
  name: Example Organization
spec:
  organizationType: organization
  lifecycle: active
"""


class EnterpriseWorkspaceWriter:
    def create_workspace(
        self,
        workspace: str,
        *,
        force: bool = False,
    ) -> list[str]:
        root = Path(workspace)
        if root.exists() and any(root.iterdir()) and not force:
            raise EnterpriseSecurityError(
                "Workspace already exists; use --force only for empty/generated trees",
                reason_code="workspace_exists",
                manifest_path=root.name,
            )
        created: list[str] = []
        directories = [
            "organizations",
            "business-domains",
            "business-capabilities",
            "applications",
            "repositories",
            "services",
            "apis",
            "data-stores",
            "messaging",
            "teams",
            "people",
            "environments",
            "cloud-resources",
            "standards",
            "initiatives",
            "relationships",
        ]
        root.mkdir(parents=True, exist_ok=True)
        enterprise_file = root / "enterprise.yaml"
        if enterprise_file.exists() and not force:
            raise EnterpriseSecurityError(
                "enterprise.yaml already exists",
                reason_code="file_exists",
                manifest_path="enterprise.yaml",
            )
        enterprise_file.write_text(_ROOT, encoding="utf-8")
        created.append("enterprise.yaml")
        for name in directories:
            (root / name).mkdir(parents=True, exist_ok=True)
        org = root / "organizations" / "organization.yaml"
        org.write_text(_MINIMAL_ORG, encoding="utf-8")
        created.append("organizations/organization.yaml")
        return created
