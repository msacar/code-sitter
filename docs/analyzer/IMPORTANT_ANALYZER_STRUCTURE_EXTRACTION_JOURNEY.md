# CodeSitter Structure Extraction: Design Journey and Implementation

## Executive Summary

This document captures the complete journey of designing and implementing the `extract_structure()` feature for CodeSitter, including our brainstorming process, design decisions, polymorphism handling, and the final layered architecture.

## The Initial Problem

We started with a simple observation: When running `codesitter analyze file test_file.ts`, we were getting function calls and imports, but not the actual functions, classes, and methods themselves - even though tree-sitter was already parsing and identifying all these structural elements.

## Brainstorming Phase

### Initial Realization
Tree-sitter already parses and finds functions, classes, and methods. The TypeScript analyzer had a `_function_query` that extracts function declarations, but this data was only being used internally to determine the "caller" context for function calls. It wasn't exposed in the output!

### The Core Problem
The `LanguageAnalyzer` base class only had methods for:
- `extract_call_relationships()` - who calls what
- `extract_import_relationships()` - what imports what
- `extract_custom_metadata()` - boolean flags

There was no method to extract **structural elements** like functions, classes, methods, interfaces, etc.

### Options Considered

1. **Extend the Base Analyzer Interface**: Add new methods like `extract_symbols()`
2. **Enrich the Metadata**: Make `extract_custom_metadata()` return actual data instead of just booleans
3. **Leverage the Existing `symbols` Field**: The `CodeChunk` already had an unused `symbols` field
4. **Create a More Generic Query System**: Make analyzers configurable with custom queries

## Key Design Decision: extract_structure() vs Enriched Metadata

### The Comparison Process

We did a detailed comparison between two approaches:

#### Option 1: Add `extract_structure()` Method
**Pros:**
- ✅ Clean separation of concerns
- ✅ Type-safe with ExtractedElement objects
- ✅ Backward compatible
- ✅ Performance: compute only when needed
- ✅ Easy to test independently

**Cons:**
- ❌ One more method to implement
- ❌ Potential duplicate parsing

#### Option 2: Enrich `extract_custom_metadata()`
**Pros:**
- ✅ No API changes needed
- ✅ Single parse operation
- ✅ Flexible - just add keys

**Cons:**
- ❌ Type safety lost (Dict[str, Any])
- ❌ Mixes different concerns
- ❌ Always computes everything
- ❌ Risk breaking existing code

### Decision Criteria

1. **Clean Architecture** - Single Responsibility Principle
2. **Type Safety** - Strongly typed returns prevent bugs
3. **Performance** - Only compute what you need
4. **Future Extensibility** - Easy to add more extraction methods
5. **Testing** - Each aspect should be testable independently

### The Decision

We chose **Option 1: Add `extract_structure()`** because:
- CodeSitter is building a multi-language system where clean abstractions matter
- Performance is important when indexing large codebases
- Different use cases (some users want structure, others just want calls)
- Growth potential (easy to add `extract_types()`, `extract_dependencies()`, etc.)
- Better testing - each extraction type can be tested independently

## The Polymorphism Challenge

### The Core Issue

Tree-sitter is a syntax parser, not a semantic analyzer. It understands the structure of code but not its meaning.

**Example:**
```typescript
function map<T, U>(items: T[], fn: (item: T) => U): U[] { ... }
```

Tree-sitter will:
- ✅ Parse this and provide nodes
- ✅ Identify a `type_parameters` node containing `<T, U>`
- ❌ NOT understand that `T` and `U` are related generic types

### Language-Specific Challenges

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

**Benefits:**
- ✅ Consistent structure across all languages
- ✅ No language-specific knowledge needed
- ✅ Works with any tree-sitter grammar

**Limitations:**
- ❌ No understanding of language semantics
- ❌ No type relationships
- ❌ No language-specific patterns

### Layer 2: Language-Specific Enhancement (Semantic Layer)

Each language analyzer adds its own understanding:

```python
class TypeScriptAnalyzer(LanguageAnalyzer):
    def extract_structure(self, chunk: CodeChunk) -> Iterator[ExtractedElement]:
        # Step 1: Get universal structure
        elements = list(self.universal_extractor.extract_all(tree))

        # Step 2: Enhance with TypeScript-specific knowledge
        for element in elements:
            if element.element_type == "function":
                # Parse generic parameters and their relationships
                element.metadata["generics"] = self._parse_generics(element)
                # Track type relationships
                element.metadata["generic_usage"] = {
                    "T": ["parameter:items", "parameter:fn.param"],
                    "U": ["parameter:fn.return", "return_type"]
                }
```

