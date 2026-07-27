"""Shared SQLAlchemy Declarative base for Platform persistence records."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for Commercial Platform ORM records."""
