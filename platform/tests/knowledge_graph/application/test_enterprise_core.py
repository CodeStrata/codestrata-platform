"""Phase 3 enterprise knowledge tests."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from codestrata_platform.knowledge_graph.application.errors import (
    EnterpriseManifestLoadError,
    EnterpriseManifestParseError,
)
from codestrata_platform.knowledge_graph.application.factory import (
    PassthroughRepositoryIdentityResolver,
    create_enterprise_knowledge_service,
    create_enterprise_query_service,
)
from codestrata_platform.knowledge_graph.application.graph_comparator import (
    EnterpriseGraphComparator,
)
from codestrata_platform.knowledge_graph.application.models import EnterprisePolicy
from codestrata_platform.knowledge_graph.domain.enums import (
    EnterpriseEntityKind,
    EnterpriseRelationshipKind,
)
from codestrata_platform.knowledge_graph.domain.identifiers import (
    build_entity_id,
    build_relationship_id,
)
from codestrata_platform.knowledge_graph.infrastructure.workspace import EnterpriseWorkspaceWriter
from codestrata_platform.knowledge_graph.infrastructure.yaml_loader import (
    YamlEnterpriseManifestSource,
)


def test_domain_avoids_yaml_and_transport_imports() -> None:
    root = Path("platform/src/codestrata_platform/knowledge_graph/domain")
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "import yaml" not in text
        assert "typer" not in text
        assert "fastmcp" not in text
        assert "sqlite3" not in text
        assert "subprocess" not in text


def test_application_avoids_typer_fastmcp_sqlite() -> None:
    root = Path("platform/src/codestrata_platform/knowledge_graph/application")
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "typer" not in text
        assert "fastmcp" not in text
        assert "sqlite3" not in text
        assert "import yaml" not in text


def test_identity_deterministic() -> None:
    assert build_entity_id(EnterpriseEntityKind.APPLICATION, "SIS") == (
        "application:sis"
    )
    rel = build_relationship_id(
        EnterpriseRelationshipKind.APPLICATION_USES_REPOSITORY,
        "application:sis",
        "repository:api",
    )
    assert rel.startswith("rel:APPLICATION_USES_REPOSITORY:")


def _write_minimal_linked_app(workspace: Path) -> None:
    """Write compact inline fixtures (no packaged university workspace)."""

    (workspace / "applications" / "demo-app.yaml").write_text(
        """apiVersion: codestrata.io/v1alpha1
kind: Application
metadata:
  id: demo-app
  name: Demo App
spec:
  applicationType: service
  lifecycle: active
""",
        encoding="utf-8",
    )
    (workspace / "repositories" / "demo-repo.yaml").write_text(
        """apiVersion: codestrata.io/v1alpha1
kind: RepositoryReference
metadata:
  id: demo-repo
  name: Demo Repo
spec:
  remoteUrl: https://github.com/example/demo-repo
""",
        encoding="utf-8",
    )
    (workspace / "relationships" / "app-uses-repo.yaml").write_text(
        """apiVersion: codestrata.io/v1alpha1
kind: Relationships
metadata:
  id: demo-relationships
spec:
  relationships:
    - kind: APPLICATION_USES_REPOSITORY
      source: application:demo-app
      target: repository:demo-repo
