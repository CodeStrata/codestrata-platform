"""Register Platform CLI groups on the Community Engine typer app."""

from __future__ import annotations

import typer


def register_ai_cli(root: typer.Typer) -> None:
    """Attach Platform AI provider CLI (embeddings / grounded answers)."""

    from codestrata_platform.rag.cli.ai import ai_app

    root.add_typer(ai_app, name="ai", rich_help_panel="Platform")


def register_enterprise_cli(root: typer.Typer) -> None:
    """Attach Platform Engineering Knowledge Graph CLI."""

    from codestrata_platform.knowledge_graph.cli.enterprise import enterprise_app

    root.add_typer(enterprise_app, name="enterprise", rich_help_panel="Platform")


def register_repository_cli(root: typer.Typer) -> None:
    """Attach Platform Repository Retrieval / Answering CLI."""

    from codestrata_platform.rag.cli.repository import repository_app

    root.add_typer(repository_app, name="repository", rich_help_panel="Platform")
