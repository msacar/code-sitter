# Function Call Association Enhancement

## Overview

The `codesitter analyze` command has been enhanced to associate function calls with their containing functions in the structure output. This provides better context about which functions call which other functions.

## What Changed

The analyze command now:
1. Maintains the top-level `calls` array for backward compatibility
2. Groups calls by their containing function
3. Adds a `calls` array to each function's metadata in the structure output

## Example

Given this TypeScript code:
```typescript
function sayHello(id: number) {
  const user = getUser(id);
  console.log(user?.name.toLowerCase());
  return user?.name.toString();
}

function getUser(id: number) {
  return users.find(u => u.id === id);
}
```

The JSON output now includes calls within each function's metadata:
```json
{
  "structure": [
    {
      "type": "function",
      "name": "sayHello",
      "metadata": {
        "calls": [
          {
            "caller": "sayHello",
            "callee": "getUser",
            "arguments": ["id"],
            "line": 7
          },
          {
            "caller": "sayHello",
            "callee": "toLowerCase",
            "arguments": [],
            "line": 8
          },
          {
            "caller": "sayHello",
            "callee": "toString",
            "arguments": [],
            "line": 9
          }
        ]
      }
    }
  ]
}
```

## Benefits

1. **Better Context**: You can see at a glance what each function calls
2. **Easier Analysis**: No need to cross-reference between the calls array and structure
3. **Backward Compatible**: The top-level calls array remains unchanged

## Usage

```bash
# JSON output with associated calls
codesitter analyze file myfile.ts --json

# Human-readable output (also shows calls)
codesitter analyze file myfile.ts
```

## Implementation Details

This enhancement follows the codesitter architecture principles:
- **Tree-sitter handles syntax**: Identifies function calls and their locations
- **We add semantic understanding**: Associate calls with their containing functions
- **Metadata for enhancements**: Function calls are added to the metadata dict

The implementation is done at the CLI layer (analyze.py) without modifying the core analyzers, maintaining clean separation of concerns.
