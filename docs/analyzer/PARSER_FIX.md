# Tree-sitter Parser API Fix

## Problem
You encountered this error:
```
ERROR:analyzer_detailed:Error extracting calls from test/setup.ts: 'tree_sitter.Parser' object has no attribute 'set_language'
```

## Root Cause
The tree-sitter API has changed between versions. The older API used:
```python
parser = Parser()
parser.set_language(language)
```

But newer versions might use a different approach.

## Solution Applied

1. **Created a utility module** (`parser_utils.py`) that handles different tree-sitter API versions:
   - Tries multiple approaches to create a parser
   - Falls back gracefully between different API versions
   - Provides detailed error messages if all methods fail

2. **Updated all analyzers** to use this utility:
   - TypeScript analyzer
   - Enhanced TypeScript analyzer
   - Python analyzer
   - Java analyzer (if present)

3. **The utility tries these methods in order:**
   - `parser.language = language` (property assignment)
   - `parser.set_language(language)` (method call)
   - `Parser(language)` (constructor parameter)
   - Language instantiation fallback

## Testing the Fix

Run the test script to verify:
```bash
cd /Users/mustafaacar/codesitter
python test_analyzer_fix.py
```

Then try running the flow again:
```bash
cocoindex update --setup /Users/mustafaacar/codesitter/src/codesitter/flows/analyzer_detailed.py
```

## If Still Having Issues

1. **Check tree-sitter version:**
```bash
pip show tree-sitter tree-sitter-language-pack
```

2. **Update dependencies:**
```bash
uv pip install -U tree-sitter tree-sitter-language-pack
```

3. **Use the simpler flow first:**
```bash
# The analyzer_aware flow might work better as it uses existing analyzers
cocoindex update --setup /Users/mustafaacar/codesitter/src/codesitter/flows/analyzer_aware.py
```

## Alternative: Use Basic Boolean Metadata
If the detailed analysis is causing issues, you can still use your original analyzer_aware flow which extracts:
- is_react_component
- has_interfaces
- has_async_functions
- etc.

This gives you searchable metadata without the complexity of detailed function signature extraction.
