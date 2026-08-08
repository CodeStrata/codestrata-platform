"""Insights auth models — no passwords or AWS material in public payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

AuthRole = Literal["authenticated_internal"]


@dataclass(frozen=True, slots=True)
class SessionClaims:
    authenticated: bool
    iat: int
    exp: int
    sv: int

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "authenticated": self.authenticated,
            "exp": self.exp,
            "iat": self.iat,
            "sv": self.sv,
        }


@dataclass(frozen=True, slots=True)
class InsightsPrincipal:
    """Minimal principal for authenticated_internal — no user identity."""

    role: AuthRole = "authenticated_internal"

    def to_stable_dict(self) -> dict[str, Any]:
        return {"role": self.role}


@dataclass(frozen=True, slots=True)
class LoginRequest:
    password: str


@dataclass(frozen=True, slots=True)
class SessionStatusResponse:
    authenticated: bool

    def to_stable_dict(self) -> dict[str, Any]:
        return {"authenticated": self.authenticated}


@dataclass(frozen=True, slots=True)
class LoginSuccessResponse:
    ok: bool = True

    def to_stable_dict(self) -> dict[str, Any]:
        return {"ok": self.ok}


@dataclass(frozen=True, slots=True)
class LogoutResponse:
    ok: bool = True

    def to_stable_dict(self) -> dict[str, Any]:
        return {"ok": self.ok}
