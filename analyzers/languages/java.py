"""Java language analyzer."""

from typing import Iterator, List, Dict, Any
import logging

from ..base import LanguageAnalyzer, CodeChunk, CallRelationship, ImportRelationship

logger = logging.getLogger(__name__)


class JavaAnalyzer(LanguageAnalyzer):
    """
    Analyzer for Java files.

    This is a minimal example showing that not all languages
    need complex analysis. Java can rely on CocoIndex's built-in
    chunking while only extracting imports.
    """

    @property
    def supported_extensions(self) -> List[str]:
        return [".java"]

    @property
    def language_name(self) -> str:
        return "java"

    def extract_call_relationships(
        self,
        chunk: CodeChunk
    ) -> Iterator[CallRelationship]:
        """
        Java doesn't need special call extraction in this example.
        CocoIndex's syntax-aware chunking is sufficient.
        """
        return []

    def extract_import_relationships(
        self,
        chunk: CodeChunk
    ) -> Iterator[ImportRelationship]:
        """Extract Java import statements using simple regex."""
        import re

        # Match import statements
        import_pattern = r'import\s+(?:static\s+)?([a-zA-Z_][a-zA-Z0-9_.]*(?:\.\*)?)\s*;'

        for match in re.finditer(import_pattern, chunk.text):
            import_path = match.group(1)
            is_static = 'static' in match.group(0)
            is_wildcard = import_path.endswith('.*')

            if is_wildcard:
                import_path = import_path[:-2]  # Remove .*
                items = ["*"]
            else:
                # Extract the class name
                parts = import_path.split('.')
                items = [parts[-1]] if parts else []

            yield ImportRelationship(
                filename=chunk.filename,
                imported_from=import_path,
                imported_items=items,
                import_type="static" if is_static else "wildcard" if is_wildcard else "class",
                line=chunk.text[:match.start()].count('\n') + chunk.start_line
            )

    def extract_custom_metadata(
        self,
        chunk: CodeChunk
    ) -> Dict[str, Any]:
        """Extract Java-specific metadata."""
        metadata = {}

        # Check for annotations
        if "@" in chunk.text:
            import re
            annotations = re.findall(r'@([A-Z][a-zA-Z0-9]*)', chunk.text)
            if annotations:
                metadata["annotations"] = list(set(annotations))

                # Common Java patterns
                if "Override" in annotations:
                    metadata["has_overrides"] = True
                if any(a in annotations for a in ["Test", "BeforeEach", "AfterEach"]):
                    metadata["is_test"] = True
                if "Deprecated" in annotations:
                    metadata["has_deprecated"] = True

        # Check for common keywords
        if "public class" in chunk.text:
            metadata["has_public_class"] = True
        if "interface " in chunk.text:
            metadata["has_interface"] = True
        if "enum " in chunk.text:
            metadata["has_enum"] = True
        if "abstract " in chunk.text:
            metadata["has_abstract"] = True

        return metadata
