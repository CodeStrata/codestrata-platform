"""Bounded router error taxonomy."""

from __future__ import annotations


class RouterError(Exception):
    category: str = "internal_error"

    def __init__(self, message: str = "", *, category: str | None = None) -> None:
        super().__init__(message)
        if category is not None:
            self.category = category


class MissingTarget(RouterError):
    category = "missing_target"


class UnknownTarget(RouterError):
    category = "unknown_target"


class MissingDestination(RouterError):
    category = "missing_destination"


class TargetConfigurationInvalid(RouterError):
    category = "target_configuration_invalid"


class TargetExportFailed(RouterError):
    category = "target_export_failed"


class UnsafeDestination(RouterError):
    category = "unsafe_destination"


class TargetResultInvalid(RouterError):
    category = "target_result_invalid"
