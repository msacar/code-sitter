# Smart Chunking for Codesitter 🧠

## The Problem

Traditional code chunking (like CocoIndex's default) splits files based on size, which can lead to:

```typescript
// Chunk 1 ends here...
export const authMiddleware = (options: AuthMiddlewareOptions = {}): middy.MiddlewareObj<APIGatewayProxyEvent, APIGatewayProxyResult> =>

// Chunk 2 starts here... WTF is this?
=> ({
    before: async (request: middy.Request<...>) => {
```

This causes:
- ❌ Lost context (imports in chunk 1, usage in chunk 2)
- ❌ Broken functions
- ❌ Incomplete analysis
- ❌ Poor search results

## The Solution: Smart Chunking

Our smart chunking system analyzes code FIRST, then creates intelligent chunks:

### 1. **Context-Aware Chunks**
Every chunk includes necessary context:

```typescript
// File: auth.ts
// Function: authMiddleware

import middy from '@middy/core'
import { APIGatewayProxyEvent } from 'aws-lambda'

export const authMiddleware = (options) => ({
    // Complete function, never split!
})
```

### 2. **Meaningful Boundaries**
- Imports stay together
- Functions are atomic units
- Classes remain intact
- Methods stay with their class

### 3. **Rich Metadata**
Each chunk carries:
```json
{
  "chunk_type": "function",
  "function_name": "authMiddleware",
  "file_imports": ["@middy/core", "aws-lambda"],
  "is_exported": true,
  "dependencies": ["file:imports"],
  "calls": ["ApiError", "validateToken"]
}
```

## How It Works

```python
# Traditional chunking
chunks = content.split_by_size(1000)  # Dumb splitting

# Smart chunking
analyzer = SmartChunker()
chunks = analyzer.chunk_file(filepath, content)  # Intelligent splitting
```

### The Process:

1. **Parse entire file** with Tree-sitter
2. **Extract structure**: imports, functions, classes
3. **Create semantic chunks**: Each chunk is meaningful
4. **Add context**: Every chunk knows about imports/exports
5. **Track relationships**: Dependencies between chunks

## Benefits

### Better Incremental Indexing
```diff
# File changes: only validateToken function modified

Traditional chunking:
- Chunk 1: ❌ Re-index (contains part of validateToken)
- Chunk 2: ❌ Re-index (contains rest of validateToken)
- Chunk 3: ❌ Re-index (overlaps with chunk 2)

Smart chunking:
- Imports chunk: ✅ Unchanged
- authMiddleware chunk: ✅ Unchanged
- validateToken chunk: ❌ Re-index (only this one!)
+ 66% fewer chunks to re-index!
```

### Better Search Results
```python
# Search: "authMiddleware"

Traditional: Returns half a function signature
Smart: Returns complete function with imports and context
```

### Better Analysis
```python
# Analyzer sees:
- Complete functions
- All imports available
- Can track cross-function calls
- Understands module dependencies
```

## Usage

### Quick Test
```bash
python test_smart_chunking.py
```

### With CocoIndex Flow
```bash
# Use the smart chunking flow
cocoindex update src/codesitter/flows/smart_chunking.py

# Or with CLI (when integrated)
codesitter index --flow smart_chunking
```

### Direct API Usage
```python
from codesitter.chunkers import SmartChunker

chunker = SmartChunker()
chunks = chunker.chunk_file("app.ts", content)

for chunk in chunks:
    print(f"{chunk.chunk_type}: {chunk.chunk_id}")
    print(f"Metadata: {chunk.metadata}")
```

## Implementation Status

✅ **Implemented:**
- Smart chunker core logic
- TypeScript/JavaScript support
- Function and class extraction
- Import preservation
- Metadata extraction
- CocoIndex flow integration

🚧 **TODO:**
- CLI integration
- More language analyzers
- Dependency graph building
- Cross-file relationship tracking
- Chunk caching for incremental updates

## Next Steps

1. **Test the smart chunking**:
   ```bash
   python test_smart_chunking.py
   ```

2. **Try with a real project**:
   ```bash
   cd /your/typescript/project
   python -m codesitter.flows.smart_chunking
   ```

3. **Compare results** with traditional chunking

4. **Extend** to more languages

## The Future

Smart chunking enables:
- 🚀 Faster incremental indexing
- 🎯 More accurate code search
- 🧩 Better cross-file analysis
- 📊 Richer code intelligence
- 🔄 Smarter dependency tracking

This is just the beginning. With smart chunks as building blocks, we can build truly intelligent code analysis tools that understand code the way developers do - as meaningful, interconnected units, not arbitrary text fragments.