### The Key Insight

The `ExtractedElement` structure has:
- **Universal fields**: name, type, location (from tree-sitter)
- **metadata dict**: for language-specific enrichments (our analysis)

This separation allows:
1. Tree-sitter to handle the parsing (what it does best)
2. Each language to add its own semantic understanding
3. New languages to get basic support automatically
4. Language-specific features to be added incrementally

## Implementation Details

### Data Structure

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

### Universal Patterns

We identified patterns that work across many languages:

```python
UNIVERSAL_PATTERNS = {
    'function': [
        'function_declaration',
        'function_definition',
        'method_definition',
        'method_declaration',
        'function_item',  # Rust
        'func_literal',   # Go
    ],
    'class': [
        'class_declaration',
        'class_definition',
        'class_specifier',  # C++
        'struct_item',      # Rust
    ],
    # ... more patterns
}
```

### TypeScript Enhancement Example

For the generics example:

1. **Tree-sitter provides**: "There's a `type_parameters` node here with text `<T, U>`"
2. **Our enhancement adds**: "T and U are generic parameters, T is used in the array type, U is the return type of the function parameter"

## Benefits of Our Approach

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

## Key Decisions and Rationale

### 1. Why Not Just Use Tree-sitter Queries?
While tree-sitter queries are powerful, they:
- Can't understand semantic relationships
- Are syntax-focused, not semantics-focused
- Would require massive duplication across languages

### 2. Why Separate Universal and Language-Specific?
- Allows incremental development
- New languages work immediately (with basic features)
- Easier to maintain and test
- Follows the principle of progressive enhancement

### 3. Why Use a Metadata Dict Instead of Subclassing?
- Avoids complex inheritance hierarchies
- Allows dynamic addition of properties
- Easier to serialize/deserialize
- More flexible for future extensions

## Implementation Journey

1. **Added `extract_structure()` to base interface** - with default empty implementation
2. **Created `UniversalExtractor`** - language-agnostic extraction
3. **Created `TypeScriptExtractor`** - TypeScript-specific enhancements
4. **Integrated into `TypeScriptAnalyzer`** - connected the pieces
5. **Updated CLI** - added beautiful display with icons and structure
6. **Fixed circular imports** - moved `ExtractedElement` to base.py
7. **Added proper defaults** - using dataclass field factories

## Results

### Before
```
📊 Metadata:
  has_interfaces: ✓
  has_type_aliases: ✓
  has_async_functions: ✓
```

### After
```
🏗️  Structure (7 elements):
  📘 Interface: User (lines 5-9)
     exported
  🔧 Function: getUser (lines 18-21)
     async | exported
     Parameters: (id: number)
     Returns: Promise<User | null>
  🏛️ Class: UserService (lines 27-40)
     Children: 3 elements
       - function: constructor
       - function: addUser
       - function: findUser
```

## Lessons Learned

1. **Start with the simplest solution that could work** - We could have over-engineered with complex type systems, but the metadata dict approach proved flexible and sufficient.

2. **Leverage existing tools** - Tree-sitter does the heavy lifting; we just add intelligence on top.

3. **Design for extensibility** - The layered approach makes it easy to add new languages and features.

4. **Type safety matters** - Using `ExtractedElement` instead of raw dicts caught bugs early.

5. **Clean architecture pays off** - The separation between structure extraction and other concerns makes the code easier to understand and maintain.

## Future Opportunities

1. **Extract interface/type bodies** - Currently we just note they exist
2. **Extract decorators** - Important for Python and TypeScript
3. **Cross-file analysis** - Resolve types across files
4. **Build dependency graphs** - Using the structural information
5. **Add more language extractors** - Python, Java, Go, etc.

## Conclusion

By carefully considering our options, choosing clean architecture over quick fixes, and building a layered system that leverages tree-sitter's strengths while adding our own semantic understanding, we created a flexible, extensible system for extracting code structure across multiple languages. The polymorphism challenge was solved not by fighting against language differences, but by embracing them through a universal base with language-specific enhancements.
