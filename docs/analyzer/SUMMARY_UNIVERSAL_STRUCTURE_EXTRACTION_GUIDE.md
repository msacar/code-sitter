# Universal Structure Extraction Guide

This document details the design, benefits, and implementation strategy for Universal Structure Extraction within `codesitter`'s analyzer.

## The Core Insight

Tree-sitter already parses and identifies all structural elements (functions, classes, methods, interfaces), but the current analyzer only uses this data internally to determine caller context. We are missing out on exposing this rich structural information directly.

## Proposed Enhancement: Universal Structure Extraction

### Core Concept

Extract all structural elements using tree-sitter's consistent node types across languages. This approach leverages universal patterns that work across many languages, such as:

- `function_declaration`, `method_definition`, `arrow_function` → Functions
- `class_declaration`, `class_expression`, `struct_item` → Classes/Structs
- `interface_declaration`, `trait_item` → Interfaces
- `variable_declaration`, `variable_declarator`, `lexical_declaration` → Variables
- `import_statement`, `import_declaration` → Imports
- `export_statement`, `export_declaration` → Exports

These patterns are surprisingly consistent across tree-sitter grammars.

### What We'd Get

Instead of just knowing "this file has functions", we'd get detailed, structured information for each element:

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

### Benefits of This Approach

1.  **Multi-language by Default**: Add a new language, and you automatically get basic structure extraction.
2.  **Rich Queries**: Find all async functions, exported classes, methods with specific parameters, etc.
3.  **Type Awareness**: Full parameter and return type information (with language-specific enrichment).
4.  **Foundation for Advanced Features**: Enables dependency graphs, refactoring tools, and more.
5.  **Leverages Tree-sitter's Strengths**: We use what tree-sitter does best – parsing structure.
6.  **Maximum Detail**: Extracts all available information from the AST.
7.  **Progressive Enhancement**: Start with universal patterns, then add language-specific features.

## Polymorphism and Language-Specific Features

Tree-sitter is a syntax parser, not a semantic analyzer. It understands the structure of code but not its meaning. This creates a polymorphism challenge when building a multi-language code analysis system. Each language has unique features that tree-sitter parses but doesn't inherently understand (e.g., TypeScript generics, Python decorators, Java annotations, Go interface satisfaction).

### The Solution: Layered Architecture

We solve this with a three-layer approach:

#### Layer 1: Universal Structure Extraction (Tree-sitter Layer)

This layer extracts what's common across all languages using tree-sitter's parsing. It provides basic elements with `element_type`, `name`, `node_type`, `location`, `text`, and raw tree-sitter `fields`.

#### Layer 2: Language-Specific Enhancement (Semantic Layer)

Each language analyzer adds its own understanding. For example, a `TypeScriptAnalyzer` would enhance a function element by parsing generic parameters, resolving types, and adding decorator metadata.

#### Layer 3: Cross-Reference Enhancement (Optional Future Layer)

This layer would add cross-file understanding, such as resolving imported types, tracking type definitions across files, and building full call graphs.

### `ExtractedElement` Structure

```python
@dataclass
class ExtractedElement:
    # Universal fields (from tree-sitter)
    element_type: str  # 'function', 'class', etc.
    name: str
    node_type: str  # Raw tree-sitter node type
    start_line: int
    end_line: int
    text: str
    fields: Dict[str, Any]  # Raw tree-sitter fields

    # Enhanced fields (from language analyzers)
    metadata: Dict[str, Any]  # Language-specific enhancements
    children: List['ExtractedElement']  # Nested elements
```

### Metadata Examples by Language

**TypeScript Function:**
```python
metadata = {
    "async": True,
    "exported": True,
    "generics": {
        "parameters": ["T", "U"],
        "constraints": {"T": "extends Record<string, any>"}
    },
    "parameters": [
        {
            "name": "items",
            "type": "T[]",
            "resolved_type": "Array<generic:T>",
            "is_generic": True,
            "optional": False
        }
    ],
    "return_type": "Promise<U[]>",
    "decorators": ["@memoize", "@deprecated"]
}
```

**Python Function:**
```python
metadata = {
    "async": True,
    "decorators": ["@staticmethod", "@lru_cache(maxsize=128)"],
    "type_hints": {
        "parameters": {"user_id": "int", "options": "Optional[Dict[str, Any]]"},
        "return": "Union[User, None]"
    },
    "docstring": "Fetch user by ID with caching.",
    "is_generator": False,
    "raises": ["UserNotFoundError", "DatabaseError"]
}
```

**Java Method:**
```python
metadata = {
    "access_modifier": "public",
    "static": False,
    "final": True,
    "generics": {
        "parameters": ["T"],
        "bounds": {"T": "extends Comparable<T>"}
    },
    "annotations": [
        {"name": "@Override"},
        {"name": "@SuppressWarnings", "value": "unchecked"}
    ],
    "throws": ["IOException", "SQLException"],
    "synchronized": False
}
```

