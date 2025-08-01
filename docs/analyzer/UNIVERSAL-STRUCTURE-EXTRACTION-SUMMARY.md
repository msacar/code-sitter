# Analyzer CLI - Integrated into codesitter

The analyzer functionality is now integrated into the main `codesitter` CLI as the `analyze` command.

## Installation

```bash
# Make sure codesitter is installed
uv pip install -e .
```

## Usage

### List Available Analyzers
```bash
codesitter analyze list
```

Shows all registered analyzers and their capabilities (calls, imports, metadata).

### Analyze a Single File
```bash
# Pretty output (default)
codesitter analyze file src/auth.ts

# JSON output for scripting
codesitter analyze file src/auth.ts --json
```

### Analyze a Directory
```bash
# Analyze all supported files
codesitter analyze directory ./src

# Filter by extension
codesitter analyze directory ./src --ext .ts

# JSON output with statistics
codesitter analyze directory ./src --json
```

## Example Output

### Pretty Output
```
🔍 Analysis: src/auth.ts
Language: typescript | Analyzer: TypeScriptAnalyzer
================================================================================

📦 Imports (3):
  @middy/core → middy (line 1)
  aws-lambda → APIGatewayProxyEvent, APIGatewayProxyResult (line 2)
  ../utils/middy-wrapper → MiddyContext (line 3)

📞 Function Calls (2):
  authMiddleware → ApiError() at line 28
  authMiddleware → ApiError() at line 38

📊 Metadata:
  has_functions: ✓
  has_classes: ✓
  has_interfaces: ✓
  is_react_component: ✗
```

### JSON Output
```json
{
  "file": "src/auth.ts",
  "language": "typescript",
  "analyzer": "TypeScriptAnalyzer",
  "imports": [
    {
      "source": "@middy/core",
      "items": ["middy"],
      "type": "named",
      "line": 1
    }
  ],
  "calls": [
    {
      "caller": "authMiddleware",
      "callee": "ApiError",
      "arguments": ["500", "'Tenant configuration not loaded'"],
      "line": 28
    }
  ],
  "metadata": {
    "has_functions": true,
    "has_classes": true,
    "is_react_component": false
  }
}
```

## Scripting Examples

### Find All React Components
```bash
for file in $(find src -name "*.tsx"); do
  result=$(codesitter analyze file "$file" --json)
  if echo "$result" | jq -e '.metadata.is_react_component' > /dev/null; then
    echo "$file is a React component"
  fi
done
```

### Extract All Imports
```bash
# Get all external dependencies
codesitter analyze directory ./src --json | \
  jq -r '.files[].imports[].source' | \
  grep -v "^\." | \
  sort | uniq
```

### CI/CD Integration
```bash
# Check for specific patterns
if codesitter analyze file src/api.ts --json | grep -q "unsafe_call"; then
  echo "Found unsafe API calls!"
  exit 1
fi
```

### Generate Import Graph
```bash
# Create a simple import dependency list
for file in src/**/*.ts; do
  echo "=== $file ==="
  codesitter analyze file "$file" --json | jq -r '.imports[] | "\(.source) -> \(.items | join(", "))"'
  echo
done > import_graph.txt
```

## Comparison with Indexing

| Feature | `codesitter index` | `codesitter analyze` |
|---------|-------------------|---------------------|
| Purpose | Build searchable index | Direct code analysis |
| Storage | Database/JSON files | No storage |
| Chunking | Yes (smart chunks) | No (full files) |
| Speed | Slower (indexing) | Fast (direct) |
| Use Case | Search & retrieval | Quick analysis |

## Benefits

- **Integrated**: Part of the main CLI, no separate tool
- **Fast**: Direct analysis without indexing overhead
- **Flexible**: Multiple output formats and filters
- **Scriptable**: JSON output for automation
- **Complete**: Full file context preserved

## Related Commands

- `codesitter index` - Index codebase for search
- `codesitter search` - Search indexed code
- `codesitter stats` - View index statistics
- `codesitter analyze` - Direct code analysis (this command)
