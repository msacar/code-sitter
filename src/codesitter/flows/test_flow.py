"""
Test flow for debugging - uses flow_def decorator pattern
"""

import os
from cocoindex import FlowBuilder, sources, functions, op, flow_def, DataScope

@op.function()
def extract_extension(filename: str) -> str:
    """Extract file extension from filename."""
    return os.path.splitext(filename)[1].lower()

@flow_def(name="TestFlow")
def test_flow(flow_builder: FlowBuilder, data_scope: DataScope):
    """Test flow for debugging."""

    # Configure source files - just TypeScript for testing
    files = data_scope["files"] = flow_builder.add_source(
        sources.LocalFile(
            path=".",
            included_patterns=["**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx"],
            excluded_patterns=["**/node_modules/**", "**/.git/**"],
        )
    )

    # Add file metadata
    files["ext"] = files["filename"].transform(extract_extension)

    # Simple JSON sink
    files.export(
        "test_output",
        functions.storages.JsonFile(
            path="./test_output.json",
            mode="overwrite",
        )
    )

# Make flow available at module level
flow = test_flow
