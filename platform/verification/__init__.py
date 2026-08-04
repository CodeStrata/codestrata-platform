"""CodeStrata Platform verification suites (not shipped in the Platform runtime).

Namespace-extended with ``engine/verification`` when both parents are on
``sys.path`` (see root ``pyproject.toml`` ``pythonpath``).
"""

from __future__ import annotations

from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)
