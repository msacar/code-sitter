# Enhanced Code Analysis with Dossier-like Features

## Overview

We've enhanced codesitter with Dossier-inspired capabilities to extract detailed function signatures, types, and more from your TypeScript codebase. This goes beyond simple boolean metadata to provide rich, queryable information about your code structure.

## What's New

### Detailed Function Signatures
Instead of just knowing "has_functions: true", you now get:
```json
{
  "functions": [
    {
      "kind": "function",
      "name": "fetchUserData",
      "parameters": [
        {"name": "userId", "type": "string", "optional": false},
        {"name": "options", "type": "FetchOptions", "optional": true}
      ],
      "returnType": "Promise<User>",
      "isAsync": true,
      "isExport": true,
      "docstring": "/** Fetches user data from the API */",
      "line": 25,
      "column": 0
    }
  ]
}
```

### Interface and Type Definitions
```json
{
  "definitions": [
    {
      "kind": "interface",
      "name": "User",
      "line": 10,
      "isExport": true
    },
    {
      "kind": "type_alias",
      "name": "UserId",
      "line": 15,
      "isExport": false
    }
  ]
}
```

## Setup

1. Use the new enhanced analyzer flow:
```bash
# Set up the database
cocoindex setup /Users/mustafaacar/codesitter/src/codesitter/flows/analyzer_detailed.py

# Run the indexing
cocoindex server /Users/mustafaacar/codesitter/src/codesitter/flows/analyzer_detailed.py -ci --address 0.0.0.0:3000
```

2. Or integrate the enhanced TypeScript analyzer:
```python
# In your analyzer registry
from codesitter.analyzers.languages.typescript_enhanced import EnhancedTypeScriptAnalyzer

# Register it
registry.register_analyzer([".ts", ".tsx", ".js", ".jsx"], EnhancedTypeScriptAnalyzer())
```

## New API Queries

### 1. Find Functions by Name
```bash
curl -X POST http://0.0.0.0:3000/cocoindex/query \
  -H "Content-Type: application/json" \
  -d '{
    "flow_name": "DetailedCodeAnalysis",
    "target_name": "code_chunks_detailed",
    "filter": {
      "function_signatures": {"$contains": "\"name\": \"fetchUserData\""}
    },
    "limit": 10
  }'
```

### 2. Find Async Functions
```bash
curl -X POST http://0.0.0.0:3000/cocoindex/query \
  -H "Content-Type: application/json" \
  -d '{
    "flow_name": "DetailedCodeAnalysis",
    "target_name": "code_chunks_detailed",
    "filter": {
      "function_signatures": {"$contains": "\"isAsync\": true"}
    },
    "limit": 20
  }'
```

### 3. Find Functions with Specific Parameters
```bash
# Find functions that take a userId parameter
curl -X POST http://0.0.0.0:3000/cocoindex/query \
  -H "Content-Type: application/json" \
  -d '{
    "flow_name": "DetailedCodeAnalysis",
    "target_name": "code_chunks_detailed",
    "filter": {
      "function_signatures": {"$contains": "\"name\": \"userId\""}
    },
    "limit": 10
  }'
```

### 4. Find Exported Interfaces
```bash
curl -X POST http://0.0.0.0:3000/cocoindex/query \
  -H "Content-Type: application/json" \
  -d '{
    "flow_name": "DetailedCodeAnalysis",
    "target_name": "code_chunks_detailed",
    "filter": {
      "function_signatures": {"$contains": "\"kind\": \"interface\""},
      "function_signatures": {"$contains": "\"isExport\": true"}
    },
    "limit": 20
  }'
```

### 5. Complex Type Search
```bash
# Find functions returning Promise types
curl -X POST http://0.0.0.0:3000/cocoindex/query \
  -H "Content-Type: application/json" \
  -d '{
    "flow_name": "DetailedCodeAnalysis",
    "target_name": "code_chunks_detailed",
    "filter": {
      "function_signatures": {"$contains": "\"returnType\": \"Promise"}
    },
    "limit": 15
  }'
```

### 6. Semantic Search with Context
```bash
# First get embedding for "user authentication"
EMBEDDING=$(curl -s -X POST http://0.0.0.0:3000/cocoindex/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "user authentication", "model": "all-MiniLM-L6-v2"}' | jq -r '.embedding')

# Then search with function context
curl -X POST http://0.0.0.0:3000/cocoindex/vector_search \
  -H "Content-Type: application/json" \
  -d "{
    \"flow_name\": \"DetailedCodeAnalysis\",
    \"target_name\": \"code_chunks_detailed\",
    \"vector_search\": {
      \"field\": \"embedding\",
      \"vector\": $EMBEDDING,
      \"limit\": 5
    },
    \"fields\": [\"filename\", \"chunk_text\", \"function_signatures\"]
  }"
```

## Direct SQL Queries (PostgreSQL)

For even more powerful queries:

```sql
-- Find all functions with more than 3 parameters
SELECT filename,
       jsonb_array_elements(function_signatures::jsonb) ->> 'name' as function_name,
       jsonb_array_length(jsonb_array_elements(function_signatures::jsonb) -> 'parameters') as param_count
FROM code_chunks_detailed
WHERE function_signatures != '[]'
  AND jsonb_array_length(jsonb_array_elements(function_signatures::jsonb) -> 'parameters') > 3;

-- Find all Promise-returning functions
SELECT DISTINCT filename,
       jsonb_array_elements(function_signatures::jsonb) ->> 'name' as function_name,
       jsonb_array_elements(function_signatures::jsonb) ->> 'returnType' as return_type
FROM code_chunks_detailed
WHERE function_signatures::text LIKE '%Promise%';

-- Find functions with optional parameters
SELECT filename,
       func ->> 'name' as function_name,
       param ->> 'name' as param_name
FROM code_chunks_detailed,
     jsonb_array_elements(function_signatures::jsonb) func,
     jsonb_array_elements(func -> 'parameters') param
WHERE param ->> 'optional' = 'true';
```

## Comparison with Dossier

| Feature | Dossier | Codesitter Enhanced |
|---------|---------|-------------------|
| Function signatures | ✅ Full | ✅ Full |
| Parameter types | ✅ | ✅ |
| Return types | ✅ | ✅ |
| JSDoc parsing | ✅ Advanced | ✅ Basic |
| Type resolution | ✅ Cross-file | ❌ Single-file |
| Language support | TS, Python | 20+ languages |
| Integration | Standalone CLI | CocoIndex integrated |
| Output format | JSON only | PostgreSQL + JSON |
| Vector search | ❌ | ✅ |

## Benefits Over Current Implementation

1. **Detailed Queries**: Search for functions by parameter types, return types, async status
2. **Better Documentation**: Extract and search JSDoc comments
3. **Type Awareness**: Find interfaces, type aliases, and their usage
4. **Call Context**: Not just "who calls who" but with what parameters
5. **Export Tracking**: Know what's part of your public API

## Next Steps

1. **Full Dossier Integration**: Run Dossier as subprocess for complete type resolution
2. **Cross-file Analysis**: Track type definitions across imports
3. **GraphQL API**: Build a GraphQL layer for more flexible queries
4. **IDE Integration**: Use this data for better code navigation

## Example Use Cases

- Find all functions that accept a specific interface
- Locate all async functions that don't have error handling
- Identify exported functions without documentation
- Track parameter type changes across refactoring
- Build dependency graphs based on actual function calls
