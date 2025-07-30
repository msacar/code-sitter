# CocoIndex Integration: Lessons Learned and Complete Implementation Guide

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [What I Missed - Critical Mistakes](#what-i-missed---critical-mistakes)
3. [Lessons Learned](#lessons-learned)
4. [How CocoIndex Actually Works](#how-cocoindex-actually-works)
5. [Our Implementation](#our-implementation)
6. [Correct Usage Patterns](#correct-usage-patterns)
7. [Troubleshooting Guide](#troubleshooting-guide)
8. [API Usage and Examples](#api-usage-and-examples)
9. [Future Improvements](#future-improvements)

## Executive Summary

This document captures the complete journey of integrating CocoIndex with a Tree-sitter-based TypeScript analyzer. We encountered several implementation challenges that revealed important patterns about how CocoIndex should be used. The final working solution demonstrates proper integration of custom language analyzers with CocoIndex's incremental indexing system.

## What I Missed - Critical Mistakes

### 1. **Non-existent `op.apply()` Method**
```python
# ❌ WRONG - This method doesn't exist
chunk["analysis"] = op.apply(analyze_chunk, chunk["text"], file["filename"])

# ✅ CORRECT - Use transform with proper function decoration
@op.function()
def analyze_chunk(text: str, filename: str) -> ChunkMetadata:
    # analysis logic
    return metadata

chunk["analysis"] = chunk["text"].transform(analyze_chunk, filename=file["filename"])
```

**Why I made this mistake**: I confused CocoIndex's API with other frameworks and didn't carefully check the documentation for available methods.

### 2. **Incorrect Data Types in KTables**
```python
# ❌ WRONG - Returning dict instead of dataclass
@op.function()
def extract_metadata(text: str) -> Dict[str, bool]:
    return {"is_react_component": True}  # CocoIndex expects structured types

# ✅ CORRECT - Use dataclasses for structured data
@dataclasses.dataclass
class ChunkMetadata:
    is_react_component: bool = False

@op.function()
def extract_metadata(text: str) -> ChunkMetadata:
    return ChunkMetadata(is_react_component=True)
```

**Why this matters**: CocoIndex needs to know the exact schema at flow definition time for type safety and optimization.

### 3. **Lambda Functions in Transforms**
```python
# ❌ WRONG - Can't use lambda directly
chunk["start_line"] = chunk["location"].transform(lambda loc: loc[0])

# ✅ CORRECT - Must use decorated functions
@op.function()
def get_start_line(location: List[int]) -> int:
    return location[0] if location else 0

chunk["start_line"] = chunk["location"].transform(get_start_line)
```

**Lesson**: Every transformation in CocoIndex must be a properly decorated function for serialization and distributed execution.

### 4. **Complex Nested Data Structures**
```python
# ❌ WRONG - Overly complex intermediate structures
result = {
    "metadata": {...},
    "relationships": {
        "calls": [...],
        "imports": [...]
    }
}

# ✅ CORRECT - Flatten data for simpler processing
@dataclasses.dataclass
class ChunkAnalysis:
    has_calls: bool
    call_count: int
    calls_json: str  # Serialize complex data as JSON string
```

### 5. **Working Directory Issues**
```python
# ❌ WRONG - Running from wrong directory
# codesitter CLI was running: cocoindex update --setup /path/to/flow.py
# From: /Users/mustafaacar/codesitter (wrong!)

# ✅ CORRECT - Must run from project directory
os.chdir("/Users/mustafaacar/retter/shortlink")
subprocess.run(["cocoindex", "update", flow_path])
```

**Critical insight**: CocoIndex needs to run from the directory containing the files to be indexed.

### 6. **Environment Variable Loading**
```python
# ❌ WRONG - Assuming environment is set
subprocess.run(["cocoindex", "setup", flow_path])

# ✅ CORRECT - Explicitly load environment
from dotenv import load_dotenv
load_dotenv("/Users/mustafaacar/codesitter/.env")
# or
os.environ['COCOINDEX_DATABASE_URL'] = 'postgresql://...'
```

## Lessons Learned

### 1. **Follow Examples Exactly**
CocoIndex has specific patterns that must be followed precisely:
- Study `examples/code_embedding/main.py` as the canonical reference
- Don't invent methods or assume API similarities with other frameworks
- When in doubt, check what decorators and methods actually exist

### 2. **Keep Transformations Simple**
- Each transformation should do one thing
- Avoid complex nested data structures
- Use multiple simple functions rather than one complex function
- Serialize complex data as JSON strings if needed

### 3. **Understand the Data Model**
```
DataScope → KTable → Row → Field → Transform → Collect → Export
```
- DataScope: Top-level container for all data
- KTable: Key-value table with schema
- Row context: Iterate over table rows
- Field transforms: Apply functions to create new fields
- Collect: Gather processed data
- Export: Save to storage (PostgreSQL, JSON, etc.)

### 4. **Proper Function Decoration**
```python
# For simple transformations
@op.function()
def my_transform(input: str) -> str:
    return input.upper()

# For reusable transformation flows
@transform_flow()
def text_to_embedding(text: DataSlice[str]) -> DataSlice[Vector[float, Literal[384]]]:
    return text.transform(functions.SentenceTransformerEmbed(...))

# Usage in flow
field["upper"] = field["text"].transform(my_transform)
field["embedding"] = field["text"].call(text_to_embedding)
```

### 5. **Working Directory Matters**
- CocoIndex sources.LocalFile reads files relative to current directory
- Always change to the project directory before running update
- The CLI should handle this automatically but currently doesn't

### 6. **Environment Setup is Critical**
Required environment variables:
- `COCOINDEX_DATABASE_URL`: PostgreSQL connection string
- `USE_POSTGRES`: Set to "true" for PostgreSQL storage
- Must be set before any CocoIndex operations

## How CocoIndex Actually Works

### Core Concepts

1. **Flow Definition Time vs Runtime**
   - Flow definition creates a computation graph
   - Actual processing happens during update/run
   - Schema must be deterministic at definition time

2. **Incremental Processing**
   - CocoIndex tracks file changes and only reprocesses what's needed
   - Uses internal tracking tables to maintain state
   - Handles additions, updates, and deletions automatically

3. **Type System**
   - Strong typing with Python type hints
   - Automatic schema inference from function signatures
   - Supports basic types, dataclasses, and specialized types (Vector, etc.)

4. **Storage Abstraction**
   - Unified interface for different storage backends
   - PostgreSQL with pgvector for production
   - JSON files for development
   - Extensible for custom storage

### Flow Execution Model

```python
@flow_def(name="ExampleFlow")
def example_flow(flow_builder: FlowBuilder, data_scope: DataScope):
    # 1. Add sources - defines input data
    data_scope["files"] = flow_builder.add_source(
        sources.LocalFile(path=".", included_patterns=["*.py"])
    )

    # 2. Create collectors - for output data
    output = data_scope.add_collector()

    # 3. Define transformations - process data
    with data_scope["files"].row() as file:
        # Each file becomes a row context
        file["processed"] = file["content"].transform(process_function)

        # Nested structures (e.g., chunks within files)
        file["chunks"] = file["content"].transform(split_function)

        with file["chunks"].row() as chunk:
            # Process each chunk
            chunk["embedding"] = chunk["text"].transform(embed_function)

            # Collect results
            output.collect(
                filename=file["filename"],
                chunk_text=chunk["text"],
                embedding=chunk["embedding"]
            )

    # 4. Export to storage
    output.export(
        "output_table",
        targets.Postgres(),
        primary_key_fields=["filename", "chunk_id"]
    )
```

## Our Implementation

### Architecture Overview

```
codesitter/
├── analyzers/                 # Language-specific analyzers
│   ├── base.py               # Abstract base classes
│   ├── registry.py           # Auto-discovery system
│   └── languages/
│       ├── typescript.py     # TypeScript/JavaScript analyzer
│       └── python.py         # Python analyzer
├── flows/                    # CocoIndex flow definitions
│   ├── flexible.py          # Basic flow with language detection
│   ├── analyzer_simple.py   # Working analyzer integration
│   └── analyzer_aware.py    # Alternative implementation
└── cli/                     # Command-line interface
```

### Key Components

#### 1. Language Analyzer Interface
```python
class LanguageAnalyzer(ABC):
    @abstractmethod
    def extract_call_relationships(self, chunk: CodeChunk) -> Iterator[CallRelationship]:
        """Extract function calls from code."""

    def extract_import_relationships(self, chunk: CodeChunk) -> Iterator[ImportRelationship]:
        """Extract imports/dependencies."""

    def extract_custom_metadata(self, chunk: CodeChunk) -> Dict[str, Any]:
        """Extract language-specific metadata."""
```

#### 2. TypeScript Analyzer Implementation
```python
class TypeScriptAnalyzer(LanguageAnalyzer):
    def __init__(self):
        # Initialize Tree-sitter parsers
        self._ts_language = get_language("typescript")
        self._tsx_language = get_language("tsx")

        # Define Tree-sitter queries
        self._call_query = """
        (call_expression
          function: [(identifier) @callee ...]
          arguments: (arguments) @args
        ) @call
        """

    def extract_custom_metadata(self, chunk: CodeChunk) -> Dict[str, Any]:
        metadata = {}

        # React component detection
        if "React" in chunk.text or "jsx" in chunk.filename:
            if "return" in chunk.text and "<" in chunk.text:
                metadata["is_react_component"] = True

        # TypeScript features
        if chunk.filename.endswith((".ts", ".tsx")):
            metadata["has_interfaces"] = "interface " in chunk.text
            metadata["has_type_aliases"] = "type " in chunk.text
            metadata["has_enums"] = "enum " in chunk.text

        return metadata
```

#### 3. Working Flow Implementation (analyzer_simple.py)
```python
@flow_def(name="CodeAnalyzerFlow")
def code_analyzer_flow(flow_builder: FlowBuilder, data_scope: DataScope):
    # Source files with analyzer-supported extensions
    patterns = [f"**/*{ext}" for ext in supported_exts.keys()]
    data_scope["files"] = flow_builder.add_source(
        sources.LocalFile(
            path=".",
            included_patterns=patterns,
            excluded_patterns=["**/node_modules/**", "**/.git/**"]
        )
    )

    code_embeddings = data_scope.add_collector()

    with data_scope["files"].row() as file:
        # Detect language using analyzer
        file["language"] = file["filename"].transform(get_language)

        # Chunk with syntax awareness
        file["chunks"] = file["content"].transform(
            functions.SplitRecursively(),
            language=file["language"],
            chunk_size=1000
        )

        with file["chunks"].row() as chunk:
            # Generate embeddings
            chunk["embedding"] = chunk["text"].call(text_to_embedding)

            # Extract metadata using analyzer
            chunk["is_react"] = chunk["text"].transform(
                is_react_component,
                filename=file["filename"]
            )

            # Collect everything
            code_embeddings.collect(
                filename=file["filename"],
                code=chunk["text"],
                embedding=chunk["embedding"],
                is_react_component=chunk["is_react"],
                # ... other metadata fields
            )

    # Export to PostgreSQL with vector index
    code_embeddings.export(
        "code_analysis",
        targets.Postgres(),
        primary_key_fields=["filename", "location"],
        vector_indexes=[VectorIndexDef("embedding", COSINE_SIMILARITY)]
    )
```

## Correct Usage Patterns

### 1. Setting Up a New Flow

```bash
# 1. Set environment variables
export USE_POSTGRES=true
export COCOINDEX_DATABASE_URL="postgresql://user:pass@localhost:5432/db"

# 2. Create database tables
cocoindex setup /path/to/flow.py

# 3. Initial indexing (from project directory!)
cd /path/to/project
cocoindex update /path/to/flow.py

# 4. Start API server
cocoindex server /path/to/flow.py -ci --address 0.0.0.0:3000
```

### 2. Writing Custom Functions

```python
# Always use @op.function() for transforms
@op.function()
def extract_feature(text: str, config: str) -> bool:
    # Implementation
    return result

# Use dataclasses for complex returns
@dataclasses.dataclass
class AnalysisResult:
    feature_count: int
    feature_list: List[str]

@op.function()
def analyze(text: str) -> AnalysisResult:
    return AnalysisResult(
        feature_count=10,
        feature_list=["a", "b", "c"]
    )
```

### 3. Handling Complex Data

```python
# For nested data, serialize as JSON
@op.function()
def extract_relationships(text: str) -> str:
    relationships = {
        "calls": [...],
        "imports": [...]
    }
    return json.dumps(relationships)

# Then query JSON in PostgreSQL
SELECT
    filename,
    jsonb_array_elements(relationships::jsonb -> 'calls') as call
FROM code_analysis
WHERE jsonb_array_length(relationships::jsonb -> 'calls') > 0;
```

### 4. Incremental Updates

```python
# Watch mode for development
cocoindex server /path/to/flow.py --watch

# Manual update after changes
cocoindex update /path/to/flow.py

# Force complete reindex
cocoindex update --force /path/to/flow.py
```

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. "Database is required for this operation"
```bash
# Solution: Set environment variable
export COCOINDEX_DATABASE_URL="postgresql://..."
# Or load from .env
source .env
```

#### 2. "Setup is not up-to-date"
```bash
# Solution: Force setup
cocoindex setup --force /path/to/flow.py
```

#### 3. Empty indexing results
```bash
# Solution: Run from correct directory
cd /your/project/directory
cocoindex update /path/to/flow.py
```

#### 4. "transform() can only be called on a CocoIndex function"
```python
# Solution: Use @op.function() decorator
@op.function()
def my_transform(text: str) -> str:
    return text.upper()
```

#### 5. Type errors with KTables
```python
# Solution: Use proper types (dataclasses, not dicts)
@dataclasses.dataclass
class MyData:
    field1: str
    field2: int
```

### Debugging Commands

```bash
# Check database connection
psql $COCOINDEX_DATABASE_URL -c "SELECT 1;"

# Verify table exists
psql $COCOINDEX_DATABASE_URL -c "\dt *code*"

# Check data count
psql $COCOINDEX_DATABASE_URL -c "SELECT COUNT(*) FROM your_table;"

# View table schema
psql $COCOINDEX_DATABASE_URL -c "\d your_table"

# Check tracking status
psql $COCOINDEX_DATABASE_URL -c "SELECT * FROM cocoindex_tracking;"
```

## API Usage and Examples

### Starting the API Server

```bash
cd /your/project
cocoindex server /path/to/flow.py -ci --address 0.0.0.0:3000
```

### REST API Endpoints

#### 1. Get Statistics
```bash
curl -X GET http://localhost:3000/cocoindex/stats

# Response
{
  "total_documents": 631,
  "total_chunks": 5432,
  "last_updated": "2024-01-15T10:30:00Z"
}
```

#### 2. Search with Natural Language
```bash
curl -X POST http://localhost:3000/cocoindex/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "React component with useState hook",
    "limit": 5
  }'

# Response
{
  "results": [
    {
      "filename": "src/components/UserProfile.tsx",
      "code": "const UserProfile: React.FC = () => {\n  const [user, setUser] = useState(null);",
      "similarity": 0.92,
      "is_react_component": true
    }
  ]
}
```

#### 3. Query with Filters
```bash
curl -X POST http://localhost:3000/cocoindex/query \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {
      "is_react_component": true,
      "has_interfaces": true
    },
    "limit": 10
  }'
```

#### 4. Get Flow Information
```bash
curl -X GET http://localhost:3000/cocoindex/flow

# Response
{
  "name": "CodeAnalyzerFlow",
  "tables": ["code_analysis"],
  "last_run": "2024-01-15T10:30:00Z",
  "status": "ready"
}
```

### Python Client Usage

```python
import requests
from typing import List, Dict

class CocoIndexClient:
    def __init__(self, base_url: str = "http://localhost:3000/cocoindex"):
        self.base_url = base_url

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Semantic search across codebase."""
        response = requests.post(
            f"{self.base_url}/search",
            json={"query": query, "limit": limit}
        )
        return response.json()["results"]

    def find_react_components(self) -> List[Dict]:
        """Find all React components."""
        response = requests.post(
            f"{self.base_url}/query",
            json={"filter": {"is_react_component": True}}
        )
        return response.json()["results"]

    def find_typescript_interfaces(self) -> List[Dict]:
        """Find all TypeScript interfaces."""
        response = requests.post(
            f"{self.base_url}/query",
            json={"filter": {"has_interfaces": True}}
        )
        return response.json()["results"]

# Usage
client = CocoIndexClient()
results = client.search("authentication logic")
for result in results:
    print(f"{result['filename']}: {result['similarity']:.2f}")
```

### Using with CocoInsight UI

1. Start the server with `-ci` flag:
   ```bash
   cocoindex server /path/to/flow.py -ci --address 0.0.0.0:3000
   ```

2. Open https://cocoindex.io/cocoinsight

3. Enter your API endpoint: `http://localhost:3000/cocoindex`

4. Use the UI for:
   - Visual code search
   - Filter by metadata
   - Explore relationships
   - View statistics

## Future Improvements

### 1. CLI Enhancements
```python
# Fix working directory issue in index.py
def index(path: str, ...):
    # Change to target directory before running cocoindex
    original_dir = os.getcwd()
    os.chdir(path)
    try:
        subprocess.run(["cocoindex", "update", flow_path])
    finally:
        os.chdir(original_dir)
```

### 2. Enhanced Relationship Extraction
```python
# Store relationships in separate tables
@flow_def(name="EnhancedAnalyzer")
def enhanced_flow(flow_builder, data_scope):
    # Multiple collectors for different data types
    chunks = data_scope.add_collector()
    calls = data_scope.add_collector()
    imports = data_scope.add_collector()

    # Process and collect separately
    # Export to different tables
    chunks.export("code_chunks", ...)
    calls.export("call_relationships", ...)
    imports.export("import_relationships", ...)
```

### 3. Real-time Analysis
```python
# Use CocoIndex's watch capabilities
@flow_def(name="LiveAnalyzer")
def live_flow(flow_builder, data_scope):
    data_scope["files"] = flow_builder.add_source(
        sources.LocalFile(
            path=".",
            watch=True,  # Enable file watching
            debounce_ms=500
        )
    )
```

### 4. Cross-Language Analysis
```python
# Track language boundaries
@op.function()
def detect_ffi_boundary(chunk: CodeChunk) -> bool:
    """Detect Foreign Function Interface calls."""
    # Check for patterns indicating cross-language calls
    return has_ffi_patterns(chunk)
```

### 5. Advanced Query Interface
```python
# GraphQL-style queries
query = """
{
  functions(where: {hasAsyncCalls: true}) {
    name
    file
    calls {
      callee
      arguments
    }
    imports {
      from
      items
    }
  }
}
"""
```

## Conclusion

This implementation journey revealed the importance of:
1. **Following framework patterns exactly** - Don't assume or invent APIs
2. **Understanding the execution model** - Flow definition vs runtime
3. **Keeping transformations simple** - Complex logic should be broken down
4. **Proper environment setup** - Database connections and working directories matter
5. **Testing incrementally** - Verify each step works before building on it

The final working solution (`analyzer_simple.py`) successfully integrates Tree-sitter-based language analysis with CocoIndex's incremental indexing system, providing real-time, queryable code intelligence across multiple programming languages.

### Key Takeaways for CocoIndex Users

1. **Start with examples** - Use `examples/code_embedding` as your template
2. **Use proper decorators** - `@op.function()` for all transforms
3. **Keep data flat** - Avoid deeply nested structures
4. **Run from project directory** - CocoIndex needs to find your files
5. **Set environment variables** - Database connection is required
6. **Use the built-in server** - It provides REST API and UI integration
7. **Leverage incremental updates** - Don't reindex everything each time

The combination of Tree-sitter's precise parsing and CocoIndex's incremental processing creates a powerful system for maintaining live, queryable code intelligence at scale.
