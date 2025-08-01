# Comprehensive Guide to `codesitter analyze`

The `codesitter analyze` command provides a powerful, integrated, and standalone tool for direct code analysis. It works on local files without requiring a pre-built index, making it fast and ideal for scripting and CI/CD pipelines.

## Core Commands

### List Available Analyzers
To see all registered analyzers and their capabilities:
```bash
codesitter analyze list
```

### Analyze a Single File
Analyze a single source file and view the output in a human-readable format or as JSON.

```bash
# Pretty-printed output for easy reading
codesitter analyze file src/auth.ts

# JSON output for scripting and automation
codesitter analyze file src/auth.ts --json
```

### Analyze a Directory
Analyze all supported files within a directory, with options to filter by file extension.

```bash
# Analyze all supported files in the src directory
codesitter analyze directory ./src

# Analyze only TypeScript files
codesitter analyze directory ./src --ext .ts

# Get a JSON report for the entire directory, including statistics
codesitter analyze directory ./src --json
```

## Output Formats

The analyzer offers two primary output formats:

### Pretty Output (Default)
Designed for humans, this format provides a clean, readable summary of the analysis.

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

### JSON Output (`--json`)
Ideal for scripting, automation, and integration with other tools. The output is a structured JSON object.

```json
{
  "file": "src/auth.ts",
  "language": "typescript",
  "analyzer": "TypeScriptAnalyzer",
  "imports": [
    { "source": "@middy/core", "items": ["middy"], "type": "named", "line": 1 }
  ],
  "calls": [
    { "caller": "authMiddleware", "callee": "ApiError", "line": 28 }
  ],
  "metadata": {
    "has_functions": true,
    "is_react_component": false
  }
}
```
*Note: The output always includes all available information (imports, calls, metadata). For filtering, pipe the JSON output to tools like `jq`.*

## Scripting & Automation Examples

### Find All React Components
```bash
codesitter analyze directory ./src --ext .tsx --json | jq '.files[] | select(.metadata.is_react_component)'
```

### Extract All External Dependencies
```bash
# Get all unique, non-relative import sources
codesitter analyze directory ./src --json | \
  jq -r '.files[].imports[].source' | \
  grep -v "^\." | \
  sort | uniq
```

### Generate an Import Graph
```bash
# Create a simple import dependency list for all TypeScript files
for file in $(find src -name "*.ts"); do
  echo "=== $file ==="
  codesitter analyze file "$file" --json | jq -r '.imports[] | "\(.source) -> \(.items | join(\", \"))"'
  echo
done > import_graph.txt
```

### CI/CD Integration
Use the exit code to fail a pipeline if certain patterns are detected.
```bash
# Check for specific patterns like "unsafe_call"
if codesitter analyze file src/api.ts --json | grep -q "unsafe_call"; then
  echo "Found unsafe API calls!"
  exit 1
fi
```

## Comparison with `codesitter index`

| Feature          | `codesitter index`      | `codesitter analyze`   |
|------------------|-------------------------|------------------------|
| **Purpose**      | Build searchable index  | Direct code analysis   |
| **Storage**      | Database / JSON files   | No storage             |
| **Context**      | Smart chunks            | Full files             |
| **Speed**        | Slower (indexing)       | Fast (direct analysis) |
| **Primary Use**  | Semantic search         | Quick analysis, linting, scripting |

## Benefits

- ✅ **Integrated**: A core part of the `codesitter` CLI.
- ✅ **Standalone**: No dependency on an index, chunking, or a database.
- ✅ **Fast**: Direct, in-memory analysis provides immediate results.
- ✅ **Flexible**: Multiple output formats (human-readable and JSON) and filters.
- ✅ **Scriptable**: Designed for easy integration into scripts and CI/CD pipelines.
- ✅ **Complete**: Analysis is performed on full files, preserving complete context.
