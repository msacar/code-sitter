# Codesitter Smart Chunking Implementation

## Overview

We've successfully implemented smart chunking that integrates seamlessly with the existing analyzer architecture. The system now:

1. **Analyzes files completely** before chunking
2. **Creates meaningful chunks** at function/class boundaries
3. **Preserves context** in every chunk
4. **Enables better incremental indexing**

## Architecture

```
src/codesitter/
├── analyzers/          # Language analyzers (unchanged)
│   ├── base.py        # Analyzer protocol
│   ├── registry.py    # Analyzer registration
│   └── languages/     # Language implementations
├── chunkers/          # NEW: Smart chunking system
│   ├── base.py        # ChunkResult types
│   └── smart_chunker.py # Smart chunking logic
├── flows/
│   └── smart_chunking.py # NEW: CocoIndex flow
└── cli/
    └── commands/
        └── index.py   # Updated with smart_chunking option
```

## How It Works

### 1. Smart Chunker Uses Analyzers

```python
# smart_chunker.py
analyzer = get_analyzer(ext)  # Get language analyzer
analysis = self._analyze_file(analyzer, file_path, content)
chunks = self._create_chunks_from_analysis(analysis)
```

### 2. Creates Context-Aware Chunks

Each chunk includes:
- File path and location
- All imports from the file
- Complete function/class body
- Rich metadata

### 3. Integrates with CocoIndex

```python
# smart_chunking.py flow
chunks = files["content"].transform(
    smart_chunk_file,
    path=files["path"]
).explode()
```

## Usage

### CLI Usage

```bash
# Index with smart chunking
codesitter index --flow smart_chunking

# With PostgreSQL
codesitter index --flow smart_chunking --postgres

# Watch mode
codesitter index --flow smart_chunking --watch
```

### Direct Flow Usage

```bash
# Setup database (first time only)
cocoindex setup src/codesitter/flows/smart_chunking.py

# Run indexing
cocoindex update src/codesitter/flows/smart_chunking.py
```

### Programmatic Usage

```python
from codesitter.chunkers import SmartChunker

chunker = SmartChunker()
chunks = chunker.chunk_file("app.ts", content)

for chunk in chunks:
    print(f"{chunk.chunk_type}: {chunk.chunk_id}")
    print(f"Metadata: {chunk.metadata}")
```

## Benefits

### 1. No More Split Functions
```typescript
// Traditional: Function split across chunks
// Chunk 1: export const authMiddleware = (options: AuthMiddlewareOptions = {}):
// Chunk 2: middy.MiddlewareObj<APIGatewayProxyEvent...

// Smart: Complete function in one chunk
// Chunk: Full function with imports and context
```

### 2. Better Incremental Updates
```
File changes: One function modified

Traditional: 2-3 chunks need reindexing
Smart: Only 1 chunk needs reindexing
```

### 3. Rich Metadata
```json
{
  "chunk_type": "function",
  "function_name": "authMiddleware",
  "is_exported": true,
  "file_imports": [...],
  "dependencies": ["file:imports"]
}
```

## Query Examples

### Find All Exported Functions
```sql
SELECT chunk_id, metadata->>'function_name'
FROM smart_chunks
WHERE chunk_type = 'function'
  AND metadata->>'is_exported' = 'true';
```

### Find Functions in a Specific File
```sql
SELECT * FROM smart_chunks
WHERE chunk_id LIKE 'src/auth.ts:%'
  AND chunk_type = 'function';
```

### Semantic Search with Context
```sql
SELECT chunk_id, text, metadata
FROM smart_chunks
WHERE chunk_type = 'function'
ORDER BY embedding <-> (SELECT embedding FROM query_embedding)
LIMIT 5;
```

## Testing

Run the demo scripts:

```bash
# See smart chunking in action
python demo_smart_chunking.py

# Compare with traditional chunking
python compare_chunking.py

# Quick start guide
python smart_chunking_quickstart.py
```

## Next Steps

1. **Enhance Language Support**: Add more sophisticated analysis for Python, Java, etc.
2. **Dependency Tracking**: Build call graphs between chunks
3. **Caching**: Add incremental update caching
4. **Performance**: Optimize for large codebases

## Clean Boundaries Maintained

- **Analyzers**: Still work on complete files, don't know about chunks
- **Chunkers**: Use analyzers for understanding, create chunks
- **Flows**: Integrate chunkers with CocoIndex
- **CLI**: Provides user interface

Each module has a single responsibility and clean interfaces!
