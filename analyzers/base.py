"""
Base Language Analyzer Interface

Defines the contract for language-specific analyzers that can be plugged
into the code indexing system.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Iterator, Optional
from dataclasses import dataclass


@dataclass
class CodeChunk:
    """Represents a chunk of code with metadata."""
    text: str
    filename: str
    start_line: int
    end_line: int
    node_type: str
    symbols: List[str]
    metadata: Dict[str, Any] = None


@dataclass
class CallRelationship:
    """Represents a function call relationship."""
    filename: str
    caller: str
    callee: str
    arguments: List[str]
    line: int
    column: int
    context: str


@dataclass
class ImportRelationship:
    """Represents an import/dependency relationship."""
    filename: str
    imported_from: str
    imported_items: List[str]
    import_type: str  # 'default', 'named', 'namespace', etc.
    line: int


class LanguageAnalyzer(ABC):
    """
    Abstract base class for language-specific analyzers.

    Each language can implement this interface to provide custom
    analysis capabilities beyond basic syntax-aware chunking.
    """

    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """Return list of file extensions this analyzer supports."""
        pass

    @property
    @abstractmethod
    def language_name(self) -> str:
        """Return the language name for Tree-sitter."""
        pass

    @abstractmethod
    def extract_call_relationships(
        self,
        chunk: CodeChunk
    ) -> Iterator[CallRelationship]:
        """
        Extract function call relationships from a code chunk.

        Args:
            chunk: Code chunk to analyze

        Yields:
            CallRelationship objects
        """
        pass

    def extract_import_relationships(
        self,
        chunk: CodeChunk
    ) -> Iterator[ImportRelationship]:
        """
        Extract import/dependency relationships.

        Default implementation returns nothing.
        Languages can override if they support imports.
        """
        return []

    def extract_custom_metadata(
        self,
        chunk: CodeChunk
    ) -> Dict[str, Any]:
        """
        Extract language-specific metadata from a chunk.

        Default implementation returns empty dict.
        Languages can override to add custom analysis.
        """
        return {}

    def should_analyze_chunk(self, chunk: CodeChunk) -> bool:
        """
        Determine if a chunk should be analyzed.

        Default implementation returns True for all chunks.
        Languages can override to filter chunks.
        """
        return True

    def preprocess_chunk(self, chunk: CodeChunk) -> CodeChunk:
        """
        Preprocess a chunk before analysis.

        Default implementation returns chunk unchanged.
        Languages can override to clean/transform chunks.
        """
        return chunk


class DefaultAnalyzer(LanguageAnalyzer):
    """
    Default analyzer that provides no custom analysis.

    Used for languages that don't need special handling
    beyond CocoIndex's built-in syntax-aware chunking.
    """

    def __init__(self, extensions: List[str], language: str):
        self._extensions = extensions
        self._language = language

    @property
    def supported_extensions(self) -> List[str]:
        return self._extensions

    @property
    def language_name(self) -> str:
        return self._language

    def extract_call_relationships(
        self,
        chunk: CodeChunk
    ) -> Iterator[CallRelationship]:
        """Default: no call extraction."""
        return []
