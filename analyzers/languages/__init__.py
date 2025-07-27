"""Language-specific analyzer implementations."""

# Import all available analyzers here
# They will be auto-discovered by the registry

from .typescript import TypeScriptAnalyzer
from .python import PythonAnalyzer

__all__ = [
    'TypeScriptAnalyzer',
    'PythonAnalyzer',
]
