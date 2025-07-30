# Using Analyzer Flows

## Overview

The codesitter project provides multiple flows that leverage language analyzers to different degrees:

### 1. Basic Flows (No Analyzer Usage)
- `basic`, `simple`, `minimal` - Use only CocoIndex's built-in features

### 2. Flexible Flow (Minimal Analyzer Usage)
- `flexible` - Uses analyzer only for language detection
- Does NOT extract relationships or custom metadata

### 3. Analyzer-Aware Flows (Full Analyzer Usage)
- `analyzer_aware` - Extracts custom metadata (React components, TypeScript features)
- `analyzer_advanced` - Extracts everything: metadata, call relationships, imports

## Running Analyzer Flows

### Setup (First Time)
```bash
# Set up database tables
export USE_POSTGRES=true
export COCOINDEX_DATABASE_URL="postgresql://user:pass@localhost:5432/dbname"

# For analyzer_aware flow
cocoindex setup /path/to/codesitter/src/codesitter/flows/analyzer_aware.py

# For analyzer_advanced flow
cocoindex setup /path/to/codesitter/src/codesitter/flows/analyzer_advanced.py
```

### Indexing
```bash
# Change to your project directory
cd /Users/mustafaacar/retter/shortlink

# Run analyzer_aware flow
codesitter index -p . --flow analyzer_aware --postgres

# Or run analyzer_advanced flow for full analysis
codesitter index -p . --flow analyzer_advanced --postgres
```

## What Gets Analyzed

### analyzer_aware Flow
Creates table: `code_chunks_with_metadata` - Main analysis data

**New Feature: File Processing with Progress Tracking**
The analyzer_aware flow now provides enhanced visibility:
- Pre-scans to show total file count before processing
- Shows files grouped by extension
- Logs each file with progress counter: `[1/25] Processing file: filename.ts [Language: typescript]`
- Provides real-time progress indication during indexing

Example output:
```
Found 25 files to process
Files by extension: {'.js': 10, '.py': 8, '.ts': 5, '.tsx': 2}
[1/25] Processing file: src/index.ts [Language: typescript]
[2/25] Processing file: src/utils.js [Language: javascript]
...
```

To get file counts from the indexed data, use SQL queries:
```sql
-- Count unique files by language
SELECT language, COUNT(DISTINCT filename) as file_count
FROM code_chunks_with_metadata
GROUP BY language
ORDER BY file_count DESC;
```

Columns in `code_chunks_with_metadata`:
- Basic: filename, location, chunk_text, embedding, language
- Metadata: is_react_component, has_interfaces, has_type_aliases, has_enums, has_async_functions, is_test_file

### analyzer_advanced Flow
Creates table: `code_chunks_analyzed`

Columns:
- Basic: filename, location, chunk_text, embedding, language
- Analysis: has_calls, has_imports, call_count, import_count
- JSON data: calls_json (array of call relationships), imports_json (array of imports)
- Metadata: Same as analyzer_aware

## Querying the Data

### File Statistics from analyzer_aware flow
```sql
-- Count unique files in the index
SELECT COUNT(DISTINCT filename) as total_files
FROM code_chunks_with_metadata;

-- Files by language
SELECT language, COUNT(DISTINCT filename) as file_count
FROM code_chunks_with_metadata
GROUP BY language
ORDER BY file_count DESC;

-- Files by extension (extract from filename)
SELECT
    SUBSTRING(filename FROM '\.([^.]+)$') as extension,
    COUNT(DISTINCT filename) as file_count
FROM code_chunks_with_metadata
GROUP BY extension
ORDER BY file_count DESC;
```

### Find React Components
```sql
SELECT filename, chunk_text
FROM code_chunks_with_metadata
WHERE is_react_component = true;
```

### Find TypeScript Interfaces
```sql
SELECT filename, chunk_text
FROM code_chunks_with_metadata
WHERE has_interfaces = true;
```

### Find Functions with Many Calls
```sql
SELECT filename, chunk_text, calls_json
FROM code_chunks_analyzed
WHERE call_count > 5;
```

### Extract Call Relationships
```sql
SELECT
    filename,
    jsonb_array_elements(calls_json::jsonb) as call
FROM code_chunks_analyzed
WHERE has_calls = true;
```

## Troubleshooting

### Error: "transform() can only be called on a CocoIndex function"
This means a lambda or non-decorated function was used with `.transform()`. All functions must be decorated with `@op.function()`.

### Error: "module 'cocoindex.op' has no attribute 'apply'"
The `op.apply()` method doesn't exist. Use `.transform()` with proper function parameters instead.

### No TypeScript Analysis
Check that:
1. Tree-sitter language pack is installed: `pip install tree-sitter-language-pack`
2. TypeScript analyzer is registered (check logs during startup)
3. Your files have .ts/.tsx extensions

## Flow Comparison

| Flow | Language Detection | Metadata | Calls | Imports | Best For |
|------|-------------------|----------|-------|---------|----------|
| flexible | ✓ | ✗ | ✗ | ✗ | Basic indexing |
| analyzer_aware | ✓ | ✓ | ✗ | ✗ | Finding components/types |
| analyzer_advanced | ✓ | ✓ | ✓ | ✓ | Full code analysis |
