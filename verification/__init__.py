"""CodeStrata monorepo verification suites (repo/export only; not shipped in the wheel).

Namespace-extended so Engine and Platform suites under ``engine/verification/`` and
``platform/verification/`` share the ``verification`` package name when parents are
on ``sys.path``.
"""

from __future__ import annotations

from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)

__all__ = ["__version__"]

__version__ = "1.0.0"
