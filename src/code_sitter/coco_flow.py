"""
CocoIndex Flow Definition for TypeScript Code Indexing

This module defines the main flow for indexing TypeScript/TSX codebases
using CocoIndex's syntax-aware chunking and embedding capabilities.
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from cocoindex import FlowBuilder, sources, functions
from sentence_transformers import SentenceTransformer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the flow
flow = FlowBuilder("TypeScriptCodeIndex")

# Configure source files - recursively scan for TypeScript files
files = flow.add_source(
    sources.LocalFile(
        path=".",  # Start from current directory
        included_patterns=["**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx"],
        excluded_patterns=[
            "**/node_modules/**",
            "**/dist/**",
            "**/build/**",
            "**/.next/**",
            "**/coverage/**",
            "**/*.min.js",
            "**/.git/**",
            "**/venv/**",
            "**/__pycache__/**"
        ],
    )
)

def extract_extension(filename: str) -> str:
    """Extract file extension from filename."""
    return os.path.splitext(filename)[1].lower()

def get_language_from_ext(ext: str) -> str:
    """Map file extension to language identifier for Tree-sitter."""
    language_map = {
        ".ts": "typescript",
        ".tsx": "tsx",
        ".js": "javascript",
        ".jsx": "jsx",
    }
    return language_map.get(ext, "typescript")

# Add file metadata
files["ext"] = files["filename"].transform(extract_extension)
files["language"] = files["ext"].transform(get_language_from_ext)

# Configure syntax-aware chunking using Tree-sitter
files["chunks"] = files["content"].transform(
    functions.SplitRecursively(),
    language=files["language"],
    chunk_size=1000,  # Characters per chunk
    chunk_overlap=200,  # Overlap between chunks
    # Ensure chunks respect syntax boundaries
    respect_syntax=True,
)

# Extract additional metadata from chunks
@flow.register_op
def extract_chunk_metadata(chunk: Dict[str, Any], filename: str) -> Dict[str, Any]:
    """Extract metadata from code chunks including symbols and context."""
    return {
        "text": chunk.get("text", ""),
        "filename": filename,
        "chunk_index": chunk.get("index", 0),
        "start_line": chunk.get("start_line", 0),
        "end_line": chunk.get("end_line", 0),
        "node_type": chunk.get("node_type", "unknown"),
        "symbols": chunk.get("symbols", []),  # Function/class names in chunk
    }

files["chunk_metadata"] = files.apply(
    lambda row: [
        extract_chunk_metadata(chunk, row["filename"])
        for chunk in row.get("chunks", [])
    ]
)

# Flatten chunks for processing
files = files.explode("chunk_metadata")
files["chunk_data"] = files["chunk_metadata"]

# Initialize embedding model (using a lightweight model for code)
embedder = SentenceTransformer("all-MiniLM-L6-v2")

@flow.register_op
def generate_code_embedding(chunk_text: str) -> List[float]:
    """Generate vector embedding for code chunk."""
    if not chunk_text:
        return []

    # Clean the code text for better embedding
    cleaned_text = chunk_text.strip()

    # Generate embedding
    embedding = embedder.encode(cleaned_text)
    return embedding.tolist()

# Add embeddings to chunks
files["embedding"] = files["chunk_data"].apply(
    lambda chunk: generate_code_embedding(chunk.get("text", ""))
)

# Configure PostgreSQL sink with pgvector for storage
if os.getenv("USE_POSTGRES", "false").lower() == "true":
    flow.add_sink(
        functions.sinks.Postgres(
            connection_string=os.getenv(
                "DATABASE_URL",
                "postgresql://localhost:5432/code_index"
            ),
            table_name="typescript_code_index",
            columns={
                "filename": "text",
                "chunk_index": "integer",
                "chunk_text": "text",
                "start_line": "integer",
                "end_line": "integer",
                "node_type": "text",
                "symbols": "text[]",
                "embedding": "vector(384)",  # all-MiniLM-L6-v2 produces 384-dim vectors
            },
            vector_column="embedding",
            on_conflict="update",  # Update existing chunks
        )
    )
else:
    # Alternative: JSON file sink for development
    flow.add_sink(
        functions.sinks.JsonFile(
            path="./code_index.json",
            mode="overwrite",
        )
    )

# Add symbol index for quick lookups
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
                "chunk_text": chunk_data.get("text", "")[:100] + "...",  # Preview
            })

    return symbol_index

# Export symbol index separately
symbol_index = flow.collect().transform(build_symbol_index)
symbol_index.add_sink(
    functions.sinks.JsonFile(
        path="./symbol_index.json",
        mode="overwrite",
    )
)

if __name__ == "__main__":
    # This allows running the flow directly
    logger.info("Starting TypeScript code indexing flow...")
    flow.run()
