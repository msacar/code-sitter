# Polymorphism and Language-Specific Features in extract_structure()

## The Challenge

Tree-sitter is a syntax parser, not a semantic analyzer. It understands the structure of code but not its meaning. This creates a polymorphism challenge when building a multi-language code analysis system.

### Example: Generic Types in TypeScript

Consider this TypeScript function:
```typescript
function map<T, U>(items: T[], fn: (item: T) => U): U[] {
    return items.map(fn);
}
```

Tree-sitter will parse this and provide:
- A `function_declaration` node
- A `type_parameters` node containing `<T, U>`
- Parameter nodes with type annotations
- But **no understanding** that `T` and `U` are related generic types

### The Problem Across Languages

Each language has unique features that tree-sitter parses but doesn't understand:

**TypeScript/JavaScript:**
- Generic type parameters and their constraints
- Decorator metadata and their meanings
- Type unions, intersections, and conditionals
- JSX component props and their types

**Python:**
- Type hints (especially complex ones like `Union[Dict[str, Any], None]`)
- Decorator stacking and their combined effects
- Metaclass implications
- Context managers and their protocols

**Java:**
- Generic bounds (`T extends Comparable<T>`)
- Annotation parameters and their compile-time values
- Interface default methods vs abstract methods
- Checked exceptions in method signatures

**Go:**
- Interface satisfaction (implicit implementation)
- Struct embedding and method promotion
- Channel directions (`chan<-` vs `<-chan`)
- Multiple return values and error patterns

## The Solution: Layered Architecture

We solve this with a three-layer approach:

### Layer 1: Universal Structure Extraction (Tree-sitter Layer)
This layer extracts what's common across all languages using tree-sitter's parsing:

```python
class UniversalExtractor:
    def extract_structure(self, tree) -> Iterator[ExtractedElement]:
        # Returns basic elements with:
        # - element_type: "function", "class", etc.
        # - name: "map"
        # - node_type: "function_declaration" (raw tree-sitter type)
        # - location: lines, bytes
        # - text: raw source code
        # - fields: raw tree-sitter fields
```

This gives us:
- ✅ Consistent structure across all languages
- ✅ No language-specific knowledge needed
- ✅ Works with any tree-sitter grammar

But it lacks:
- ❌ Understanding of language semantics
- ❌ Type relationships
- ❌ Language-specific patterns

### Layer 2: Language-Specific Enhancement (Semantic Layer)
Each language analyzer adds its own understanding:

```python
class TypeScriptAnalyzer(LanguageAnalyzer):
    def extract_structure(self, chunk: CodeChunk) -> Iterator[ExtractedElement]:
        # Step 1: Get universal structure
        parser = self._get_parser()
        tree = parser.parse(chunk.text)
        elements = list(self.universal_extractor.extract_all(tree))

        # Step 2: Enhance with TypeScript-specific knowledge
        for element in elements:
            if element.element_type == "function":
                self._enhance_function(element)
            elif element.element_type == "class":
                self._enhance_class(element)

        return elements

    def _enhance_function(self, element: ExtractedElement):
        """Add TypeScript-specific function understanding."""
        # Parse generic parameters and their relationships
        if "<" in element.text and ">" in element.text:
            generics = self._parse_generic_parameters(element)
            element.metadata["generics"] = generics

            # Track where each generic is used
            element.metadata["generic_usage"] = {
                "T": ["parameter:items", "parameter:fn.param"],
                "U": ["parameter:fn.return", "return_type"]
            }

        # Analyze parameter types deeply
        for param in element.metadata.get("parameters", []):
            param["resolved_type"] = self._resolve_type(param["type"])
            param["is_generic"] = self._is_generic_type(param["type"])
```

### Layer 3: Cross-Reference Enhancement (Optional Future Layer)
This layer could add cross-file understanding:
- Resolve imported types
- Track type definitions across files
- Understand inheritance hierarchies
- Build full call graphs

## Implementation Strategy

### ExtractedElement Structure
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

## Benefits of This Approach

1. **Separation of Concerns**
   - Tree-sitter handles parsing
   - Language analyzers handle semantics
   - Clear boundaries between layers

2. **Extensibility**
   - New languages get basic support automatically
   - Language-specific features can be added incrementally
   - No need to modify core extraction logic

3. **Reusability**
   - Universal patterns work across languages
   - Language-specific enhancements are isolated
   - Easy to share common analysis patterns

4. **Type Safety with Flexibility**
   - Strongly typed ExtractedElement structure
   - Flexible metadata dict for language-specific data
   - Best of both worlds

## Example: Handling Complex TypeScript Types

Here's how we'd handle a complex TypeScript type pattern:

```typescript
type Middleware<T extends Request> = (
    req: T,
    res: Response,
    next: (err?: Error) => void
) => Promise<void> | void;
```

1. **Tree-sitter gives us:**
   - A `type_alias_declaration` node
   - Raw text of the type

2. **TypeScript analyzer adds:**
   ```python
   metadata = {
       "kind": "type_alias",
       "generics": {
           "parameters": ["T"],
           "constraints": {"T": "extends Request"}
       },
       "resolved_type": {
           "kind": "function_type",
           "parameters": [
               {"name": "req", "type": "T"},
               {"name": "res", "type": "Response"},
               {"name": "next", "type": "(err?: Error) => void"}
           ],
           "return_type": "Promise<void> | void"
       },
       "is_generic_function_type": True
   }
   ```

This layered approach allows us to leverage tree-sitter's excellent parsing while adding our own semantic understanding on top, solving the polymorphism challenge elegantly.
