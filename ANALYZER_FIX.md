# Analyzer CLI Fix

## Issue
The analyzer CLI was failing with "No analyzer found for .ts files" due to:

1. **Wrong function call**: `get_analyzer(ext)` was being called with just the extension (`.ts`) instead of a full filename
2. **Duplicate registrations**: Analyzers were being registered multiple times, causing warnings
3. **Default analyzer conflicts**: Default analyzers were overriding custom ones

## Fix Applied

### 1. Fixed `get_analyzer` calls
Changed from:
```python
analyzer = get_analyzer(ext)  # Wrong - ext is just ".ts"
```

To:
```python
analyzer = get_analyzer(str(path))  # Correct - full filename
```

### 2. Prevented duplicate initialization
Added initialization guard:
```python
_initialized = False

def _ensure_initialized():
    global _initialized
    if not _initialized:
        register_defaults()
        auto_discover_analyzers()
        _initialized = True
```

### 3. Skip defaults for custom analyzers
Updated `register_defaults()` to skip languages that have custom analyzers:
```python
skip_languages = {
    "typescript", "javascript", "python", "java"
}
```

### 4. Improved analyzer listing
Fixed the `analyze list` command to properly group analyzers by class.

## Testing

Run the test script to verify the fix:
```bash
./test_analyzer_fix.sh
```

Or test manually:
```bash
# Should work now!
codesitter analyze file modules/shortlink-api/src/services/instanceService.ts

# List analyzers
codesitter analyze list

# Get JSON output
codesitter analyze file your-file.ts --json
```

## Result

The analyzer CLI now works correctly:
- ✅ No more "No analyzer found" errors
- ✅ No more duplicate registration warnings
- ✅ Proper analyzer detection for all file types
- ✅ Clean output without warnings
