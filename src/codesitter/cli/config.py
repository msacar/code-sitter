"""Configuration for codesitter CLI."""

import os
from pathlib import Path

# Default paths
DEFAULT_CODE_INDEX_PATH = "code_index.json"
DEFAULT_SYMBOL_INDEX_PATH = "symbol_index.json"
DEFAULT_CALL_RELATIONSHIPS_PATH = "call_relationships.json"
DEFAULT_IMPORT_RELATIONSHIPS_PATH = "import_relationships.json"

# Environment variables
USE_POSTGRES = os.getenv("USE_POSTGRES", "false").lower() == "true"
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cocoindex:cocoindex@localhost:5432/cocoindex")
COCOINDEX_DATABASE_URL = os.getenv("COCOINDEX_DATABASE_URL", "postgresql://cocoindex:cocoindex@localhost:5432/cocoindex")

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
FLEXIBLE_NO_VECTOR_FLOW_PATH = FLOW_DIR / "flexible_no_vector.py"
SIMPLE_FLOW_PATH = FLOW_DIR / "simple.py"
MINIMAL_FLEXIBLE_FLOW_PATH = FLOW_DIR / "minimal_flexible.py"
MINIMAL_FLOW_PATH = FLOW_DIR / "minimal.py"
ANALYZER_AWARE_FLOW_PATH = FLOW_DIR / "analyzer_aware.py"
ANALYZER_ADVANCED_FLOW_PATH = FLOW_DIR / "analyzer_advanced.py"
ANALYZER_SIMPLE_FLOW_PATH = FLOW_DIR / "analyzer_simple.py"
ANALYZER_DETAILED_FLOW_PATH = FLOW_DIR / "analyzer_detailed.py"
SMART_CHUNKING_FLOW_PATH = FLOW_DIR / "smart_chunking.py"

# Display settings
MAX_CODE_PREVIEW_LENGTH = 400
MAX_TOP_SYMBOLS = 10
MAX_NODE_TYPES_DISPLAY = 99
