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
    VectorIndexDef,
    VectorSimilarityMetric,
)
from cocoindex.targets import Postgres
from cocoindex.op import TargetSpec, target_connector

from sentence_transformers import SentenceTransformer
import logging

from codesitter.analyzers import (
    get_registry,
    auto_discover_analyzers,
    register_defaults,
    get_analyzer,
)

# ————————————————————————————————————————————————————————————————————————————————
# Custom JSON‑file target (since there's no built‑in JsonFile in cocoindex.targets)
# ————————————————————————————————————————————————————————————————————————————————

class JsonFileTarget(TargetSpec):
    """Write all collected rows out as a single JSON array."""
    path: str
    mode: str = "overwrite"  # "overwrite" (default) or "append"

@target_connector(spec_cls=JsonFileTarget)
class JsonFileTargetConnector:
    @staticmethod
    def get_persistent_key(spec: JsonFileTarget, target_name: str) -> str:
        # Use filepath as the unique key
        return spec.path

    @staticmethod
    def apply_setup_change(key: str, previous: JsonFileTarget | None, current: JsonFileTarget | None) -> None:
        # If we're overwriting, remove any existing file before writing
        if current is not None and current.mode == "overwrite":
            try:
                os.remove(key)
            except FileNotFoundError:
                pass

    @staticmethod
    def mutate(*all_mutations: tuple[JsonFileTarget, dict[Any, Any]]) -> None:
        # Gather every row’s value dict, then dump as one JSON array
        rows: List[Any] = []
        for spec, batch in all_mutations:
            rows.extend(batch.values())
        open_mode = "w" if spec.mode == "overwrite" else "a"
        with open(spec.path, open_mode) as f:
            json.dump(rows, f)

# ————————————————————————————————————————————————————————————————————————————————
# End custom target
# ————————————————————————————————————————————————————————————————————————————————

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

@flow_def(name="FlexibleCodeIndex")
def flexible_code_index_flow(flow_builder: FlowBuilder, data_scope: DataScope):
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

    # 2. Collector for vector shards
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

    # 4. Export to Postgres or JSON file
    if os.getenv("USE_POSTGRES", "false").lower() == "true":
        collector.export(
            "code_chunks",
            Postgres(),
            primary_key_fields=["filename", "location"],
            vector_indexes=[VectorIndexDef("embedding", VectorSimilarityMetric.COSINE_SIMILARITY)],
        )
    else:
        collector.export(
            "code_index",
            JsonFileTarget(path="./code_index.json", mode="overwrite"),
            primary_key_fields=["filename", "location"],
        )

flow = flexible_code_index_flow

if __name__ == "__main__":
    logger.info("Starting flexible code indexing…")
    flow.run()
