"""
Enhanced Flow with Call-Site Extraction

This module extends the basic flow to extract function call relationships
using Tree-sitter AST queries for detailed code analysis.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Iterator

# Add the src directory to Python path for imports
current_file = Path(__file__).resolve()
src_dir = current_file.parent.parent.parent  # flows -> code_sitter -> src
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from cocoindex import FlowBuilder, sources, functions
import cocoindex.op as op
from sentence_transformers import SentenceTransformer
from tree_sitter import Language, Parser, Query
from tree_sitter_language_pack import get_language
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Tree-sitter languages using language pack
TS_LANGUAGE = get_language("typescript")
TSX_LANGUAGE = get_language("tsx")
JS_LANGUAGE = get_language("javascript")
JSX_LANGUAGE = get_language("jsx")

# Language mapping
LANGUAGE_MAP = {
    "typescript": TS_LANGUAGE,
    "tsx": TSX_LANGUAGE,
    "javascript": JS_LANGUAGE,
    "jsx": JSX_LANGUAGE,
}

# Tree-sitter query for call expressions
CALL_QUERY = """
(function_declaration
  name: (identifier) @function_name
  body: (statement_block) @body
) @function

(method_definition
  name: (property_identifier) @method_name
  body: (statement_block) @body
) @method

(arrow_function
  body: (statement_block) @body
) @arrow

(call_expression
  function: [
    (identifier) @callee
    (member_expression
      property: (property_identifier) @callee
    )
  ]
  arguments: (arguments) @args
) @call
"""

# Initialize the flow
flow = FlowBuilder("EnhancedTypeScriptCodeIndex")

# Configure source files
files = flow.add_source(
    sources.LocalFile(
        path=".",
        included_patterns=["**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx"],
        excluded_patterns=[
            "**/node_modules/**",
            "**/dist/**",
            "**/build/**",
            "**/.next/**",
            "**/coverage/**",
            "**/*.min.js",
            "**/.git/**",
            "**/venv/**",
            "**/__pycache__/**"
        ],
    )
)

def extract_extension(filename: str) -> str:
    """Extract file extension from filename."""
    return os.path.splitext(filename)[1].lower()

def get_language_from_ext(ext: str) -> str:
    """Map file extension to language identifier for Tree-sitter."""
    language_map = {
        ".ts": "typescript",
        ".tsx": "tsx",
        ".js": "javascript",
        ".jsx": "jsx",
    }
    return language_map.get(ext, "typescript")

# Add file metadata
files["ext"] = files["filename"].transform(extract_extension)
files["language"] = files["ext"].transform(get_language_from_ext)

# Configure syntax-aware chunking
files["chunks"] = files["content"].transform(
    functions.SplitRecursively(),
    language=files["language"],
    chunk_size=1000,
    chunk_overlap=200,
    respect_syntax=True,
)

@op.function()
def extract_call_relationships(
    chunk_text: str,
    filename: str,
    language: str
) -> Iterator[Dict[str, Any]]:
    """
    Extract function call relationships from code chunks using Tree-sitter.

    Yields:
        Dictionary with call relationship data
    """
    if not chunk_text or language not in LANGUAGE_MAP:
        return

    # Get the appropriate parser
    parser = Parser()
    parser.set_language(LANGUAGE_MAP[language])

    try:
        # Parse the code
        tree = parser.parse(bytes(chunk_text, "utf8"))

        # Create and run the query
        query = Query(LANGUAGE_MAP[language], CALL_QUERY)
        captures = query.captures(tree.root_node)

        # Track current context
        current_function = None
        current_method = None

        # Process captures
        for name, node in captures:
            if name == "function_name":
                current_function = node.text.decode("utf8")
                current_method = None
            elif name == "method_name":
                current_method = node.text.decode("utf8")
                current_function = None
            elif name == "call":
                # Extract call details
                callee_node = None
                args_node = None

                # Find callee and args in children
                for child_name, child_node in captures:
                    if child_name == "callee" and child_node.start_byte >= node.start_byte and child_node.end_byte <= node.end_byte:
                        callee_node = child_node
                    elif child_name == "args" and child_node.start_byte >= node.start_byte and child_node.end_byte <= node.end_byte:
                        args_node = child_node

                if callee_node:
                    callee = callee_node.text.decode("utf8")

                    # Extract arguments
                    args = []
                    if args_node:
                        args_text = args_node.text.decode("utf8")
                        # Simple argument extraction (can be enhanced)
                        args = [arg.strip() for arg in args_text[1:-1].split(",") if arg.strip()]

                    yield {
                        "filename": filename,
                        "caller": current_function or current_method or "anonymous",
                        "callee": callee,
                        "arguments": args,
                        "line": node.start_point[0] + 1,
                        "column": node.start_point[1] + 1,
                        "context": chunk_text[max(0, node.start_byte-50):min(len(chunk_text), node.end_byte+50)]
                    }

    except Exception as e:
        logger.error(f"Error parsing {filename}: {e}")

# Extract call relationships from chunks
@flow.register_op
def process_chunk_for_calls(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Process each chunk to extract call relationships."""
    chunks = row.get("chunks", [])
    filename = row.get("filename", "")
    language = row.get("language", "")

    all_calls = []

    for chunk in chunks:
        if isinstance(chunk, dict) and "text" in chunk:
            chunk_text = chunk["text"]
        else:
            chunk_text = str(chunk)

        # Extract calls from this chunk
        calls = list(extract_call_relationships(chunk_text, filename, language))
        all_calls.extend(calls)

    return all_calls

