"""
Simple Multi-Language Flow for Code Indexing

This is a simplified version that works reliably with CocoIndex.
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

# Custom JSON file target
from cocoindex.targets import TargetSpec
from cocoindex.op import target_connector

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
        if current and current.mode == "overwrite":
            try:
                os.remove(current.path)
            except FileNotFoundError:
                pass

    @staticmethod
    def mutate(*all_mutations: tuple[JsonFileTarget, dict]) -> None:
        # Gather every row's value dict, then dump as one JSON array
        import json
        all_rows = []
        for spec, value_dict in all_mutations:
            all_rows.append(value_dict)
        
        # Write to the file
        with open(spec.path, 'w') as f:
            json.dump(all_rows, f, indent=2)

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

@flow_def(name="SimpleCodeIndex")
def simple_code_index_flow(flow_builder: FlowBuilder, data_scope: DataScope):
    # 1. Source files
    files = flow_builder.add_source(
        sources.LocalFile(
            path=".",
            included_patterns=[
                # JavaScript/TypeScript
                "**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx", "**/*.mjs", "**/*.cjs",
                # Python
                "**/*.py", "**/*.pyw",
                # Java
                "**/*.java",
                # Go
                "**/*.go",
                # Rust
                "**/*.rs",
                # Ruby
                "**/*.rb",
                # PHP
                "**/*.php",
                # C/C++
                "**/*.c", "**/*.h", "**/*.cpp", "**/*.cc", "**/*.hpp", "**/*.cxx",
                # C#
                "**/*.cs",
                # Swift
                "**/*.swift",
                # Kotlin
                "**/*.kt", "**/*.kts",
                # Shell
                "**/*.sh", "**/*.bash", "**/*.zsh",
                # Others
                "**/*.scala", "**/*.lua", "**/*.r", "**/*.R",
                # Config files
                "**/*.json", "**/*.yaml", "**/*.yml", "**/*.toml", "**/*.xml",
                # Web files
                "**/*.html", "**/*.htm", "**/*.css", "**/*.scss", "**/*.sass",
            ],
            excluded_patterns=[
                "**/node_modules/**",
                "**/.git/**",
                "**/venv/**",
                "**/.venv/**",
                "**/dist/**",
                "**/build/**",
                "**/target/**",
                "**/vendor/**",
                "**/__pycache__/**",
                "**/.next/**",
                "**/coverage/**",
                "**/*.min.js",
                "**/.bundle/**",
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

    # 4. Export to JSON file
    collector.export(
        "code_index",
        JsonFileTarget(path="./code_index.json", mode="overwrite"),
        primary_key_fields=["filename", "location"],
    )

flow = simple_code_index_flow

if __name__ == "__main__":
    print("Starting simple code indexing...")
    flow.run()
