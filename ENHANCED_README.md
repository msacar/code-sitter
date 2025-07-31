# Enhanced Codesitter: From Boolean Flags to Detailed Code Analysis

## The Problem
Your current implementation only stores boolean metadata:
- `is_react_component: true`
- `has_interfaces: true`

But you want to search for:
- What functions exist?
- What are their parameters and types?
- Which functions call which other functions?
- What's the public API (exported functions)?

## The Solution: Dossier-Inspired Enhanced Analysis

I've implemented enhanced analyzers that extract detailed information similar to [Doctave/dossier](https://github.com/Doctave/dossier):

### What's New
1. **Detailed Function Signatures**
   ```json
   {
     "name": "fetchUserData",
     "parameters": [
       {"name": "userId", "type": "string", "optional": false},
       {"name": "options", "type": "FetchOptions", "optional": true}
     ],
     "returnType": "Promise<User>",
     "isAsync": true,
     "isExport": true
   }
   ```

2. **Interface & Type Definitions**
   ```json
   {
     "kind": "interface",
     "name": "User",
     "isExport": true,
     "line": 10
   }
   ```

3. **Call Relationships** (Your analyzer already has this!)
   ```json
   {
     "caller": "handleLogin",
     "callee": "fetchUserData",
     "arguments": ["user.id", "{ cache: true }"],
     "line": 45
   }
   ```

## Quick Start

### 1. Use the Enhanced Flow
```bash
# Run the new detailed analyzer
cocoindex server /Users/mustafaacar/codesitter/src/codesitter/flows/analyzer_detailed.py -ci --address 0.0.0.0:3000
```

### 2. Try Example Queries
```bash
# Run the example queries script
./examples/enhanced_queries.sh

# Or use the Python client
./examples/enhanced_api_client.py
```

### 3. Example API Calls

**Find functions by name:**
```bash
curl -X POST http://0.0.0.0:3000/cocoindex/query \
  -H "Content-Type: application/json" \
  -d '{
    "flow_name": "DetailedCodeAnalysis",
    "target_name": "code_chunks_detailed",
    "filter": {
      "function_signatures": {"$contains": "\"name\": \"useState\""}
    }
  }'
```

**Find async functions returning Promises:**
```bash
curl -X POST http://0.0.0.0:3000/cocoindex/query \
  -H "Content-Type: application/json" \
  -d '{
    "flow_name": "DetailedCodeAnalysis",
    "target_name": "code_chunks_detailed",
    "filter": {
      "function_signatures": {"$contains": "\"isAsync\": true"},
      "function_signatures": {"$contains": "\"returnType\": \"Promise"}
    }
  }'
```

## Files Created

1. **Enhanced Flow**: `/src/codesitter/flows/analyzer_detailed.py`
   - Extracts function signatures, call relationships, and more

2. **Enhanced TypeScript Analyzer**: `/src/codesitter/analyzers/languages/typescript_enhanced.py`
   - Parses detailed function information using Tree-sitter

3. **API Client Examples**: `/examples/enhanced_api_client.py`
   - Python client showing how to query the enhanced data

4. **Query Examples**: `/examples/enhanced_queries.sh`
   - Shell script with curl examples

5. **Documentation**:
   - `/docs/ENHANCED_ANALYSIS_GUIDE.md` - Full guide
   - `/docs/DOSSIER_IMPLEMENTATION.md` - Implementation details

## Comparison: Old vs New

| Query | Old Way | New Way |
|-------|---------|---------|
| Find async functions | `has_async_functions: true` | List actual async functions with signatures |
| Find React components | `is_react_component: true` | See component names, props, return types |
| Find interfaces | `has_interfaces: true` | Get interface names, export status |
| Find function calls | Not available | See caller, callee, arguments passed |

## Next Steps

1. **Test it**: Run the enhanced analyzer on your codebase
2. **Compare**: See how it compares to Dossier's output
3. **Extend**: Add more language-specific features
4. **Integrate**: Use Dossier as an external tool for deep analysis

The enhanced analyzer gives you powerful search capabilities while staying integrated with CocoIndex's vector search and PostgreSQL storage!
