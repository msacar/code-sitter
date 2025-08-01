# Using the Enhanced Analyzer Detailed Flow

The `analyzer_detailed` flow is now available in the codesitter CLI! Here are your options:

## Option 1: Use with codesitter CLI (Now Working!)
```bash
# After the fixes, this should now work:
codesitter index -p /Users/mustafaacar/retter/shortlink --flow analyzer_detailed --postgres

# With verbose output to see progress:
codesitter index -p /Users/mustafaacar/retter/shortlink --flow analyzer_detailed --postgres -v

# With timeout adjustment (if needed):
codesitter index -p /Users/mustafaacar/retter/shortlink --flow analyzer_detailed --postgres -t 600
```

## Option 2: Use cocoindex directly (Alternative)
```bash
cd /Users/mustafaacar/retter/shortlink
cocoindex update --setup /Users/mustafaacar/codesitter/src/codesitter/flows/analyzer_detailed.py
```

## Option 3: Use analyzer_aware (If detailed still has issues)
```bash
# This flow already works and provides similar functionality:
codesitter index -p /Users/mustafaacar/retter/shortlink --flow analyzer_aware --postgres
```

## What analyzer_detailed provides:
- Detailed function signatures with parameters and types
- Call relationships with arguments
- More structured data than boolean flags
- Better search capabilities

## Troubleshooting

If you still get parser errors:
1. First test the parser fix:
   ```bash
   cd /Users/mustafaacar/codesitter
   python test_analyzer_fix.py
   ```

2. Check your tree-sitter version:
   ```bash
   pip show tree-sitter tree-sitter-language-pack
   ```

3. Update if needed:
   ```bash
   uv pip install -U tree-sitter tree-sitter-language-pack
   ```

## Example Queries After Indexing

Once indexed with analyzer_detailed, you can query:
```bash
# Find functions by name
curl -X POST http://0.0.0.0:3000/cocoindex/query \
  -H "Content-Type: application/json" \
  -d '{
    "flow_name": "DetailedCodeAnalysis",
    "target_name": "code_chunks_detailed",
    "filter": {
      "function_signatures": {"$contains": "\"name\": \"fetchData\""}
    }
  }'
```