files["call_relationships"] = files.transform(process_chunk_for_calls)

# Also process chunks for embeddings as before
@flow.register_op
def extract_chunk_metadata(chunk: Dict[str, Any], filename: str) -> Dict[str, Any]:
    """Extract metadata from code chunks including symbols and context."""
    return {
        "text": chunk.get("text", ""),
        "filename": filename,
        "chunk_index": chunk.get("index", 0),
        "start_line": chunk.get("start_line", 0),
        "end_line": chunk.get("end_line", 0),
        "node_type": chunk.get("node_type", "unknown"),
        "symbols": chunk.get("symbols", []),
    }

files["chunk_metadata"] = files.apply(
    lambda row: [
        extract_chunk_metadata(chunk, row["filename"])
        for chunk in row.get("chunks", [])
    ]
)

# Flatten chunks for embedding processing
chunks_flow = files.explode("chunk_metadata")
chunks_flow["chunk_data"] = chunks_flow["chunk_metadata"]

# Initialize embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")

@flow.register_op
def generate_code_embedding(chunk_text: str) -> List[float]:
    """Generate vector embedding for code chunk."""
    if not chunk_text:
        return []
    cleaned_text = chunk_text.strip()
    embedding = embedder.encode(cleaned_text)
    return embedding.tolist()

# Add embeddings
chunks_flow["embedding"] = chunks_flow["chunk_data"].apply(
    lambda chunk: generate_code_embedding(chunk.get("text", ""))
)

# Configure storage based on environment
if os.getenv("USE_POSTGRES", "false").lower() == "true":
    # Store code chunks with embeddings
    chunks_flow.add_sink(
        functions.sinks.Postgres(
            connection_string=os.getenv(
                "DATABASE_URL",
                "postgresql://localhost:5432/code_index"
            ),
            table_name="typescript_code_index",
            columns={
                "filename": "text",
                "chunk_index": "integer",
                "chunk_text": "text",
                "start_line": "integer",
                "end_line": "integer",
                "node_type": "text",
                "symbols": "text[]",
                "embedding": "vector(384)",
            },
            vector_column="embedding",
            on_conflict="update",
        )
    )

    # Store call relationships separately
    calls_flow = files.explode("call_relationships")
    calls_flow.add_sink(
        functions.sinks.Postgres(
            connection_string=os.getenv(
                "DATABASE_URL",
                "postgresql://localhost:5432/code_index"
            ),
            table_name="call_relationships",
            columns={
                "filename": "text",
                "caller": "text",
                "callee": "text",
                "arguments": "text[]",
                "line": "integer",
                "column": "integer",
                "context": "text",
            },
            on_conflict="update",
        )
    )
else:
    # JSON file sinks for development
    chunks_flow.add_sink(
        functions.sinks.JsonFile(
            path="./code_index.json",
            mode="overwrite",
        )
    )

    # Store call relationships
    calls_flow = files.explode("call_relationships")
    calls_flow.add_sink(
        functions.sinks.JsonFile(
            path="./call_relationships.json",
            mode="overwrite",
        )
    )

# Build symbol index
@flow.register_op
def build_symbol_index(rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Build an index of symbols to their locations."""
    symbol_index = {}

    for row in rows:
        chunk_data = row.get("chunk_data", {})
        symbols = chunk_data.get("symbols", [])

        for symbol in symbols:
            if symbol not in symbol_index:
                symbol_index[symbol] = []

            symbol_index[symbol].append({
                "filename": chunk_data.get("filename"),
                "line_start": chunk_data.get("start_line"),
                "line_end": chunk_data.get("end_line"),
                "chunk_text": chunk_data.get("text", "")[:100] + "...",
            })

    return symbol_index

# Export symbol index
symbol_index = chunks_flow.collect().transform(build_symbol_index)
symbol_index.add_sink(
    functions.sinks.JsonFile(
        path="./symbol_index.json",
        mode="overwrite",
    )
)

if __name__ == "__main__":
    logger.info("Starting enhanced TypeScript code indexing with call extraction...")
    flow.run()
