"""
Basic CocoIndex Flow for Code Indexing

This module defines a minimal flow for indexing codebases.
"""

import os
from cocoindex import FlowBuilder, sources, functions

# Initialize the flow
flow = FlowBuilder("BasicCodeIndex")

# Configure source files
flow.add_source(
    sources.LocalFile(
        path=".",  # Current directory
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

# Simple JSON sink
flow.add_sink(
    functions.sinks.JsonFile(
        path="./code_index.json",
        mode="overwrite",
    )
)

# The flow is ready to be used by CocoIndex CLI
