"""Adversarial tenant-isolation and privacy hardening regressions."""

from __future__ import annotations

import pytest

from codestrata.security.database_url import sanitize_exception_message
from codestrata.security.redaction import REDACTED, redact_secrets
from codestrata_platform.api.app import create_app
from codestrata_platform.api.security import (
    PLATFORM_API_KEY_ENV,
    PLATFORM_ENV_VAR,
    assert_production_auth_configuration,
)
from codestrata_platform.application.common.errors import NotFoundError
from codestrata_platform.application.executive_intelligence.commands import (
    BuildExecutiveIntelligenceCommand,
)
from codestrata_platform.application.executive_intelligence.queries import (
    GetExecutiveIntelligenceQuery,
)
from codestrata_platform.application.strategic_roadmap.queries import (
    GetStrategicRoadmapQuery,
)
from codestrata_platform.application.strategic_roadmap.services import (
    StrategicRoadmapService,
)
from codestrata_platform.domain.executive_intelligence.identifiers import (
    ExecutiveIntelligenceId,
)
from codestrata_platform.domain.intelligence.ids import EvidenceReferenceId
from codestrata_platform.domain.intelligence.value_objects import EvidenceReference
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.workspace.ids import WorkspaceId

from .test_executive_intelligence_service import (
    _build_portfolio,
    _enable_executive_intelligence,
    _seed_repository,
    _stack,
)
from .test_strategic_roadmap import _enable_roadmap


def test_evidence_excerpt_redacts_secret_assignments() -> None:
    evidence = EvidenceReference(
        evidence_id=EvidenceReferenceId.generate(),
        path_reference="src/config.py",
        redacted_excerpt="password=hunter2 and api_key=sk-live-abcdef",
    )
    assert evidence.redacted_excerpt is not None
    assert "hunter2" not in evidence.redacted_excerpt
    assert "sk-live-abcdef" not in evidence.redacted_excerpt
    assert REDACTED in evidence.redacted_excerpt


def test_dialect_database_url_sanitized_in_exception_messages() -> None:
    message = (
        "OperationalError: connection failed "
        "postgresql+psycopg://codestrata:TopSecret123@127.0.0.1:5432/codestrata"
    )
    sanitized = sanitize_exception_message(message)
    assert "TopSecret123" not in sanitized
    assert "TopSecret123" not in redact_secrets(message)


def test_production_auth_fails_closed_without_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(PLATFORM_ENV_VAR, "production")
    monkeypatch.delenv(PLATFORM_API_KEY_ENV, raising=False)
    with pytest.raises(RuntimeError, match=PLATFORM_API_KEY_ENV):
        assert_production_auth_configuration()
    with pytest.raises(RuntimeError, match=PLATFORM_API_KEY_ENV):
        create_app(use_memory=True)


def test_cross_tenant_executive_intelligence_is_indistinguishable_404(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_executive_intelligence(monkeypatch)
    stack = _stack()
    repo_id = _seed_repository(stack, idx=1, tech_key="python")
    portfolio_id = _build_portfolio(stack, repo_ids=[repo_id])
    details = stack["exec_service"].build_intelligence(
        BuildExecutiveIntelligenceCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    exec_id = ExecutiveIntelligenceId(details.summary.executive_intelligence_id)

    with pytest.raises(NotFoundError) as missing:
        stack["exec_service"].get(
            GetExecutiveIntelligenceQuery(
                executive_intelligence_id=ExecutiveIntelligenceId("exec:missing"),
                organization_id=stack["org"].organization_id,
                workspace_id=stack["workspace"].workspace_id,
            )
        )
    with pytest.raises(NotFoundError) as foreign:
        stack["exec_service"].get(
            GetExecutiveIntelligenceQuery(
                executive_intelligence_id=exec_id,
                organization_id=OrganizationId("org:other"),
                workspace_id=stack["workspace"].workspace_id,
            )
        )
    assert (
        missing.value.reason_code
        == foreign.value.reason_code
        == "executive_intelligence_not_found"
    )


def test_cross_tenant_roadmap_is_indistinguishable_404(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_executive_intelligence(monkeypatch)
    _enable_roadmap(monkeypatch)
    stack = _stack()
    repo_id = _seed_repository(stack, idx=1, tech_key="fastapi")
    portfolio_id = _build_portfolio(stack, repo_ids=[repo_id])
    details = stack["exec_service"].build_intelligence(
        BuildExecutiveIntelligenceCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    service = StrategicRoadmapService(
        executive_intelligence=stack["exec_service"],
        executive_intelligence_repository=stack["executive_intelligence"],
    )
    with pytest.raises(NotFoundError):
        service.get(
            GetStrategicRoadmapQuery(
                executive_intelligence_id=ExecutiveIntelligenceId(
                    details.summary.executive_intelligence_id
                ),
                organization_id=OrganizationId("org:attacker"),
                workspace_id=WorkspaceId("workspace:attacker"),
            )
        )
