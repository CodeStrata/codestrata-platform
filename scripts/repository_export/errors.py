"""Bounded exporter error taxonomy."""

from __future__ import annotations


class ExportError(Exception):
    """Base exporter error with a stable machine category."""

    category: str = "internal_error"

    def __init__(self, message: str = "", *, category: str | None = None) -> None:
        super().__init__(message)
        if category is not None:
            self.category = category


class SourceRootInvalid(ExportError):
    category = "source_root_invalid"


class SourceLayoutInvalid(ExportError):
    category = "source_layout_invalid"


class SourceFileUnclassified(ExportError):
    category = "source_file_unclassified"


class ProhibitedSourceFile(ExportError):
    category = "prohibited_source_file"


class UnsafeDestination(ExportError):
    category = "unsafe_destination"


class DestinationInsideSource(ExportError):
    category = "destination_inside_source"


class DestinationSymlink(ExportError):
    category = "destination_symlink"


class UnmanagedDestination(ExportError):
    category = "unmanaged_destination"


class UnmanagedDestinationFile(ExportError):
    category = "unmanaged_destination_file"


class DestinationManifestInvalid(ExportError):
    category = "destination_manifest_invalid"


class PathCollision(ExportError):
    category = "path_collision"


class CaseCollision(ExportError):
    category = "case_collision"


class SymlinkNotAllowed(ExportError):
    category = "symlink_not_allowed"


class PermissionNotAllowed(ExportError):
    category = "permission_not_allowed"


class GeneratedFileInvalid(ExportError):
    category = "generated_file_invalid"


class DocumentationLinkInvalid(ExportError):
    category = "documentation_link_invalid"


class ManifestValidationFailed(ExportError):
    category = "manifest_validation_failed"


class InventoryValidationFailed(ExportError):
    category = "inventory_validation_failed"


class ChecksumValidationFailed(ExportError):
    category = "checksum_validation_failed"


class AtomicWriteFailed(ExportError):
    category = "atomic_write_failed"
