"""Base types and interfaces for smart chunking."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum


class ChunkType(Enum):
    """Types of chunks we can create."""
    FILE_CONTEXT = "file_context"
    IMPORTS = "imports"
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    TYPE_DEFINITION = "type_definition"
    INTERFACE = "interface"


@dataclass
class ChunkResult:
    """A chunk with full context and metadata."""
    text: str                          # The actual chunk content
    chunk_type: ChunkType             # What kind of chunk this is
    chunk_id: str                     # Stable ID for incremental updates
    content_hash: str                 # Hash of content for change detection
    metadata: Dict[str, Any]          # Rich metadata about the chunk

    # Context that every chunk needs
    file_path: str
    file_imports: List[Dict[str, Any]]  # All imports from the file
    file_exports: List[str]             # All exports from the file

    # Optional location info
    start_line: Optional[int] = None
    end_line: Optional[int] = None

    # For incremental indexing
    dependencies: List[str] = None      # Other chunks this depends on
    dependents: List[str] = None        # Chunks that depend on this
