"""Technology detector implementations."""

from codestrata.services.detectors.composite_technology_detector import (
    CompositeTechnologyDetector,
)
from codestrata.services.detectors.csharp_technology_detector import (
    CsharpTechnologyDetector,
)
from codestrata.services.detectors.java_technology_detector import (
    JavaTechnologyDetector,
)
from codestrata.services.detectors.javascript_technology_detector import (
    JavaScriptTechnologyDetector,
)
from codestrata.services.detectors.php_technology_detector import (
    PhpTechnologyDetector,
)

__all__ = [
    "CompositeTechnologyDetector",
    "CsharpTechnologyDetector",
    "JavaScriptTechnologyDetector",
    "JavaTechnologyDetector",
    "PhpTechnologyDetector",
]
