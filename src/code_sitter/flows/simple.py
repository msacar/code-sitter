"""
Simple Multi-Language Flow for Code Indexing

This is a simplified version that works reliably with CocoIndex.
"""

import os
from cocoindex import FlowBuilder, sources, functions

# Initialize the flow
flow = FlowBuilder("MultiLanguageIndex")

# Configure source files - support multiple languages
flow.add_source(
    sources.LocalFile(
        path=".",  # Current directory
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

# Simple JSON sink for all data
flow.add_sink(
    functions.sinks.JsonFile(
        path="./code_index.json",
        mode="overwrite",
    )
)

# The flow is ready to be used by CocoIndex CLI
