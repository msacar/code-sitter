"""Smart chunking implementation that creates meaningful, context-aware chunks."""

import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from tree_sitter import Node, Tree

from .base import ChunkResult, ChunkType
from ..analyzers import get_analyzer, get_registry
from ..analyzers.base import LanguageAnalyzer, CodeChunk as AnalyzerCodeChunk

logger = logging.getLogger(__name__)


class SmartChunker:
    """Creates intelligent chunks based on code structure analysis."""

    def __init__(self):
        self.registry = get_registry()

    def chunk_file(self, file_path: str, content: str) -> List[ChunkResult]:
        """
        Create smart chunks from a file.

        Each chunk will be a complete, meaningful unit:
        - Full functions with their context
        - Complete classes
        - Import blocks
        - Type definitions
        """
        ext = Path(file_path).suffix
        analyzer = get_analyzer(ext)

        if not analyzer:
            logger.warning(f"No analyzer for {ext}, falling back to basic chunking")
            return self._basic_chunking(file_path, content)

        # Use analyzer to understand the file structure
        analysis_result = self._analyze_file(analyzer, file_path, content)

        # Create smart chunks from analysis
        chunks = []

        # Create import/context chunk
        if analysis_result['imports']:
            import_chunk = self._create_import_chunk(
                file_path,
                analysis_result['imports'],
                content
            )
            if import_chunk:
                chunks.append(import_chunk)

        # Create function chunks with context
        for func in analysis_result['functions']:
            chunk = self._create_function_chunk(
                file_path,
                func,
                analysis_result['imports'],
                analysis_result['exports'],
                content
            )
            chunks.append(chunk)

        # Create class chunks
        for cls in analysis_result['classes']:
            chunk = self._create_class_chunk(
                file_path,
                cls,
                analysis_result['imports'],
                analysis_result['exports'],
                content
            )
            chunks.append(chunk)

        # If no chunks were created, create a single file chunk
        if not chunks:
            chunks = [self._create_file_chunk(file_path, content)]

        # Link dependencies
        self._link_chunk_dependencies(chunks)

        return chunks

    def _analyze_file(self, analyzer: LanguageAnalyzer, file_path: str, content: str) -> Dict[str, Any]:
        """Use analyzer to extract file structure."""
        # Create a single chunk representing the whole file for analysis
        whole_file_chunk = AnalyzerCodeChunk(
            content=content,
            start_line=1,
            end_line=len(content.split('\n')),
            file_path=file_path,
            chunk_index=0,
            total_chunks=1,
            language=analyzer.language_name,
            node_type="file"
        )

        # Extract information using analyzer
        result = {
            'imports': [],
            'exports': [],
            'functions': [],
            'classes': [],
            'metadata': {}
        }

        # Get custom metadata if analyzer supports it
        if hasattr(analyzer, 'extract_custom_metadata'):
            try:
                result['metadata'] = analyzer.extract_custom_metadata(whole_file_chunk)
            except Exception as e:
                logger.debug(f"Could not extract custom metadata: {e}")

        # Extract imports if analyzer supports it
        if hasattr(analyzer, 'extract_import_relationships'):
            try:
                for imp in analyzer.extract_import_relationships(whole_file_chunk):
                    result['imports'].append({
                        'source': imp.source,
                        'items': imp.imported_items,
                        'type': imp.import_type,
                        'line': imp.line,
                        'text': f"import {', '.join(imp.imported_items)} from '{imp.source}'"
                    })
            except Exception as e:
                logger.debug(f"Could not extract imports: {e}")

        # For now, use simple extraction for functions and classes
        # This could be enhanced with AST parsing per language
        result['functions'] = self._extract_functions_simple(content)
        result['classes'] = self._extract_classes_simple(content)
        result['exports'] = self._extract_exports_simple(content)

        return result

    def _extract_functions_simple(self, content: str) -> List[Dict[str, Any]]:
        """Simple function extraction based on common patterns."""
        functions = []
        lines = content.split('\n')

        function_patterns = [
            (r'^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)', 'function'),
            (r'^\s*(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\(', 'arrow'),
            (r'^\s*(?:export\s+)?(?:let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(', 'arrow'),
            (r'^\s*(\w+)\s*\(.*\)\s*{', 'method'),  # Simple method pattern
        ]

        import re

        for i, line in enumerate(lines):
            for pattern, func_type in function_patterns:
                match = re.match(pattern, line)
                if match:
                    func_name = match.group(1)

                    # Find the end of the function (simple brace counting)
                    start_line = i + 1
                    end_line = self._find_block_end(lines, i)

                    functions.append({
                        'name': func_name,
                        'type': func_type,
                        'start_line': start_line,
                        'end_line': end_line,
                        'text': '\n'.join(lines[i:end_line])
                    })
                    break

        return functions

    def _extract_classes_simple(self, content: str) -> List[Dict[str, Any]]:
        """Simple class extraction."""
        classes = []
        lines = content.split('\n')

        import re
        class_pattern = r'^\s*(?:export\s+)?class\s+(\w+)'

        for i, line in enumerate(lines):
            match = re.match(class_pattern, line)
            if match:
                class_name = match.group(1)
                start_line = i + 1
                end_line = self._find_block_end(lines, i)

                classes.append({
                    'name': class_name,
                    'start_line': start_line,
                    'end_line': end_line,
                    'text': '\n'.join(lines[i:end_line])
                })

        return classes

    def _extract_exports_simple(self, content: str) -> List[str]:
        """Simple export extraction."""
        exports = []
        import re

        patterns = [
            r'export\s+(?:function|class|const|let|var)\s+(\w+)',
            r'export\s+{\s*([^}]+)\s*}',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if ',' in match:  # Named exports
                    exports.extend([name.strip() for name in match.split(',')])
                else:
                    exports.append(match)

        return list(set(exports))  # Remove duplicates

    def _find_block_end(self, lines: List[str], start_idx: int) -> int:
        """Find the end of a code block using brace counting."""
        brace_count = 0
        in_string = False
        string_char = None

        for i in range(start_idx, len(lines)):
            line = lines[i]

            for j, char in enumerate(line):
                # Handle string literals
                if char in ['"', "'", '`'] and (j == 0 or line[j-1] != '\\'):
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif char == string_char:
                        in_string = False
                        string_char = None

                # Count braces only outside strings
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1

                        if brace_count == 0 and i > start_idx:
                            return i + 1

        return len(lines)

    def _create_import_chunk(self, file_path: str, imports: List[Dict], content: str) -> Optional[ChunkResult]:
        """Create a chunk for imports and file context."""
        if not imports:
            return None

        # Get all import lines
        import_lines = []
        for imp in imports:
            import_lines.append(imp.get('text', f"import from '{imp['source']}'"))

        import_text = '\n'.join(import_lines)

        return ChunkResult(
            text=import_text,
            chunk_type=ChunkType.IMPORTS,
            chunk_id=f"{file_path}:imports",
            content_hash=hashlib.md5(import_text.encode()).hexdigest(),
            metadata={
                "imports": imports,
                "import_count": len(imports)
            },
            file_path=file_path,
            file_imports=imports,
            file_exports=[],  # Will be filled later
            start_line=1,
            end_line=max(imp.get('line', 1) for imp in imports) if imports else 1
        )

    def _create_function_chunk(self, file_path: str, func: Dict, imports: List[Dict],
                              exports: List[str], content: str) -> ChunkResult:
        """Create a chunk for a function with full context."""

        # Build context-aware chunk text
        chunk_lines = [
            f"// File: {file_path}",
            f"// Function: {func['name']}",
            ""
        ]

        # Add relevant imports (those used by this function)
        # For now, add all imports - we can optimize later
        for imp in imports:
            chunk_lines.append(imp.get('text', f"import from '{imp['source']}'"))

        if imports:
            chunk_lines.append("")

        # Add the function itself
        chunk_lines.append(func['text'])

        chunk_text = '\n'.join(chunk_lines)

        return ChunkResult(
            text=chunk_text,
            chunk_type=ChunkType.FUNCTION,
            chunk_id=f"{file_path}:{func['name']}",
            content_hash=hashlib.md5(func['text'].encode()).hexdigest(),
            metadata={
                "function_name": func['name'],
                "function_type": func.get('type', 'function'),
                "is_exported": func['name'] in exports,
                "original_text": func['text']
            },
            file_path=file_path,
            file_imports=imports,
            file_exports=exports,
            start_line=func['start_line'],
            end_line=func['end_line']
        )

    def _create_class_chunk(self, file_path: str, cls: Dict, imports: List[Dict],
                           exports: List[str], content: str) -> ChunkResult:
        """Create a chunk for a class with full context."""

        # Build context-aware chunk text
        chunk_lines = [
            f"// File: {file_path}",
            f"// Class: {cls['name']}",
            ""
        ]

        # Add imports
        for imp in imports:
            chunk_lines.append(imp.get('text', f"import from '{imp['source']}'"))

        if imports:
            chunk_lines.append("")

        # Add the class
        chunk_lines.append(cls['text'])

        chunk_text = '\n'.join(chunk_lines)

        return ChunkResult(
            text=chunk_text,
            chunk_type=ChunkType.CLASS,
            chunk_id=f"{file_path}:{cls['name']}",
            content_hash=hashlib.md5(cls['text'].encode()).hexdigest(),
            metadata={
                "class_name": cls['name'],
                "is_exported": cls['name'] in exports,
                "original_text": cls['text']
            },
            file_path=file_path,
            file_imports=imports,
            file_exports=exports,
            start_line=cls['start_line'],
            end_line=cls['end_line']
        )

    def _create_file_chunk(self, file_path: str, content: str) -> ChunkResult:
        """Create a single chunk for the entire file."""
        return ChunkResult(
            text=content,
            chunk_type=ChunkType.FILE_CONTEXT,
            chunk_id=f"{file_path}:full",
            content_hash=hashlib.md5(content.encode()).hexdigest(),
            metadata={"language": "unknown"},
            file_path=file_path,
            file_imports=[],
            file_exports=[]
        )

    def _link_chunk_dependencies(self, chunks: List[ChunkResult]):
        """Analyze and link dependencies between chunks."""
        # TODO: Implement dependency analysis
        # For now, just mark imports as dependencies for all code chunks
        import_chunk_id = None

        for chunk in chunks:
            if chunk.chunk_type == ChunkType.IMPORTS:
                import_chunk_id = chunk.chunk_id
                chunk.dependents = []
                break

        if import_chunk_id:
            for chunk in chunks:
                if chunk.chunk_type != ChunkType.IMPORTS:
                    chunk.dependencies = [import_chunk_id]
                    chunks[0].dependents.append(chunk.chunk_id)

    def _basic_chunking(self, file_path: str, content: str) -> List[ChunkResult]:
        """Fallback to basic chunking for unsupported languages."""
        # Just create one chunk with the whole file
        return [self._create_file_chunk(file_path, content)]
