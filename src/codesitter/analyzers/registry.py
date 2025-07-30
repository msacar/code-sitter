"""
Analyzer Registry

Manages registration and lookup of language-specific analyzers.
"""

import os
import importlib
import logging
from typing import Dict, Optional, Type
from pathlib import Path

from .base import LanguageAnalyzer, DefaultAnalyzer

logger = logging.getLogger(__name__)


class AnalyzerRegistry:
    """Registry for language analyzers."""

    def __init__(self):
        self._analyzers: Dict[str, LanguageAnalyzer] = {}
        self._extension_map: Dict[str, str] = {}

    def register(self, analyzer: LanguageAnalyzer) -> None:
        """
        Register a language analyzer.

        Args:
            analyzer: The analyzer instance to register
        """
        language = analyzer.language_name

        if language in self._analyzers:
            logger.warning(f"Overwriting existing analyzer for {language}")

        self._analyzers[language] = analyzer

        # Map extensions to language
        for ext in analyzer.supported_extensions:
            self._extension_map[ext] = language

        logger.info(f"Registered {language} analyzer for extensions: {analyzer.supported_extensions}")

    def get_analyzer_for_file(self, filename: str) -> Optional[LanguageAnalyzer]:
        """
        Get the appropriate analyzer for a file.

        Args:
            filename: The file path

        Returns:
            The analyzer instance or None if no analyzer found
        """
        ext = os.path.splitext(filename)[1].lower()
        language = self._extension_map.get(ext)

        if language:
            return self._analyzers.get(language)

        return None

    def get_analyzer_by_language(self, language: str) -> Optional[LanguageAnalyzer]:
        """Get analyzer by language name."""
        return self._analyzers.get(language)

    def list_supported_extensions(self) -> Dict[str, str]:
        """Return mapping of extensions to languages."""
        return self._extension_map.copy()

    def auto_discover(self, path: str = None) -> None:
        """
        Auto-discover and load analyzer plugins.

        Args:
            path: Directory to search for analyzers.
                  Defaults to the 'languages' subdirectory.
        """
        if path is None:
            path = Path(__file__).parent / "languages"
        else:
            path = Path(path)

        if not path.exists():
            logger.warning(f"Analyzer directory {path} does not exist")
            return

        # Find all Python files in the languages directory
        for file_path in path.glob("*.py"):
            if file_path.name.startswith("_"):
                continue

            module_name = file_path.stem

            try:
                # Import the module
                module = importlib.import_module(f".languages.{module_name}", package="codesitter.analyzers")

                # Look for analyzer classes
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)

                    # Check if it's a class that inherits from LanguageAnalyzer
                    if (isinstance(attr, type) and
                        issubclass(attr, LanguageAnalyzer) and
                        attr is not LanguageAnalyzer and
                        attr is not DefaultAnalyzer):

                        # Instantiate and register
                        analyzer = attr()
                        self.register(analyzer)

            except Exception as e:
                logger.error(f"Failed to load analyzer from {module_name}: {e}")


# Global registry instance
_registry = AnalyzerRegistry()


def get_analyzer(filename: str) -> Optional[LanguageAnalyzer]:
    """
    Get the appropriate analyzer for a file.

    This is a convenience function that uses the global registry.
    """
    return _registry.get_analyzer_for_file(filename)


def register_analyzer(analyzer: LanguageAnalyzer) -> None:
    """Register an analyzer in the global registry."""
    _registry.register(analyzer)


def auto_discover_analyzers() -> None:
    """Auto-discover and load all available analyzers."""
    _registry.auto_discover()


def get_registry() -> AnalyzerRegistry:
    """Get the global registry instance."""
    return _registry


# Register default analyzers for common languages
def register_defaults():
    """Register default analyzers for languages without custom implementations."""
    defaults = [
        # Web languages
        DefaultAnalyzer([".html", ".htm"], "html"),
        DefaultAnalyzer([".css", ".scss", ".sass"], "css"),

        # Config languages
        DefaultAnalyzer([".json"], "json"),
        DefaultAnalyzer([".yaml", ".yml"], "yaml"),
        DefaultAnalyzer([".toml"], "toml"),
        DefaultAnalyzer([".xml"], "xml"),

        # Shell scripts
        DefaultAnalyzer([".sh", ".bash"], "bash"),

        # Other languages (can be overridden by custom analyzers)
        DefaultAnalyzer([".c"], "c"),
        DefaultAnalyzer([".cpp", ".cc", ".cxx"], "cpp"),
        DefaultAnalyzer([".rs"], "rust"),
        DefaultAnalyzer([".go"], "go"),
        DefaultAnalyzer([".rb"], "ruby"),
        DefaultAnalyzer([".php"], "php"),
        DefaultAnalyzer([".swift"], "swift"),
        DefaultAnalyzer([".kt"], "kotlin"),
    ]

    for analyzer in defaults:
        register_analyzer(analyzer)
