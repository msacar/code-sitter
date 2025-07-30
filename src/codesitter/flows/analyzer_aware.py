"""
Analyzer-Aware Flow (Fixed with proper dataclasses)

This flow properly utilizes the language analyzer capabilities.
"""

import os
from typing import List, Any, Literal, Dict
from pathlib import Path
import dataclasses

from cocoindex import (
    FlowBuilder,
    sources,
    functions,
    op,
    flow_def,
    DataScope,
    VectorIndexDef,
    VectorSimilarityMetric,
    Vector,
    transform_flow,
    DataSlice,
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
from codesitter.analyzers.base import CodeChunk

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

# Data classes for structured data
@dataclasses.dataclass
class ChunkMetadata:
    """Metadata extracted from a code chunk."""
    is_react_component: bool = False
    has_interfaces: bool = False
    has_type_aliases: bool = False
    has_enums: bool = False
    has_async_functions: bool = False
    is_test_file: bool = False

@op.function()
def extract_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()

@op.function()
def get_language(filename: str) -> str:
    analyzer = get_analyzer(filename)
    if analyzer:
        return analyzer.language_name
    return "text"

@transform_flow()
def text_to_embedding(text: DataSlice[str]) -> DataSlice[Vector[float, Literal[384]]]:
    """Transform text to embedding using SentenceTransformer."""
    return text.transform(
        functions.SentenceTransformerEmbed(
            model="all-MiniLM-L6-v2"
        )
    )

@op.function()
def extract_chunk_metadata(chunk_text: str, filename: str) -> ChunkMetadata:
    """Extract metadata from a chunk using the appropriate analyzer."""
    analyzer = get_analyzer(filename)

    # Default metadata
    metadata = ChunkMetadata()

    if not analyzer or analyzer.language_name == "default":
        return metadata

    # Create minimal CodeChunk for metadata extraction
    chunk_obj = CodeChunk(
        text=chunk_text,
        filename=filename,
        start_line=0,
        end_line=0,
        node_type="",
        symbols=[]
    )

    try:
        custom_metadata = analyzer.extract_custom_metadata(chunk_obj)
        # Update dataclass fields with actual metadata
        if custom_metadata:
            metadata.is_react_component = custom_metadata.get("is_react_component", False)
            metadata.has_interfaces = custom_metadata.get("has_interfaces", False)
            metadata.has_type_aliases = custom_metadata.get("has_type_aliases", False)
            metadata.has_enums = custom_metadata.get("has_enums", False)
            metadata.has_async_functions = custom_metadata.get("has_async_functions", False)
            metadata.is_test_file = custom_metadata.get("is_test_file", False)
    except Exception as e:
        logger.error(f"Error extracting metadata from {filename}: {e}")

    return metadata

# Individual extractor functions for each metadata field
@op.function()
def get_is_react_component(metadata: ChunkMetadata) -> bool:
    return metadata.is_react_component

@op.function()
def get_has_interfaces(metadata: ChunkMetadata) -> bool:
    return metadata.has_interfaces

@op.function()
def get_has_type_aliases(metadata: ChunkMetadata) -> bool:
    return metadata.has_type_aliases

@op.function()
def get_has_enums(metadata: ChunkMetadata) -> bool:
    return metadata.has_enums

@op.function()
def get_has_async_functions(metadata: ChunkMetadata) -> bool:
    return metadata.has_async_functions

@op.function()
def get_is_test_file(metadata: ChunkMetadata) -> bool:
    return metadata.is_test_file

# Global counter for progress tracking
_progress_counter = {"current": 0, "total": 0}

@op.function()
def log_file_with_progress(filename: str, language: str) -> str:
    """Log file processing with progress counter."""
    _progress_counter["current"] += 1
    current = _progress_counter["current"]
    total = _progress_counter["total"]

    if total > 0:
        logger.info(f"[{current}/{total}] Processing file: {filename} [Language: {language}]")
    else:
        logger.info(f"Processing file: {filename} [Language: {language}]")

    return filename

@flow_def(name="AnalyzerAwareCodeIndex")
def analyzer_aware_flow(flow_builder: FlowBuilder, data_scope: DataScope):
    # 1. Source files
    patterns = [f"**/*{ext}" for ext in supported_exts.keys()]
    logger.info(f"Searching for files with patterns: {patterns}")

    # Pre-scan to count files (optional - for visibility)
    import glob
    from pathlib import Path
    current_dir = Path(".")
    excluded_dirs = {"node_modules", "cdk.out", "dist", "build", ".git"}

    total_files = 0
    files_by_ext = {}

    for pattern in patterns:
        for file_path in current_dir.glob(pattern):
            # Skip if in excluded directory
            if any(excluded in file_path.parts for excluded in excluded_dirs):
                continue

            total_files += 1
            ext = file_path.suffix
            files_by_ext[ext] = files_by_ext.get(ext, 0) + 1

    logger.info(f"Found {total_files} files to process")
    if files_by_ext:
        logger.info(f"Files by extension: {dict(sorted(files_by_ext.items()))}")

    # Set total for progress tracking
    global _progress_counter
    _progress_counter = {"current": 0, "total": total_files}

    data_scope["files"] = flow_builder.add_source(
        sources.LocalFile(
            path=".",
            included_patterns=patterns,
            excluded_patterns=["**/node_modules/**","**/cdk.out/**", "**/dist/**", "**/build/**", "**/.git/**"],
        )
    )

    # 2. Collector for chunks with metadata
    chunk_collector = data_scope.add_collector()

    # 3. Process each file
    with data_scope["files"].row() as file:
        file["ext"] = file["filename"].transform(extract_extension)
        file["language"] = file["filename"].transform(get_language)

        # Log file processing with progress
        file["logged_filename"] = file["filename"].transform(
            log_file_with_progress,
            language=file["language"]
        )

        # Use CocoIndex's SplitRecursively for chunking
        file["chunks"] = file["content"].transform(
            functions.SplitRecursively(),
            language=file["language"],
            chunk_size=1000,
            chunk_overlap=200,
        )

        with file["chunks"].row() as chunk:
            # Generate embedding using transform flow
            chunk["embedding"] = chunk["text"].call(text_to_embedding)

            # Extract metadata as a dataclass
            chunk["metadata"] = chunk["text"].transform(
                extract_chunk_metadata,
                filename=file["filename"]
            )

            # Extract individual metadata fields
            chunk["is_react_component"] = chunk["metadata"].transform(get_is_react_component)
            chunk["has_interfaces"] = chunk["metadata"].transform(get_has_interfaces)
            chunk["has_type_aliases"] = chunk["metadata"].transform(get_has_type_aliases)
            chunk["has_enums"] = chunk["metadata"].transform(get_has_enums)
            chunk["has_async_functions"] = chunk["metadata"].transform(get_has_async_functions)
            chunk["is_test_file"] = chunk["metadata"].transform(get_is_test_file)

            # Collect all chunk data including metadata
            chunk_collector.collect(
                filename=file["filename"],
                location=chunk["location"],
                chunk_text=chunk["text"],
                embedding=chunk["embedding"],
                language=file["language"],
                # Metadata fields
                is_react_component=chunk["is_react_component"],
                has_interfaces=chunk["has_interfaces"],
                has_type_aliases=chunk["has_type_aliases"],
                has_enums=chunk["has_enums"],
                has_async_functions=chunk["has_async_functions"],
                is_test_file=chunk["is_test_file"],
            )

    # 4. Export to storage
    if os.getenv("USE_POSTGRES", "false").lower() == "true":
        # Export chunks with embeddings and metadata
        chunk_collector.export(
            "code_chunks_with_metadata",
            Postgres(),
            primary_key_fields=["filename", "location"],
            vector_indexes=[VectorIndexDef("embedding", VectorSimilarityMetric.COSINE_SIMILARITY)],
        )

        logger.info("Data exported to PostgreSQL table: code_chunks_with_metadata")
    else:
        logger.warning("JSON export not implemented for analyzer-aware flow")
        logger.info("Set USE_POSTGRES=true to use PostgreSQL storage")

flow = analyzer_aware_flow

if __name__ == "__main__":
    logger.info("Starting analyzer-aware code indexing...")
    flow.run()
    logger.info("Code indexing complete!")
