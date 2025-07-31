# Implementing Dossier-like Features in Codesitter

## Summary

Yes, you can apply Dossier's TypeScript parsing features to your project! Here's how:

## Current State vs Enhanced State

### What You Have Now
- Boolean metadata: `is_react_component`, `has_interfaces`, etc.
- Basic call extraction (caller/callee/arguments) - **but not being used**
- Tree-sitter infrastructure already in place

### What Dossier Provides
- Detailed function signatures with parameter names and types
- Return type information
- Interface and type alias definitions
- JSDoc/TSDoc parsing
- Cross-file type resolution

## Implementation Options

### Option 1: Direct Dossier Integration (Simplest)
Install Dossier and call it from your analyzer:

```bash
cargo install dossier
```

Then in your flow:
```python
@op.function()
def analyze_with_dossier(filename: str) -> str:
    """Run dossier and return JSON output."""
    result = subprocess.run(['dossier', filename], capture_output=True, text=True)
    return result.stdout
```

### Option 2: Enhanced Tree-sitter Analysis (Already Implemented)
I've created enhanced analyzers that extract:
- Function signatures with parameters and types
- Return types
- Async/export status
- Interfaces and type aliases

Files created:
- `/src/codesitter/flows/analyzer_detailed.py` - New flow with detailed extraction
- `/src/codesitter/analyzers/languages/typescript_enhanced.py` - Enhanced TypeScript analyzer
- `/examples/enhanced_api_client.py` - Example API queries

### Option 3: Hybrid Approach (Recommended)
1. Use your existing Tree-sitter for fast extraction
2. Call Dossier for deep type analysis when needed
3. Store both in PostgreSQL for powerful queries

## Quick Start

1. **Using the enhanced analyzer:**
```bash
# Setup database
export USE_POSTGRES=true
export COCOINDEX_DATABASE_URL="postgresql://cocoindex:cocoindex@localhost:5432/cocoindex"

# Run the enhanced flow
cocoindex setup /Users/mustafaacar/codesitter/src/codesitter/flows/analyzer_detailed.py
cocoindex server /Users/mustafaacar/codesitter/src/codesitter/flows/analyzer_detailed.py -ci --address 0.0.0.0:3000
```

2. **Query for detailed function info:**
```bash
# Find all async functions
curl -X POST http://0.0.0.0:3000/cocoindex/query \
  -H "Content-Type: application/json" \
  -d '{
    "flow_name": "DetailedCodeAnalysis",
    "target_name": "code_chunks_detailed",
    "filter": {
      "function_signatures": {"$contains": "\"isAsync\": true"}
    }
  }'

# Find functions with specific parameter types
curl -X POST http://0.0.0.0:3000/cocoindex/query \
  -H "Content-Type: application/json" \
  -d '{
    "flow_name": "DetailedCodeAnalysis",
    "target_name": "code_chunks_detailed",
    "filter": {
      "function_signatures": {"$contains": "\"type\": \"string\""}
    }
  }'
```

## What You Can Now Search For

With the enhanced implementation:
- ✅ Functions by name, parameters, return type
- ✅ Async functions
- ✅ Exported vs internal functions
- ✅ Functions with specific parameter counts
- ✅ Interfaces and type aliases
- ✅ Functions with JSDoc comments
- ✅ Call relationships with full context

## Example Queries

```python
# Using the enhanced API client
from enhanced_api_client import EnhancedCodeAnalysisAPI

api = EnhancedCodeAnalysisAPI()

# Find all Promise-returning functions
promises = api.find_functions_returning_type("Promise")

# Find exported APIs
public_api = api.find_exported_apis()

# Analyze file complexity
analysis = api.analyze_function_complexity("src/components/Auth.tsx")
```

## Next Steps

1. **Test the enhanced analyzer** with your TypeScript codebase
2. **Compare results** with Dossier's output
3. **Adjust queries** based on your specific needs
4. **Consider adding** GraphQL API for more flexible queries

The enhanced analyzer gives you 80% of Dossier's functionality while staying integrated with CocoIndex's vector search and PostgreSQL storage. You get the best of both worlds!
