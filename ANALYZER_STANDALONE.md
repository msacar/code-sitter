# Standalone Analyzer Usage - Integrated CLI

The analyzer functionality is now fully integrated into the main `codesitter` CLI as the `analyze` command. This provides a clean, unified interface for all codesitter functionality.

## The `codesitter analyze` Command

A comprehensive set of commands for running analyzers directly on files:

```bash
# List all available analyzers
codesitter analyze list

# Analyze a single file
codesitter analyze file src/auth.ts

# Get JSON output for scripting
codesitter analyze file src/auth.ts --json

# Analyze entire directories
codesitter analyze directory ./src --ext .ts

# Extract specific information
codesitter analyze file src/auth.ts --calls-only    # Just function calls
codesitter analyze file src/auth.ts --imports-only  # Just imports
```

## Key Features

1. **No Dependencies on Chunking**
   - Works on complete files
   - No context loss
   - Full analysis results

2. **Multiple Output Formats**
   - Pretty-printed for humans
   - JSON for scripting
   - Filtered views (calls/imports only)

3. **Batch Processing**
   - Analyze entire directories
   - Filter by extension
   - Summary statistics

4. **Scriptable**
   - JSON output for integration
   - Exit codes for CI/CD
   - Composable with other tools

## Example Use Cases

### Find All React Components
```bash
codesitter analyze directory ./src --ext .tsx --json | jq '.files[] | select(.metadata.is_react_component)'
```

### Check Dependencies
```bash
codesitter analyze file src/index.ts --imports-only
```

### CI/CD Integration
```bash
# In your CI pipeline
codesitter analyze file src/main.ts --json > analysis.json
if grep -q "unsafe_call" analysis.json; then
  echo "Found unsafe calls!"
  exit 1
fi
```

### Generate Reports
```bash
# Analyze all TypeScript files and create a report
for file in $(find src -name "*.ts"); do
  echo "=== $file ==="
  codesitter analyze file "$file"
done > code_report.txt
```

## Advanced Examples

See `analyzer_examples.py` for more complex usage:

```bash
# Find React components
./analyzer_examples.py react-components ./src

# Analyze dependencies
./analyzer_examples.py dependencies src/index.ts

# Find potentially unused functions
./analyzer_examples.py unused src/utils.ts
```

## Testing

Run the test script to verify everything works:

```bash
./test_integrated_analyzer.sh
```

## Benefits

- ✅ **Standalone**: No CocoIndex or chunking needed
- ✅ **Fast**: Direct analysis, no overhead
- ✅ **Flexible**: Use in scripts, CI/CD, or manually
- ✅ **Complete**: Full file context preserved
- ✅ **Extensible**: Easy to add new analyzers

This gives you exactly what you wanted - a way to run analyzers separately and independently! 🎉
