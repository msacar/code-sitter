# Exports and Symbols Extraction in CodeSitter

## Current State

CodeSitter **already has full support** for extracting exports and symbols from code files. This functionality is implemented through the `extract_structure()` method that was added to the `LanguageAnalyzer` interface.

## What's Already Implemented

### 1. **ExtractedElement Data Structure** (base.py)
```python
@dataclass
class ExtractedElement:
    element_type: str  # 'function', 'class', 'interface', etc.
    name: str
    node_type: str  # Raw tree-sitter node type
    start_line: int
    end_line: int
    start_byte: int
    end_byte: int
    text: str
    fields: Dict[str, Any]  # Raw tree-sitter fields
    metadata: Dict[str, Any]  # Language-specific enrichments
    children: List['ExtractedElement']  # Nested elements
```

### 2. **Universal Extraction Pattern** (universal_extractor.py)
The `UniversalExtractor` class provides language-agnostic extraction for common patterns:
- Functions, classes, interfaces
- Variables, types, enums
- Import and export statements

### 3. **TypeScript-Specific Enhancements** (TypeScriptExtractor)
For TypeScript/JavaScript files, the extractor adds:
- Export status detection (`metadata['exported'] = True/False`)
- Parameter types and optionality
- Return types
- Async function detection
- Generic type parameters
- Decorators
- Variable kinds (const/let/var)

### 4. **CLI Integration** (analyze.py)
The analyze command displays structure with:
- Icons for different element types
- Export status indicators
- Parameter and return type information
- Nested element display (methods within classes)

## Example Output

When running `codesitter analyze file test_exports_symbols.ts`:

```
🏗️  Structure (15 elements):
  📦 Variable: API_VERSION (lines 4-4)
     exported | const
  📦 Variable: currentUser (lines 5-5)
     exported | let
  📘 Interface: User (lines 8-12)
     exported
  📐 Type: UserRole (line 14)
     exported
  🏛️ Class: UserService (lines 17-31)
     exported
     Children: 3 elements
       - function: constructor
       - function: getUser
       - function: addUser
  🎯 Enum: UserStatus (lines 67-71)
     exported
  ...
```

## How Exports Are Detected

The TypeScript extractor checks for exports by examining the parent node:
```python
# Check if exported
parent = node.parent
if parent and parent.type == 'export_statement':
    metadata['exported'] = True
```

## Available Data for Each Symbol

1. **Basic Information**:
   - Element type (function, class, interface, etc.)
   - Name
   - Location (line numbers, byte positions)
   - Full text of the element

2. **Export Status**:
   - `metadata['exported']`: true/false

3. **Type Information** (for functions):
   - Parameters with types and optionality
   - Return types
   - Generic type parameters

4. **Additional Metadata**:
   - Async status
   - Variable kind (const/let/var)
   - Decorators
   - Abstract classes
   - Extends/implements relationships

## Usage Examples

### CLI Usage
```bash
# Analyze a file and see all symbols with export status
codesitter analyze file myfile.ts

# Get JSON output for programmatic use
codesitter analyze file myfile.ts --json
```

### Programmatic Usage
```python
from codesitter.analyzers.languages.typescript import TypeScriptAnalyzer
from codesitter.analyzers.base import CodeChunk

analyzer = TypeScriptAnalyzer()
chunk = CodeChunk(text=code, filename="test.ts", ...)

# Get all structural elements
elements = list(analyzer.extract_structure(chunk))

# Filter exported symbols
exported = [e for e in elements if e.metadata.get('exported')]

# Filter by type
functions = [e for e in elements if e.element_type == 'function']
```

## Integration with Search and Indexing

The extracted structure data can be:
1. Indexed for fast symbol search
2. Used to build dependency graphs
3. Queried to find specific patterns
4. Used for code navigation and documentation

## Summary

The exports and symbols extraction functionality is **fully implemented** in CodeSitter:
- ✅ Extracts all structural elements (functions, classes, interfaces, types, etc.)
- ✅ Tracks export status for each symbol
- ✅ Captures rich metadata (types, parameters, async status, etc.)
- ✅ Supports nested structures
- ✅ Available through both CLI and programmatic interfaces
- ✅ Integrated with the analyze command output

This provides a solid foundation for building advanced features like:
- Symbol search
- Dependency analysis
- Export tracking
- Code navigation
- Documentation generation
