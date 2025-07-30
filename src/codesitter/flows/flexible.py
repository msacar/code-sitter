"""
Flexible Flow with Pluggable Language Analyzers

This module provides a flexible code indexing flow that uses
language-specific analyzers for enhanced code analysis.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the src directory to Python path for imports
current_file = Path(__file__).resolve()
src_dir = current_file.parent.parent.parent  # flows -> codesitter -> src
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from cocoindex import FlowBuilder, sources, functions, op, flow_def, DataScope, VectorIndexDef, VectorSimilarityMetric
from sentence_transformers import SentenceTransformer
import logging

from codesitter.analyzers import (
    get_registry,
    auto_discover_analyzers,
    register_defaults,
    CodeChunk,
    get_analyzer
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize analyzer registry
logger.info("Initializing language analyzers...")
register_defaults()  # Register default analyzers
auto_discover_analyzers()  # Auto-discover custom analyzers

# Show registered languages
registry = get_registry()
supported_exts = registry.list_supported_extensions()
logger.info(f"Registered language support for: {list(supported_exts.keys())}")

# -----------------------------------------------------------------------------
# Helper functions for the flow

@op.function()
def extract_extension(filename: str) -> str:
    """Extract file extension from filename."""
    return os.path.splitext(filename)[1].lower()

@op.function()
def get_language_for_cocoindex(filename: str) -> str:
    """Map filename to language for CocoIndex chunking."""
    analyzer = get_analyzer(filename)
    if analyzer:
        return analyzer.language_name

    # Fallback mapping
    ext = extract_extension(filename)
    fallback_map = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",  # JSX uses JavaScript parser
        ".ts": "typescript",
        ".tsx": "typescript",  # TSX uses TypeScript parser
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".cs": "csharp",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
    }
    return fallback_map.get(ext, "text")

# Initialize embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")

@op.function()
def generate_code_embedding(chunk_text: str) -> List[float]:
    """Generate vector embedding for code chunk."""
    if not chunk_text:
        return []
    cleaned_text = chunk_text.strip()
    embedding = embedder.encode(cleaned_text)
    return embedding.tolist()

@op.function()
def analyze_chunk(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze chunks using language-specific analyzers.

    Returns enhanced chunk data with:
    - Call relationships
    - Import relationships
    - Custom metadata
    """
    filename = row.get("filename", "")
    chunks = row.get("chunks", [])

    analyzer = get_analyzer(filename)

    all_calls = []
    all_imports = []

    for i, chunk in enumerate(chunks):
        # Convert to CodeChunk object
        if isinstance(chunk, dict):
            chunk_obj = CodeChunk(
                text=chunk.get("text", ""),
                filename=filename,
                start_line=chunk.get("start_line", 0),
                end_line=chunk.get("end_line", 0),
                node_type=chunk.get("node_type", "unknown"),
                symbols=chunk.get("symbols", [])
            )
        else:
            # Fallback for simple text chunks
            chunk_obj = CodeChunk(
                text=str(chunk),
                filename=filename,
                start_line=0,
                end_line=0,
                node_type="unknown",
                symbols=[]
            )

        # Use analyzer if available
        if analyzer:
            # Check if chunk should be analyzed
            if analyzer.should_analyze_chunk(chunk_obj):
                # Preprocess chunk
                chunk_obj = analyzer.preprocess_chunk(chunk_obj)

                # Extract relationships
                try:
                    calls = list(analyzer.extract_call_relationships(chunk_obj))
                    all_calls.extend([{
                        "chunk_index": i,
                        "filename": call.filename,
                        "caller": call.caller,
                        "callee": call.callee,
                        "arguments": call.arguments,
                        "line": call.line,
                        "column": call.column,
                        "context": call.context
                    } for call in calls])

                    imports = list(analyzer.extract_import_relationships(chunk_obj))
                    all_imports.extend([{
                        "chunk_index": i,
                        "filename": imp.filename,
                        "imported_from": imp.imported_from,
                        "imported_items": imp.imported_items,
                        "import_type": imp.import_type,
                        "line": imp.line
                    } for imp in imports])

                    # Add custom metadata
                    custom_metadata = analyzer.extract_custom_metadata(chunk_obj)
                    if custom_metadata and isinstance(chunk, dict):
                        chunk["custom_metadata"] = custom_metadata

                except Exception as e:
                    logger.error(f"Error analyzing chunk in {filename}: {e}")

    # Return enhanced row data
    return {
        **row,
        "call_relationships": all_calls,
        "import_relationships": all_imports,
        "has_analyzer": analyzer is not None,
        "analyzer_language": analyzer.language_name if analyzer else None
    }