## Proposed Implementation Details

### Universal Node Patterns

#### DECLARATION PATTERNS:
- `function_declaration`
- `class_declaration`
- `method_definition`
- `variable_declaration` / `variable_declarator`
- `interface_declaration` (TS, Java, etc.)
- `enum_declaration`
- `module_declaration`

#### COMMON FIELDS (available via `node.field_name_for_child`):
- `name`: The identifier of the declaration
- `parameters`: Function/method parameters
- `body`: The implementation
- `type`: Type annotations
- `value`: Initial values

### Language-Specific Enrichments (TypeScript Example)

#### TypeScript Specific Node Types:
- `type_alias_declaration` (`type Foo = ...`)
- `interface_declaration`
- `enum_declaration`
- `namespace_declaration`
- `ambient_declaration` (`declare ...`)
- `decorator` (`@ annotations`)
- `type_parameter` (generics `<T>`)
- `type_annotation` (`: Type`)
- `as_expression` (type assertions)
- `satisfies_expression`
- `readonly_type`
- `optional_parameter`
- `rest_parameter`

#### TypeScript Type Nodes:
- `union_type` (`A | B`)
- `intersection_type` (`A & B`)
- `generic_type` (`Array<T>`)
- `function_type` (`() => void`)
- `object_type` (`{ x: number }`)
- `literal_type` (`"foo" | 123`)
- `template_literal_type`
- `conditional_type` (`T extends U ? X : Y`)
- `infer_type`
- `type_predicate` (`x is Type`)

### Example Implementation Snippets

```python
class UniversalExtractor:
    '''Base extractor using universal patterns'''

    UNIVERSAL_PATTERNS = {
        'functions': ['function_declaration', 'method_definition', 'arrow_function'],
        'classes': ['class_declaration', 'class_expression'],
        'interfaces': ['interface_declaration'],
        'variables': ['variable_declaration', 'variable_declarator', 'lexical_declaration'],
        'imports': ['import_statement', 'import_declaration'],
        'exports': ['export_statement', 'export_declaration'],
    }

    def extract_element(self, node):
        '''Extract common fields that exist across languages'''
        element = {
            'type': node.type,
            'name': self.get_name(node),
            'range': {
                'start_line': node.start_point[0],
                'end_line': node.end_point[0],
                'start_byte': node.start_byte,
                'end_byte': node.end_byte
            },
            'text': node.text.decode('utf-8'),
            'fields': {}
        }

        # Extract all available fields
        for i, child in enumerate(node.named_children):
            field_name = node.field_name_for_named_child(i)
            if field_name:
                element['fields'][field_name] = {
                    'type': child.type,
                    'text': child.text.decode('utf-8')
                }

        return element

class TypeScriptEnricher(UniversalExtractor):
    '''Add TypeScript-specific extraction'''

    TS_SPECIFIC_PATTERNS = {
        'types': ['type_alias_declaration', 'type_parameter'],
        'enums': ['enum_declaration'],
        'namespaces': ['namespace_declaration', 'module_declaration'],
        'decorators': ['decorator'],
    }

    def enrich_function(self, element, node):
        '''Add TypeScript-specific function details'''
        # Extract parameter types
        params = []
        param_list = self.find_child_by_type(node, 'formal_parameters')
        if param_list:
            for param in param_list.named_children:
                param_info = {
                    'name': self.get_name(param),
                    'optional': self.find_child_by_type(param, 'optional_parameter') is not None,
                    'type': None,
                    'default': None
                }

                # Get type annotation
                type_ann = self.find_child_by_field(param, 'type')
                if type_ann:
                    param_info['type'] = type_ann.text.decode('utf-8')

                # Get default value
                default = self.find_child_by_field(param, 'value')
                if default:
                    param_info['default'] = default.text.decode('utf-8')

                params.append(param_info)

        element['parameters'] = params

        # Extract return type
        return_type = self.find_child_by_field(node, 'return_type')
        if return_type:
            element['return_type'] = return_type.text.decode('utf-8')

        # Check if async
        element['async'] = node.text.decode('utf-8').strip().startswith('async ')

        # Extract generics
        type_params = self.find_child_by_type(node, 'type_parameters')
        if type_params:
            element['generics'] = type_params.text.decode('utf-8')

        return element
```

## Proposed `codesitter analyze` Output with Structure Extraction

When universal structure extraction is implemented, the `codesitter analyze` output will be significantly richer, providing a dedicated section for structural elements.

### Pretty Output Example

