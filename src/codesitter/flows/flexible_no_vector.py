import os
import sys
import json
from pathlib import Path
from typing import List, Any

from cocoindex import (
    FlowBuilder,
    sources,
    functions,
    op,
    flow_def,
    DataScope,
)
from cocoindex.targets import Postgres

from sentence_transformers import SentenceTransformer
import logging

from codesitter.analyzers import (
    get_registry,
    auto_discover_analyzers,
    register_defaults,
    get_analyzer,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize analyzer registry
logger.info("Initializing language analyzers...")
register_defaults()
auto_discover_analyzers()

# Log supported extensions
registry = get_registry()
supported_exts = registry.list_supported_extensions()
logger.info(f"Registered language support for: {list(supported_exts.keys())}")

# Embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")

@op.function()
def extract_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()

@op.function()
def get_language(filename: str) -> str:
    analyzer = get_analyzer(filename)
    if analyzer:
        return analyzer.language_name
    ext = extract_extension(filename)
    return {
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
    }.get(ext, "text")

@op.function()
def embed(text: str) -> List[float]:
    if not text:
        return []
    return embedder.encode(text.strip()).tolist()

@flow_def(name="FlexibleCodeIndexNoVector")
def flexible_code_index_no_vector_flow(flow_builder: FlowBuilder, data_scope: DataScope):
    # 1. Source files
    patterns = [f"**/*{ext}" for ext in supported_exts.keys()]
    files = flow_builder.add_source(
        sources.LocalFile(
            path=".",
            included_patterns=patterns,
            excluded_patterns=["**/node_modules/**", "**/dist/**", "**/build/**", "**/.git/**"],
        )
    )
    data_scope["files"] = files

    # 2. Collector for chunks
    collector = data_scope.add_collector()

    # 3. Process each file → chunks → embeddings
    with files.row() as file:
        file["ext"] = file["filename"].transform(extract_extension)
        file["language"] = file["filename"].transform(get_language)

        file["chunks"] = file["content"].transform(
            functions.SplitRecursively(),
            language=file["language"],
            chunk_size=1000,
            chunk_overlap=200,
        )

        with file["chunks"].row() as chunk:
            chunk["embedding"] = chunk["text"].transform(embed)
            collector.collect(
                filename=file["filename"],
                location=chunk["location"],
                chunk_text=chunk["text"],
                embedding=chunk["embedding"],
                language=file["language"],
            )

    # 4. Export to Postgres WITHOUT vector indexes
    collector.export(
        "code_chunks",
        Postgres(),
        primary_key_fields=["filename", "location"],
        # No vector_indexes parameter - just store embeddings as JSONB
    )

flow = flexible_code_index_no_vector_flow

if __name__ == "__main__":
    logger.info("Starting flexible code indexing without vector indexes...")
    flow.run()
