"""
Simplified Analyzer-Aware Flow (Corrected)

Following CocoIndex code_embedding example exactly.
"""

import os
from typing import Literal
from pathlib import Path

import cocoindex
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

@cocoindex.op.function()
def extract_extension(filename: str) -> str:
    """Extract file extension."""
    return os.path.splitext(filename)[1].lower()

@cocoindex.op.function()
def get_language(filename: str) -> str:
    """Get language name for a file."""
    analyzer = get_analyzer(filename)
    if analyzer:
        return analyzer.language_name
    # Fallback mapping
    ext = extract_extension(filename)
    return {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".jsx": "javascript",
    }.get(ext, "text")

@cocoindex.transform_flow()
def text_to_embedding(
    text: cocoindex.DataSlice[str],
) -> cocoindex.DataSlice[cocoindex.Vector[float, Literal[384]]]:
    """Embed text using SentenceTransformer."""
    return text.transform(
        cocoindex.functions.SentenceTransformerEmbed(
            model="all-MiniLM-L6-v2"
        )
    )

# Individual metadata extraction functions
@cocoindex.op.function()
def is_react_component(text: str, filename: str) -> bool:
    """Check if chunk contains a React component."""
    analyzer = get_analyzer(filename)
    if not analyzer or analyzer.language_name == "default":
        return False

    chunk_obj = CodeChunk(
        text=text,
        filename=filename,
        start_line=0,
        end_line=0,
        node_type="",
        symbols=[]
    )

    try:
        metadata = analyzer.extract_custom_metadata(chunk_obj)
        return metadata.get("is_react_component", False)
    except:
        return False

@cocoindex.op.function()
def has_interfaces(text: str, filename: str) -> bool:
    """Check if chunk has TypeScript interfaces."""
    analyzer = get_analyzer(filename)
    if not analyzer or analyzer.language_name == "default":
        return False

    chunk_obj = CodeChunk(
        text=text,
        filename=filename,
        start_line=0,
        end_line=0,
        node_type="",
        symbols=[]
    )

    try:
        metadata = analyzer.extract_custom_metadata(chunk_obj)
        return metadata.get("has_interfaces", False)
    except:
        return False

@cocoindex.op.function()
def has_type_aliases(text: str, filename: str) -> bool:
    """Check if chunk has TypeScript type aliases."""
    analyzer = get_analyzer(filename)
    if not analyzer or analyzer.language_name == "default":
        return False

    chunk_obj = CodeChunk(
        text=text,
        filename=filename,
        start_line=0,
        end_line=0,
        node_type="",
        symbols=[]
    )

    try:
        metadata = analyzer.extract_custom_metadata(chunk_obj)
        return metadata.get("has_type_aliases", False)
    except:
        return False

@cocoindex.op.function()
def has_async_functions(text: str, filename: str) -> bool:
    """Check if chunk has async functions."""
    analyzer = get_analyzer(filename)
    if not analyzer or analyzer.language_name == "default":
        return False

    chunk_obj = CodeChunk(
        text=text,
        filename=filename,
        start_line=0,
        end_line=0,
        node_type="",
        symbols=[]
    )

    try:
        metadata = analyzer.extract_custom_metadata(chunk_obj)
        return metadata.get("has_async_functions", False)
    except:
        return False

@cocoindex.op.function()
def is_test_file(text: str, filename: str) -> bool:
    """Check if this is a test file."""
    analyzer = get_analyzer(filename)
    if not analyzer or analyzer.language_name == "default":
        return False

    chunk_obj = CodeChunk(
        text=text,
        filename=filename,
        start_line=0,
        end_line=0,
        node_type="",
        symbols=[]
    )

    try:
        metadata = analyzer.extract_custom_metadata(chunk_obj)
        return metadata.get("is_test_file", False)
    except:
        return False

@cocoindex.flow_def(name="CodeAnalyzerFlow")
def code_analyzer_flow(
    flow_builder: cocoindex.FlowBuilder,
    data_scope: cocoindex.DataScope
) -> None:
    """Flow that analyzes code with language analyzers."""

    # Add source
    patterns = [f"**/*{ext}" for ext in supported_exts.keys()]
    data_scope["files"] = flow_builder.add_source(
        cocoindex.sources.LocalFile(
            path=".",
            included_patterns=patterns,
            excluded_patterns=["**/node_modules/**", "**/dist/**", "**/build/**", "**/.git/**"],
        )
    )

    # Create collector
    code_embeddings = data_scope.add_collector()

    # Process files
    with data_scope["files"].row() as file:
        file["extension"] = file["filename"].transform(extract_extension)
        file["language"] = file["filename"].transform(get_language)

        # Chunk the file
        file["chunks"] = file["content"].transform(
            cocoindex.functions.SplitRecursively(),
            language=file["language"],
            chunk_size=1000,
            chunk_overlap=200,
        )

        # Process each chunk
        with file["chunks"].row() as chunk:
            # Get embedding
            chunk["embedding"] = chunk["text"].call(text_to_embedding)

            # Analyze metadata
            chunk["is_react"] = chunk["text"].transform(
                is_react_component,
                filename=file["filename"]
            )
            chunk["has_interfaces_flag"] = chunk["text"].transform(
                has_interfaces,
                filename=file["filename"]
            )
            chunk["has_types"] = chunk["text"].transform(
                has_type_aliases,
                filename=file["filename"]
            )
            chunk["has_async"] = chunk["text"].transform(
                has_async_functions,
                filename=file["filename"]
            )
            chunk["is_test"] = chunk["text"].transform(
                is_test_file,
                filename=file["filename"]
            )

            # Collect data
            code_embeddings.collect(
                filename=file["filename"],
                location=chunk["location"],
                code=chunk["text"],
                embedding=chunk["embedding"],
                language=file["language"],
                # Metadata fields
                is_react_component=chunk["is_react"],
                has_interfaces=chunk["has_interfaces_flag"],
                has_type_aliases=chunk["has_types"],
                has_async_functions=chunk["has_async"],
                is_test_file=chunk["is_test"],
            )

    # Export to PostgreSQL
    code_embeddings.export(
        "code_analysis",
        cocoindex.targets.Postgres(),
        primary_key_fields=["filename", "location"],
        vector_indexes=[
            cocoindex.VectorIndexDef(
                field_name="embedding",
                metric=cocoindex.VectorSimilarityMetric.COSINE_SIMILARITY,
            )
        ],
    )

# Use this flow
flow = code_analyzer_flow

if __name__ == "__main__":
    import cocoindex
    from dotenv import load_dotenv

    load_dotenv()
    cocoindex.init()

    # Update the flow
    stats = flow.update()
    print("Updated index:", stats)
