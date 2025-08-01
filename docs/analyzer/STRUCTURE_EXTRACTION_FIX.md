# Structure Extraction Issue - Fixed

## Problem
When running `codesitter analyze file test_calls.ts --json`, the structure extraction was incomplete. It was only showing a few anonymous variable declarations and missing key elements like:
- The `User` interface
- The `UserService` class and its methods
- Named variables like `createUserService`

## Root Causes

### 1. Container Node Issue
The `UniversalExtractor` was treating `lexical_declaration` as an element type, but it's actually a container node (like `const x = ...`). When the extractor found a `lexical_declaration`, it would:
- Create an element with no name (`<anonymous>`)
- Return early, preventing it from finding the actual `variable_declarator` inside

### 2. Interface Categorization
The `TypeScriptExtractor` was mapping `interface_declaration` to the element type 'type' instead of 'interface', causing confusion in the output.

## Solution

### Fix 1: Remove Container Nodes from Patterns
```python
# Before:
'variable': [
    'variable_declaration',
    'variable_declarator',
    'lexical_declaration',  # This is a container!
    ...
]

# After:
'variable': [
    'variable_declaration',
    'variable_declarator',
    # Don't include lexical_declaration - it's a container
    ...
]
```

### Fix 2: Properly Categorize Interfaces
```python
# Before:
TS_PATTERNS = {
    'type': [
        'type_alias_declaration',
        'interface_declaration',  # Wrong category!
    ],
    ...
}

# After:
TS_PATTERNS = {
    'type': [
        'type_alias_declaration',
    ],
    'interface': [
        'interface_declaration',  # Correct category
    ],
    ...
}
```

### Fix 3: Remove Export Statement from Patterns
`export_statement` is also a container that wraps the actual elements. It was removed from the patterns, and exported elements are detected by checking their parent node.

## Result
After these fixes, `codesitter analyze file test_calls.ts --json` now correctly extracts:
- ✅ Interface: User
- ✅ Class: UserService (with all its methods)
- ✅ Variable: createUserService (properly named)
- ✅ Function: testCalls
- ✅ All with correct export status

## Key Lesson
The issue was distinguishing between **container nodes** (which wrap elements) and **element nodes** (the actual code structures). Container nodes like `lexical_declaration` and `export_statement` should not be treated as elements themselves.