```
$ codesitter analyze file src/services/userService.ts

═══════════════════════════════════════════════════════════════════════════════
Analysis: src/services/userService.ts
Language: typescript | Analyzer: TypeScriptAnalyzer
═══════════════════════════════════════════════════════════════════════════════

📦 Imports (3):
  react → useState, useEffect (line 1)
  ./types → User, UserRole (line 2)
  ./api → fetchUser (line 3)

🏗️ Structure (5 elements):

  📘 Interface: User (lines 5-9)
    Fields: id: number, name: string, email?: string
    Exported: ✓

  📘 Type: UserRole (line 11)
    Definition: 'admin' | 'user' | 'guest'
    Exported: ✓

  🔧 Function: getUser (lines 13-17)
    async ✓ | exported ✓
    Parameters: (id: number, options?: FetchOptions)
    Returns: Promise<User | null>

  🔧 Function: validateUser (lines 19-21)
    arrow function ✓ | exported ✓
    Parameters: (user: User)
    Returns: boolean

  🏛️ Class: UserService (lines 23-45)
    exported ✓
    Methods: 3
      - constructor(db: Database)
      - async addUser(user: User): Promise<void>
      - findUser(id: number): User | undefined

📞 Function Calls (8):
  constructor → super() at line 25
  addUser → this.db.save(user) at line 30
  findUser → this.users.find(callback) at line 35
  ... and 5 more

📊 Metadata:
  has_interfaces: ✓
  has_type_aliases: ✓
  has_async_functions: ✓
  is_test_file: ✗

═══════════════════════════════════════════════════════════════════════════════
```

### JSON Output Example (`--json` flag)

```json
{
  "file": "src/services/userService.ts",
  "structure": [
    {
      "type": "interface",
      "name": "User",
      "lines": "5-9",
      "exported": true,
      "fields": [
        {"name": "id", "type": "number", "optional": false},
        {"name": "name", "type": "string", "optional": false},
        {"name": "email", "type": "string", "optional": true}
      ]
    },
    {
      "type": "function",
      "name": "getUser",
      "lines": "13-17",
      "async": true,
      "exported": true,
      "parameters": [
        {"name": "id", "type": "number", "optional": false},
        {"name": "options", "type": "FetchOptions", "optional": true}
      ],
      "return_type": "Promise<User | null>"
    }
  ],
  "imports": [...],
  "calls": [...],
  "metadata": {...}
}
```

## Integration Strategy

### Option 1: Replace Current Analyzer
This involves modifying the `TypeScriptAnalyzer` (and other language analyzers) to directly use the new `UniversalExtractor` and its language-specific enrichers to return `ExtractedElement` objects.

### Option 2: Add as New Method
Introduce a new abstract method `extract_structure()` to the `LanguageAnalyzer` interface, which would be implemented by each language-specific analyzer to return an iterator of `ExtractedElement` objects.

### Option 3: Enrich Existing Metadata
Modify `extract_custom_metadata()` to include the structured elements directly within the metadata dictionary, categorized by type (e.g., `functions`, `classes`, `interfaces`).

## Query Capabilities

With universal extraction, we can answer complex queries:

1.  **"Show me all async functions"**
    ```python
    [e for e in elements if e.element_type == 'function' and e.metadata.get('async')]
    ```

2.  **"Find functions with optional parameters"**
    ```python
    [e for e in elements
     if e.element_type == 'function'
     and any(p.get('optional') for p in e.metadata.get('parameters', []))]
    ```

3.  **"List all exported interfaces"**
    ```python
    [e for e in elements
     if e.element_type == 'interface'
     and e.metadata.get('exported')]
    ```

4.  **"Find classes that extend other classes"**
    ```python
    [e for e in elements
     if e.element_type == 'class'
     and e.metadata.get('extends')]
    ```

## Language Support Comparison

The universal extraction approach provides a strong foundation for detailed analysis across various languages:

### TypeScript (Full Support)
-   ✅ Functions, Classes, Interfaces, Types, Enums
-   ✅ Type annotations, Generics, Decorators
-   ✅ Async/await, Optional parameters

### Python (Would work automatically)
-   ✅ Functions, Classes
-   ✅ Type hints (if present), Decorators
-   ✅ Async/await, Default parameters
-   ⚠️ No interfaces (but has protocols)

### Java (Would work automatically)
-   ✅ Methods, Classes, Interfaces
-   ✅ Type information, Generics, Annotations
-   ⚠️ Different async pattern (CompletableFuture)
-   ✅ Method overloading

### Go (Would work automatically)
-   ✅ Functions, Structs, Interfaces
-   ✅ Type information
-   ⚠️ No classes (but has methods on structs)
-   ⚠️ No generics (in older versions)
-   ✅ Multiple return values

## Implementation Path

1.  **Phase 1**: Add `extract_structure()` to base analyzer.
2.  **Phase 2**: Implement universal extractor.
3.  **Phase 3**: Add TypeScript enrichment.
4.  **Phase 4**: Update CLI to display structure.
5.  **Phase 5**: Add other language enrichers as needed.
