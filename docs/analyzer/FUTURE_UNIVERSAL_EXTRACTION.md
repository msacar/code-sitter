# Future Direction: Universal Structure Extraction

## Current State
The analyzer currently extracts:
- **Call relationships**: Who calls what functions
- **Import relationships**: What imports what modules
- **Metadata**: Boolean flags like `has_interfaces`, `is_react_component`

## The Missing Piece
Tree-sitter already parses and identifies all structural elements (functions, classes, methods, interfaces), but we only use this internally to determine caller context. We're not exposing the actual structure!

## Proposed Enhancement: Universal Structure Extraction

### Core Concept
Extract all structural elements using tree-sitter's consistent node types across languages:

```python
UNIVERSAL_PATTERNS = {
    'function': ['function_declaration', 'method_definition', 'func_literal'],
    'class': ['class_declaration', 'struct_item'],
    'interface': ['interface_declaration', 'trait_item'],
    # ... works across TypeScript, Python, Java, Go, Rust, etc.
}
```

### What We'd Get
Instead of just knowing "this file has functions", we'd get:

```json
{
  "type": "function",
  "name": "getUser",
  "async": true,
  "exported": true,
  "parameters": [
    {"name": "id", "type": "number", "optional": false}
  ],
  "return_type": "Promise<User | null>",
  "line": 25
}
```

### Benefits
1. **Multi-language by default** - Universal patterns work across languages
2. **Rich queries** - Find all async functions, exported classes, etc.
3. **Type awareness** - Full parameter and return type information
4. **Foundation for advanced features** - Dependency graphs, refactoring tools

### Implementation Path
1. Add `extract_structure()` method to base analyzer
2. Implement `UniversalExtractor` using tree-sitter node types
3. Add language-specific enrichers (TypeScript types, Python decorators, etc.)
4. Update CLI to display structural elements

See `UNIVERSAL_EXTRACTION_DESIGN.md` and `UNIVERSAL_EXTRACTION_COMPARISON.md` for detailed design.
