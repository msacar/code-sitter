"""
Basic Flow for Code Indexing

A very simple flow that just processes files and outputs to PostgreSQL.
"""

import os
from cocoindex import (
    FlowBuilder,
    sources,
    functions,
    op,
    flow_def,
    DataScope,
)
from cocoindex.targets import Postgres

@op.function()
def extract_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()

@op.function()
def get_language(filename: str) -> str:
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
        ".html": "html",
        ".css": "css",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".xml": "xml",
        ".sh": "bash",
        ".bash": "bash",
    }.get(ext, "text")

@flow_def(name="BasicCodeIndex")
def basic_code_index_flow(flow_builder: FlowBuilder, data_scope: DataScope):
    # 1. Source files - just a few common types
    files = flow_builder.add_source(
        sources.LocalFile(
            path=".",
            included_patterns=[
                "**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx",
                "**/*.py", "**/*.json", "**/*.html", "**/*.css",
            ],
            excluded_patterns=[
                "**/node_modules/**", "**/.git/**", "**/dist/**", 
                "**/build/**", "**/__pycache__/**",
            ],
        )
    )
    data_scope["files"] = files

    # 2. Collector for chunks
    collector = data_scope.add_collector()

    # 3. Process each file → chunks
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
            collector.collect(
                filename=file["filename"],
                location=chunk["location"],
                chunk_text=chunk["text"],
                language=file["language"],
                extension=file["ext"],
            )

    # 4. Export to PostgreSQL
    collector.export(
        "code_chunks",
        Postgres(),
        primary_key_fields=["filename", "location"],
    )

flow = basic_code_index_flow

if __name__ == "__main__":
    print("Starting basic code indexing...")
    flow.run()