@op.function()
def extract_chunk_metadata(chunk: Dict[str, Any], filename: str) -> Dict[str, Any]:
    """Extract metadata from code chunks."""
    return {
        "text": chunk.get("text", ""),
        "filename": filename,
        "chunk_index": chunk.get("index", 0),
        "start_line": chunk.get("start_line", 0),
        "end_line": chunk.get("end_line", 0),
        "node_type": chunk.get("node_type", "unknown"),
        "symbols": chunk.get("symbols", []),
        "custom_metadata": chunk.get("custom_metadata", {})
    }

# -----------------------------------------------------------------------------
# Define the flexible code indexing flow
@flow_def(name="FlexibleCodeIndex")
def flexible_code_index_flow(flow_builder: FlowBuilder, data_scope: DataScope):
    """
    Flexible code indexing flow with pluggable language analyzers.
    """
    # Configure source files - now supports many more languages!
    all_patterns = []
    for ext in supported_exts.keys():
        all_patterns.append(f"**/*{ext}")

    data_scope["files"] = flow_builder.add_source(
        sources.LocalFile(
            path=".",
            included_patterns=all_patterns,
            excluded_patterns=[
                "**/node_modules/**",
                "**/dist/**",
                "**/build/**",
                "**/.next/**",
                "**/coverage/**",
                "**/*.min.js",
                "**/.git/**",
                "**/venv/**",
                "**/__pycache__/**",
                "**/.venv/**",
                "**/target/**",  # Rust
                "**/vendor/**",  # Go
                "**/.bundle/**", # Ruby
            ],
        )
    )

    # Add file metadata
    # Use data_scope directly without aliasing to avoid struct type errors
    data_scope["files"]["ext"] = (
        data_scope["files"]["filename"]
        .transform(extract_extension)
    )
    data_scope["files"]["language"] = (
        data_scope["files"]["filename"]
        .transform(get_language_for_cocoindex)
    )

    # Note: Cannot log DataSlice objects directly
    logger.info(f"Source files configured, supported languages: {list(supported_exts.values())}")

    # Configure syntax-aware chunking
    data_scope["files"]["chunks"] = data_scope["files"]["content"].transform(
        functions.SplitRecursively(),
        language=data_scope["files"]["language"],
        chunk_size=1000,
        chunk_overlap=200,
        respect_syntax=True,
    )

    # Apply analysis to all files
    data_scope["files"] = data_scope["files"].transform(analyze_chunk)

    # Add collectors
    code_embeddings = data_scope.add_collector()

    # Process chunks for embedding
    with data_scope["files"].row() as file:
        # Debug log per file (safe within row context)
        # Using single quotes inside the f-string for clarity
        logger.debug(f"Processing file: {file['filename']}")

        # Process each chunk in the file
        with file["chunks"].row() as chunk:
            # Generate embedding for chunk text
            chunk["embedding"] = chunk["text"].transform(generate_code_embedding)

            # Collect chunk data with embedding
            code_embeddings.collect(
                filename=file["filename"],
                location=chunk["location"],
                chunk_text=chunk["text"],
                embedding=chunk["embedding"],
                language=file["language"]
            )

    # Configure storage based on environment
    if os.getenv("USE_POSTGRES", "false").lower() == "true":
        # PostgreSQL storage - export directly from collector
        code_embeddings.export(
            "code_chunks",
            functions.storages.Postgres(
                connection_string=os.getenv(
                    "DATABASE_URL",
                    "postgresql://localhost:5432/code_index"
                ),
            ),
            primary_key_fields=["filename", "location"],
            vector_indexes=[
                VectorIndexDef("embedding", VectorSimilarityMetric.COSINE_SIMILARITY)
            ]
        )
    else:
        # JSON file storage for development
        code_embeddings.export(
            "code_index",
            functions.storages.JsonFile(
                path="./code_index.json",
                mode="overwrite",
            ),
            primary_key_fields=["filename", "location"]
        )

# Make flow available at module level
flow = flexible_code_index_flow

if __name__ == "__main__":
    logger.info("Starting flexible code indexing with pluggable analyzers...")
    logger.info(f"Supported languages: {list(supported_exts.values())}")
    flow.run()
