"""
Smart Chunking Flow - Uses our custom chunker for better analysis

This flow:
1. Analyzes files completely first
2. Creates intelligent chunks with full context
3. Enables better incremental indexing
4. Preserves all relationships and imports
"""

import os
from typing import List, Dict, Any
from pathlib import Path
import logging

from cocoindex import (
    FlowBuilder,
    sources,
    op,
    flow_def,
    DataScope,
    transform_flow,
)

from sentence_transformers import SentenceTransformer

from codesitter.chunkers import SmartChunker, ChunkResult

logger = logging.getLogger(__name__)

# Initialize the smart chunker
smart_chunker = SmartChunker()

# Initialize embedder
embedder = SentenceTransformer("all-MiniLM-L6-v2")


@op
def smart_chunk_file(content: str, path: str) -> List[Dict[str, Any]]:
    """
    Use our smart chunker to create intelligent chunks.

    Returns a list of chunk dictionaries compatible with CocoIndex.
    """
    logger.info(f"Smart chunking file: {path}")

    try:
        # Get smart chunks
        chunk_results = smart_chunker.chunk_file(path, content)

        # Convert to CocoIndex format
        chunks = []
        for i, chunk_result in enumerate(chunk_results):
            chunk_dict = {
                "text": chunk_result.text,
                "chunk_index": i,
                "chunk_type": chunk_result.chunk_type.value,
                "chunk_id": chunk_result.chunk_id,
                "content_hash": chunk_result.content_hash,
                "metadata": chunk_result.metadata,
                "file_path": chunk_result.file_path,
                "file_imports": chunk_result.file_imports,
                "file_exports": chunk_result.file_exports,
                "start_line": chunk_result.start_line,
                "end_line": chunk_result.end_line,
                "dependencies": chunk_result.dependencies or [],
                "dependents": chunk_result.dependents or []
            }
            chunks.append(chunk_dict)

        logger.info(f"Created {len(chunks)} smart chunks for {path}")
        return chunks

    except Exception as e:
        logger.error(f"Error chunking {path}: {e}")
        # Fallback to single chunk
        return [{
            "text": content,
            "chunk_index": 0,
            "chunk_type": "file_context",
            "chunk_id": f"{path}:full",
            "content_hash": str(hash(content)),
            "metadata": {"error": str(e)},
            "file_path": path,
            "file_imports": [],
            "file_exports": [],
            "start_line": 1,
            "end_line": len(content.split('\n')),
            "dependencies": [],
            "dependents": []
        }]


@op
def create_embedding(text: str) -> List[float]:
    """Create embeddings for semantic search."""
    return embedder.encode(text).tolist()


# Build the flow
flow = FlowBuilder("SmartChunkingFlow")

# Source files
files = flow.add_source(
    sources.LocalFile(
        path=".",
        included_patterns=[
            "*.ts", "*.tsx", "*.js", "*.jsx",  # JavaScript/TypeScript
            "*.py", "*.pyw",                    # Python
            "*.java",                           # Java
            "*.go",                             # Go
            "*.rs",                             # Rust
            "*.rb",                             # Ruby
            "*.php",                            # PHP
            "*.swift",                          # Swift
            "*.kt", "*.kts",                    # Kotlin
            "*.scala",                          # Scala
            "*.c", "*.cpp", "*.cc", "*.h",     # C/C++
            "*.cs",                             # C#
            "*.m", "*.mm",                      # Objective-C
            "*.lua",                            # Lua
            "*.dart",                           # Dart
            "*.r", "*.R",                       # R
            "*.jl",                             # Julia
            "*.ex", "*.exs",                    # Elixir
            "*.clj", "*.cljs",                  # Clojure
            "*.ml", "*.mli",                    # OCaml
            "*.fs", "*.fsi",                    # F#
            "*.v",                              # Verilog
            "*.vhd", "*.vhdl",                  # VHDL
            "*.elm",                            # Elm
            "*.purs",                           # PureScript
            "*.nim",                            # Nim
            "*.zig",                            # Zig
        ],
        excluded_patterns=[
            "**/node_modules/**",
            "**/.git/**",
            "**/dist/**",
            "**/build/**",
            "**/__pycache__/**",
            "**/.venv/**",
            "**/venv/**",
            "**/*.min.js",
            "**/*.min.css",
        ],
    )
)

# Apply smart chunking
chunks = files["content"].transform(
    smart_chunk_file,
    path=files["path"]
).explode()

# Add embeddings for semantic search
chunks["embedding"] = chunks["text"].transform(create_embedding)

# Select columns for output
output = chunks.select(
    path=chunks["file_path"],
    chunk_index=chunks["chunk_index"],
    chunk_type=chunks["chunk_type"],
    chunk_id=chunks["chunk_id"],
    content_hash=chunks["content_hash"],
    text=chunks["text"],
    embedding=chunks["embedding"],
    metadata=chunks["metadata"],
    file_imports=chunks["file_imports"],
    file_exports=chunks["file_exports"],
    start_line=chunks["start_line"],
    end_line=chunks["end_line"],
    dependencies=chunks["dependencies"],
    dependents=chunks["dependents"]
)

# Storage configuration
if os.getenv("USE_POSTGRES", "false").lower() == "true":
    from cocoindex.sinks import Postgres

    # PostgreSQL storage
    flow.add_sink(
        Postgres(
            table_name="smart_chunks",
            connection_string=os.getenv("COCOINDEX_DATABASE_URL"),
            vector_column="embedding",
            vector_size=384,
            columns={
                "path": "TEXT",
                "chunk_index": "INTEGER",
                "chunk_type": "TEXT",
                "chunk_id": "TEXT PRIMARY KEY",
                "content_hash": "TEXT",
                "text": "TEXT",
                "embedding": f"vector(384)",
                "metadata": "JSONB",
                "file_imports": "JSONB",
                "file_exports": "JSONB",
                "start_line": "INTEGER",
                "end_line": "INTEGER",
                "dependencies": "TEXT[]",
                "dependents": "TEXT[]"
            },
            drop_existing_table=True,
        ),
        output
    )
else:
    from cocoindex.sinks import JsonFile

    # JSON file storage
    flow.add_sink(
        JsonFile(path="./smart_chunks_index.json"),
        output
    )

# Export the flow
flow_def = flow.build()

if __name__ == "__main__":
    # Run directly
    flow.update()
    print("Smart chunking complete!")
