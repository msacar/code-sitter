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
src_dir = current_file.parent.parent.parent  # flows -> code_sitter -> src
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from cocoindex import FlowBuilder, sources, functions
from sentence_transformers import SentenceTransformer
import logging

from code_sitter.analyzers import (
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

# Initialize the flow
flow = FlowBuilder("FlexibleCodeIndex")

# Configure source files - now supports many more languages!
all_patterns = []
for ext in supported_exts.keys():
    all_patterns.append(f"**/*{ext}")

files = flow.add_source(
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

def extract_extension(filename: str) -> str:
    """Extract file extension from filename."""
    return os.path.splitext(filename)[1].lower()

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
        ".ts": "typescript",
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

# Add file metadata
files["ext"] = files["filename"].transform(extract_extension)
files["language"] = files["filename"].transform(get_language_for_cocoindex)

# Configure syntax-aware chunking
files["chunks"] = files["content"].transform(
    functions.SplitRecursively(),
    language=files["language"],
    chunk_size=1000,
    chunk_overlap=200,
    respect_syntax=True,
)

@flow.register_op
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

# Apply analysis to all files
files = files.transform(analyze_chunk)

# Extract chunk metadata for embedding
@flow.register_op
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

files["chunk_metadata"] = files.apply(
    lambda row: [
        extract_chunk_metadata(chunk, row["filename"])
        for chunk in row.get("chunks", [])
    ]
)

# Flatten chunks for embedding processing
chunks_flow = files.explode("chunk_metadata")
chunks_flow["chunk_data"] = chunks_flow["chunk_metadata"]

# Initialize embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")

@flow.register_op
def generate_code_embedding(chunk_text: str) -> List[float]:
    """Generate vector embedding for code chunk."""
    if not chunk_text:
        return []
    cleaned_text = chunk_text.strip()
    embedding = embedder.encode(cleaned_text)
    return embedding.tolist()

# Add embeddings
chunks_flow["embedding"] = chunks_flow["chunk_data"].apply(
    lambda chunk: generate_code_embedding(chunk.get("text", ""))
)

# Configure storage based on environment
if os.getenv("USE_POSTGRES", "false").lower() == "true":
    # PostgreSQL storage with separate tables

    # Store code chunks with embeddings
    chunks_flow.add_sink(
        functions.sinks.Postgres(
            connection_string=os.getenv(
                "DATABASE_URL",
                "postgresql://localhost:5432/code_index"
            ),
            table_name="code_chunks",
            columns={
                "filename": "text",
                "chunk_index": "integer",
                "chunk_text": "text",
                "start_line": "integer",
                "end_line": "integer",
                "node_type": "text",
                "symbols": "text[]",
                "embedding": "vector(384)",
                "language": "text",
                "custom_metadata": "jsonb",
            },
            vector_column="embedding",
            on_conflict="update",
        )
    )

    # Store call relationships
    calls_flow = files.explode("call_relationships")
    calls_flow.add_sink(
        functions.sinks.Postgres(
            connection_string=os.getenv("DATABASE_URL"),
            table_name="call_relationships",
            columns={
                "filename": "text",
                "chunk_index": "integer",
                "caller": "text",
                "callee": "text",
                "arguments": "text[]",
                "line": "integer",
                "column": "integer",
                "context": "text",
                "language": "text",
            },
            on_conflict="update",
        )
    )

    # Store import relationships
    imports_flow = files.explode("import_relationships")
    imports_flow.add_sink(
        functions.sinks.Postgres(
            connection_string=os.getenv("DATABASE_URL"),
            table_name="import_relationships",
            columns={
                "filename": "text",
                "chunk_index": "integer",
                "imported_from": "text",
                "imported_items": "text[]",
                "import_type": "text",
                "line": "integer",
                "language": "text",
            },
            on_conflict="update",
        )
    )
else:
    # JSON file storage for development

    # Main index
    chunks_flow.add_sink(
        functions.sinks.JsonFile(
            path="./code_index.json",
            mode="overwrite",
        )
    )

    # Call relationships
    @flow.register_op
    def collect_calls(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Collect all call relationships."""
        all_calls = []
        for row in rows:
            calls = row.get("call_relationships", [])
            for call in calls:
                call["language"] = row.get("analyzer_language", "unknown")
                all_calls.append(call)
        return all_calls

    calls_data = files.collect().transform(collect_calls)
    calls_data.add_sink(
        functions.sinks.JsonFile(
            path="./call_relationships.json",
            mode="overwrite",
        )
    )

    # Import relationships
    @flow.register_op
    def collect_imports(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Collect all import relationships."""
        all_imports = []
        for row in rows:
            imports = row.get("import_relationships", [])
            for imp in imports:
                imp["language"] = row.get("analyzer_language", "unknown")
                all_imports.append(imp)
        return all_imports

    imports_data = files.collect().transform(collect_imports)
    imports_data.add_sink(
        functions.sinks.JsonFile(
            path="./import_relationships.json",
            mode="overwrite",
        )
    )

# Build symbol index
@flow.register_op
def build_symbol_index(rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Build an index of symbols to their locations."""
    symbol_index = {}

    for row in rows:
        chunk_data = row.get("chunk_data", {})
        symbols = chunk_data.get("symbols", [])

        for symbol in symbols:
            if symbol not in symbol_index:
                symbol_index[symbol] = []

            symbol_index[symbol].append({
                "filename": chunk_data.get("filename"),
                "line_start": chunk_data.get("start_line"),
                "line_end": chunk_data.get("end_line"),
                "chunk_text": chunk_data.get("text", "")[:100] + "...",
                "language": row.get("analyzer_language", "unknown")
            })

    return symbol_index

# Export symbol index
symbol_index = chunks_flow.collect().transform(build_symbol_index)
symbol_index.add_sink(
    functions.sinks.JsonFile(
        path="./symbol_index.json",
        mode="overwrite",
    )
)

# Language statistics
@flow.register_op
def build_language_stats(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build statistics about analyzed languages."""
    stats = {
        "total_files": 0,
        "languages": {},
        "analyzers_used": set()
    }

    for row in rows:
        stats["total_files"] += 1

        lang = row.get("analyzer_language", "unknown")
        if lang not in stats["languages"]:
            stats["languages"][lang] = {
                "file_count": 0,
                "call_count": 0,
                "import_count": 0,
                "has_analyzer": row.get("has_analyzer", False)
            }

        stats["languages"][lang]["file_count"] += 1
        stats["languages"][lang]["call_count"] += len(row.get("call_relationships", []))
        stats["languages"][lang]["import_count"] += len(row.get("import_relationships", []))

        if row.get("has_analyzer"):
            stats["analyzers_used"].add(lang)

    stats["analyzers_used"] = list(stats["analyzers_used"])
    return stats

language_stats = files.collect().transform(build_language_stats)
language_stats.add_sink(
    functions.sinks.JsonFile(
        path="./language_stats.json",
        mode="overwrite",
    )
)

if __name__ == "__main__":
    logger.info("Starting flexible code indexing with pluggable analyzers...")
    logger.info(f"Supported languages: {list(supported_exts.values())}")
    flow.run()
