"""
Minimal flexible flow for debugging
"""

import os
import logging
from pathlib import Path
from typing import List

from cocoindex import FlowBuilder, sources, functions, op, flow_def, DataScope
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")

@op.function()
def extract_extension(filename: str) -> str:
    """Extract file extension from filename."""
    return os.path.splitext(filename)[1].lower()

@op.function()
def get_language_for_cocoindex(filename: str) -> str:
    """Map filename to language for CocoIndex chunking."""
    ext = extract_extension(filename)

    # Simple mapping - no dependency on analyzers
    language_map = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".cs": "csharp",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".html": "html",
        ".css": "css",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".xml": "xml",
        ".sh": "bash",
    }

    lang = language_map.get(ext, "text")
    logger.info(f"File {filename} -> extension {ext} -> language {lang}")
    return lang

@op.function()
def generate_code_embedding(chunk_text: str) -> List[float]:
    """Generate vector embedding for code chunk."""
    if not chunk_text:
        return []
    cleaned_text = chunk_text.strip()
    embedding = embedder.encode(cleaned_text)
    return embedding.tolist()

@flow_def(name="MinimalFlexibleFlow")
def minimal_flexible_flow(flow_builder: FlowBuilder, data_scope: DataScope):
    """Minimal flexible flow for debugging."""

    logger.info("Starting minimal flexible flow...")

    # Configure source files - focus on TypeScript/JavaScript
    files = data_scope["files"] = flow_builder.add_source(
        sources.LocalFile(
            path=".",
            included_patterns=[
                "**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx",
                "**/*.py", "**/*.java", "**/*.go", "**/*.rs"
            ],
            excluded_patterns=[
                "**/node_modules/**",
                "**/.git/**",
                "**/venv/**",
                "**/.venv/**",
                "**/dist/**",
                "**/build/**"
            ],
        )
    )

    logger.info("Source files configured")

    # Add file metadata
    files["ext"] = files["filename"].transform(extract_extension)
    files["language"] = files["filename"].transform(get_language_for_cocoindex)

    logger.info("File metadata added")

    # Configure syntax-aware chunking
    files["chunks"] = files["content"].transform(
        functions.SplitRecursively(),
        language=files["language"],
        chunk_size=1000,
        chunk_overlap=200,
        respect_syntax=True,
    )

    logger.info("Chunking configured")

    # Add collectors
    code_embeddings = data_scope.add_collector()

    # Process chunks for embedding
    with files.row() as file:
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

    logger.info("Embedding processing configured")

    # JSON file storage (simpler for debugging)
    code_embeddings.export(
        "minimal_code_index",
        functions.storages.JsonFile(
            path="./minimal_code_index.json",
            mode="overwrite",
        ),
        primary_key_fields=["filename", "location"]
    )

    logger.info("Storage configured")

# Make flow available at module level
flow = minimal_flexible_flow

if __name__ == "__main__":
    logger.info("Running minimal flexible flow...")
    flow.run()
