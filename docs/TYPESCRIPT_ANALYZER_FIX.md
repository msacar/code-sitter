# TypeScript Analyzer Fix

## Problem
The TypeScript analyzer was only showing minimal metadata when analyzing files:
```
Analysis: modules/shortlink-api/src/services/instanceService.ts
Language: typescript | Analyzer: TypeScriptAnalyzer
================================================================================
📊 Metadata:
  has_async_functions: ✓
```

## Root Cause
The tree-sitter API has changed in newer versions. The old way of creating queries:
```python
query = Query(language, query_string)
captures = query.captures(tree.root_node)
```

No longer works and throws: `'tree_sitter.Query' object has no attribute 'captures'`

## Solution
Use the new API where queries are created from the language object:
```python
query = language.query(query_string)
captures = query.captures(tree.root_node)
```

## Files Modified
1. `/src/codesitter/analyzers/languages/typescript.py` - Updated to use `language.query()`
2. `/src/codesitter/analyzers/languages/python.py` - Updated to use `language.query()`
3. `/src/codesitter/cli/commands/analyze.py` - Fixed attribute access bug (`imp.source` → `imp.imported_from`)

## Result
The TypeScript analyzer now properly extracts:
- ✅ Import statements with source and imported items
- ✅ Function calls with caller/callee relationships
- ✅ TypeScript-specific metadata (async functions, React components, etc.)

## Testing
Run: `codesitter analyze file <typescript-file>`

You should now see full analysis output including imports, function calls, and metadata.
