"""
Detailed Analyzer Flow - Captures function signatures, types, and relationships
Inspired by Doctave/dossier's approach
"""

import os
import json
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
from codesitter.analyzers.base import CodeChunk, CallRelationship

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize analyzer registry
logger.info("Initializing language analyzers...")
register_defaults()
auto_discover_analyzers()

# Data classes for structured data
@dataclasses.dataclass
class FunctionSignature:
    """Detailed function signature information."""
    name: str
    parameters: List[Dict[str, str]]  # [{"name": "param1", "type": "string"}]
    return_type: str
    is_async: bool = False
    is_export: bool = False
    docstring: str = ""

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
def extract_function_signatures(chunk_text: str, filename: str) -> str:
    """Extract detailed function signatures from code."""
    # For now, return empty JSON - this would be enhanced with actual parsing
    # In a real implementation, this would use Tree-sitter to extract:
    # - Function names
    # - Parameter names and types
    # - Return types
    # - JSDoc comments
    return json.dumps([])

@op.function()
def extract_call_relationships_json(chunk_text: str, filename: str) -> str:
    """Extract call relationships and return as JSON string."""
    analyzer = get_analyzer(filename)

    if not analyzer or analyzer.language_name == "default":
        return json.dumps([])

    # Create CodeChunk for analysis
    chunk_obj = CodeChunk(
        text=chunk_text,
        filename=filename,
        start_line=0,
        end_line=0,
        node_type="",
        symbols=[]
    )

    try:
        calls = []
        for call in analyzer.extract_call_relationships(chunk_obj):
            calls.append({
                "caller": call.caller,
                "callee": call.callee,
                "arguments": call.arguments,
                "line": call.line,
                "column": call.column
            })
        return json.dumps(calls)
    except Exception as e:
        logger.error(f"Error extracting calls from {filename}: {e}")
        return json.dumps([])

@flow_def(name="DetailedCodeAnalysis")
def detailed_analysis_flow(flow_builder: FlowBuilder, data_scope: DataScope):
    # 1. Source files
    registry = get_registry()
    supported_exts = registry.list_supported_extensions()
    patterns = [f"**/*{ext}" for ext in supported_exts.keys()]

    data_scope["files"] = flow_builder.add_source(
        sources.LocalFile(
            path=".",
            included_patterns=patterns,
            excluded_patterns=["**/node_modules/**", "**/cdk.out/**", "**/dist/**", "**/build/**", "**/.git/**"],
        )
    )

    # 2. Collectors for different data types
    chunk_collector = data_scope.add_collector()
    symbol_collector = data_scope.add_collector()
    call_collector = data_scope.add_collector()

    # 3. Process each file
    with data_scope["files"].row() as file:
        file["ext"] = file["filename"].transform(extract_extension)
        file["language"] = file["filename"].transform(get_language)

        # Chunk the file
        file["chunks"] = file["content"].transform(
            functions.SplitRecursively(),
            language=file["language"],
            chunk_size=1000,
            chunk_overlap=200,
        )

        with file["chunks"].row() as chunk:
            # Generate embedding
            chunk["embedding"] = chunk["text"].call(text_to_embedding)

            # Extract function signatures (would be implemented with Tree-sitter)
            chunk["function_signatures"] = chunk["text"].transform(
                extract_function_signatures,
                filename=file["filename"]
            )

            # Extract call relationships
            chunk["call_relationships"] = chunk["text"].transform(
                extract_call_relationships_json,
                filename=file["filename"]
            )

            # Collect chunk data
            chunk_collector.collect(
                filename=file["filename"],
                location=chunk["location"],
                chunk_text=chunk["text"],
                embedding=chunk["embedding"],
                language=file["language"],
                function_signatures=chunk["function_signatures"],
                call_relationships=chunk["call_relationships"]
            )

    # 4. Export to storage
    if os.getenv("USE_POSTGRES", "false").lower() == "true":
        # Main chunks table with detailed analysis
        chunk_collector.export(
            "code_chunks_detailed",
            Postgres(),
            primary_key_fields=["filename", "location"],
            vector_indexes=[VectorIndexDef("embedding", VectorSimilarityMetric.COSINE_SIMILARITY)],
        )

        logger.info("Detailed analysis exported to PostgreSQL")
    else:
        logger.warning("JSON export not implemented for detailed flow")
        logger.info("Set USE_POSTGRES=true to use PostgreSQL storage")

flow = detailed_analysis_flow

if __name__ == "__main__":
    logger.info("Starting detailed code analysis...")
    flow.run()
    logger.info("Analysis complete!")
