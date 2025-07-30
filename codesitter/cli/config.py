"""Configuration for Code-Sitter CLI."""

import os
from pathlib import Path

# Default paths
DEFAULT_CODE_INDEX_PATH = "code_index.json"
DEFAULT_SYMBOL_INDEX_PATH = "symbol_index.json"
DEFAULT_CALL_RELATIONSHIPS_PATH = "call_relationships.json"
DEFAULT_IMPORT_RELATIONSHIPS_PATH = "import_relationships.json"

# Environment variables
USE_POSTGRES = os.getenv("USE_POSTGRES", "false").lower() == "true"
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/code_index")

# Search defaults
DEFAULT_SEARCH_LIMIT = 5
DEFAULT_SIMILARITY_THRESHOLD = 0.5

# Indexing defaults
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200

# Flow file locations
FLOW_DIR = Path(__file__).parent.parent / "flows"
BASIC_FLOW_PATH = FLOW_DIR / "basic.py"
ENHANCED_FLOW_PATH = FLOW_DIR / "enhanced.py"
FLEXIBLE_FLOW_PATH = FLOW_DIR / "flexible.py"
SIMPLE_FLOW_PATH = FLOW_DIR / "simple.py"

# Display settings
MAX_CODE_PREVIEW_LENGTH = 200
MAX_TOP_SYMBOLS = 5
MAX_NODE_TYPES_DISPLAY = 10