""",
        encoding="utf-8",
    )


def test_init_validate_build_query(tmp_path: Path) -> None:
    workspace = tmp_path / "enterprise"
    writer = EnterpriseWorkspaceWriter()
    created = writer.create_workspace(str(workspace), force=False)
    assert "enterprise.yaml" in created
    _write_minimal_linked_app(workspace)

    policy = EnterprisePolicy(
        require_registered_repositories=False,
        allow_unresolved_repositories=True,
    )
    service = create_enterprise_knowledge_service(
        policy=policy,
        resolver=PassthroughRepositoryIdentityResolver(),
        knowledge_directory=tmp_path / "knowledge",
    )
    validation = service.validate_workspace(str(workspace))
    assert validation.status == "passed", validation.errors

    built = service.build_graph(str(workspace))
    assert built.graph.enterprise_id == "enterprise:example"
    assert len(built.graph.entities) >= 2
    assert len(built.graph.relationships) >= 1

    queries = create_enterprise_query_service(
        policy=policy, knowledge_directory=tmp_path / "knowledge"
    )
    apps = queries.list_entities(
        kind=EnterpriseEntityKind.APPLICATION,
        enterprise_id="enterprise:example",
    )
    assert any(item.entity_id == "application:demo-app" for item in apps)

    repos = queries.list_by_relationship(
        source_id="application:demo-app",
        kind=EnterpriseRelationshipKind.APPLICATION_USES_REPOSITORY,
        enterprise_id="enterprise:example",
    )
    assert any(item.entity_id == "repository:demo-repo" for item in repos)

    impact = queries.repository_context(
        "repository:demo-repo", enterprise_id="enterprise:example"
    )
    assert impact.impacted_entities


def test_unsafe_yaml_constructor_blocked(tmp_path: Path) -> None:
    workspace = tmp_path / "enterprise"
    workspace.mkdir()
    (workspace / "enterprise.yaml").write_text(
        "!!python/object/apply:os.system ['echo pwned']\n",
        encoding="utf-8",
    )
    loader = YamlEnterpriseManifestSource(policy=EnterprisePolicy())
    with pytest.raises(
        (EnterpriseManifestParseError, EnterpriseManifestLoadError, yaml.YAMLError)
    ):
        loader.load(str(workspace))


def test_secret_field_rejected(tmp_path: Path) -> None:
    workspace = tmp_path / "enterprise"
    EnterpriseWorkspaceWriter().create_workspace(str(workspace))
    bad = workspace / "applications" / "bad.yaml"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text(
        """apiVersion: codestrata.io/v1alpha1
kind: Application
metadata:
  id: bad-app
  name: Bad App
spec:
  password: super-secret
""",
        encoding="utf-8",
    )
    service = create_enterprise_knowledge_service(
        policy=EnterprisePolicy(
            require_registered_repositories=False,
            allow_unresolved_repositories=True,
        ),
        knowledge_directory=tmp_path / "knowledge",
    )
    result = service.validate_workspace(str(workspace))
    assert result.status == "failed"
    assert any(issue.code == "suspicious_secret_field" for issue in result.errors)


def test_credential_url_rejected(tmp_path: Path) -> None:
    workspace = tmp_path / "enterprise"
    EnterpriseWorkspaceWriter().create_workspace(str(workspace))
    repo = workspace / "repositories" / "bad.yaml"
    repo.parent.mkdir(parents=True, exist_ok=True)
    repo.write_text(
        """apiVersion: codestrata.io/v1alpha1
kind: RepositoryReference
metadata:
  id: bad-repo
  name: Bad Repo
spec:
  remoteUrl: https://user:token@github.com/acme/bad
""",
        encoding="utf-8",
    )
    service = create_enterprise_knowledge_service(
        policy=EnterprisePolicy(
            require_registered_repositories=False,
            allow_unresolved_repositories=True,
        ),
        knowledge_directory=tmp_path / "knowledge",
    )
    result = service.validate_workspace(str(workspace))
    assert any(issue.code == "credential_bearing_url" for issue in result.errors)


def test_graph_compare_and_immutability(tmp_path: Path) -> None:
    workspace = tmp_path / "enterprise"
    EnterpriseWorkspaceWriter().create_workspace(str(workspace))
    _write_minimal_linked_app(workspace)
    policy = EnterprisePolicy(
        require_registered_repositories=False,
        allow_unresolved_repositories=True,
    )
    service = create_enterprise_knowledge_service(
        policy=policy,
        resolver=PassthroughRepositoryIdentityResolver(),
        knowledge_directory=tmp_path / "knowledge",
    )
    first = service.build_graph(str(workspace)).graph
    app = workspace / "applications" / "demo-app.yaml"
    payload = yaml.safe_load(app.read_text(encoding="utf-8"))
    payload["metadata"]["name"] = "Demo App Renamed"
    app.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    second = service.build_graph(str(workspace)).graph
    assert first.graph_id != second.graph_id
    loaded = service.get_graph(first.graph_id)
    assert loaded.graph_id == first.graph_id
    diff = EnterpriseGraphComparator().compare(first, second)
    assert "application:demo-app" in diff.entities_modified


def test_enterprise_settings_default(tmp_path: Path) -> None:
    from codestrata.config import load_settings

    config = tmp_path / "codestrata.toml"
    config.write_text(
        """
        [repository]
        path = "examples/sample-js-app"
        """,
        encoding="utf-8",
    )
    settings = load_settings(config)
    assert settings.enterprise.enabled is False
    assert settings.enterprise.workspace == "enterprise"
