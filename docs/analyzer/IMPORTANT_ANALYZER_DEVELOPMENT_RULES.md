# CodeSitter Development Rules: Structure & Polymorphism

## Core Principles for Future Development

Based on our established architecture and the lessons learned from implementing `extract_structure()`, here are the rules to follow for future CodeSitter development:

## 1. The Layered Architecture Rule

**Always maintain the separation between syntax and semantics:**

```
Layer 1: Universal/Syntax (Tree-sitter)     →  What the code IS
Layer 2: Language-Specific/Semantics (Ours) →  What the code MEANS
```

### DO:
```python
# Let tree-sitter handle syntax
elements = universal_extractor.extract_all(tree)  # Gets: "there's a function here"

# Add semantic understanding
for element in elements:
    element.metadata["async"] = True  # We understand it's async
    element.metadata["pure"] = is_pure_function(element)  # We analyze behavior
```

### DON'T:
```python
# Don't try to parse syntax yourself
if "async function" in code_text:  # ❌ Fragile string matching
    # ...
```

## 2. The Universal-First Rule

**Start with what's common across languages, then add language-specific features:**

### When adding a new feature:
1. First ask: "Is this universal across languages?"
2. If yes → Add to `UniversalExtractor`
3. If no → Add to language-specific extractor

### Example:
```python
# ✅ Universal: All languages have some form of functions
UNIVERSAL_PATTERNS = {
    'function': ['function_declaration', 'method_definition', 'func', ...]
}

# ✅ Language-specific: Only some languages have decorators
class PythonExtractor(UniversalExtractor):
    def _enrich_function(self, element):
        element.metadata["decorators"] = self._extract_decorators(element)
```

## 3. The Metadata Extension Rule

**Use the metadata dict for language-specific features, not subclassing:**

### DO:
```python
# Add language features via metadata
element.metadata["typescript_generics"] = extract_generics(node)
element.metadata["python_decorators"] = extract_decorators(node)
element.metadata["java_annotations"] = extract_annotations(node)
```

### DON'T:
```python
# Don't create language-specific subclasses
class TypeScriptFunction(ExtractedElement):  # ❌ Leads to inheritance hell
    generics: List[str]
```

## 4. The Progressive Enhancement Rule

**Every language should work at a basic level without specific enhancements:**

### Implementation pattern:
```python
class NewLanguageAnalyzer(LanguageAnalyzer):
    def extract_structure(self, chunk):
        # Step 1: Universal extraction (always works)
        elements = list(self.universal_extractor.extract_all(tree))

        # Step 2: Enhance if we have language knowledge
        if self.has_language_enhancer:
            for element in elements:
                self._enhance_element(element)

        return elements
```

## 5. The Tree-sitter Trust Rule

**Trust tree-sitter for parsing, don't try to outsmart it:**

### DO:
```python
# Use tree-sitter's understanding of the AST
if node.type == "function_declaration":
    # Trust that tree-sitter correctly identified this
```

### DON'T:
```python
# Don't second-guess tree-sitter
if node.type == "function_declaration" and "function" in node.text:  # ❌ Redundant
```

## 6. The Semantic Enhancement Rule

**Language-specific extractors should add meaning, not re-parse syntax:**

### Good Enhancement:
```python
def _enhance_function(self, element, node):
    # ✅ Adding semantic understanding
    element.metadata["is_event_handler"] = (
        element.name.startswith("on") or
        element.name.startswith("handle")
    )
    element.metadata["is_hook"] = element.name.startswith("use")  # React hook
    element.metadata["complexity"] = calculate_cyclomatic_complexity(node)
```

### Bad Enhancement:
```python
def _enhance_function(self, element, node):
    # ❌ Re-parsing what tree-sitter already did
    element.metadata["has_parameters"] = "(" in element.text
```

## 7. The Interface Consistency Rule

**All language analyzers must implement the same interface methods:**

```python
class AnyLanguageAnalyzer(LanguageAnalyzer):
    # Required methods (must work even if minimal)
    def extract_call_relationships(self, chunk) -> Iterator[CallRelationship]
    def extract_import_relationships(self, chunk) -> Iterator[ImportRelationship]
    def extract_structure(self, chunk) -> Iterator[ExtractedElement]
    def extract_custom_metadata(self, chunk) -> Dict[str, Any]

    # Language-specific enhancements go in metadata, not new methods
```

## 8. The Node Type Pattern Matching Rule

**Use tree-sitter node types, not text matching, for identification:**

### DO:
```python
# Map node types to element types
NODE_TYPE_MAPPING = {
    'function_declaration': 'function',
    'class_declaration': 'class',
    'interface_declaration': 'interface'
}

element_type = NODE_TYPE_MAPPING.get(node.type, 'unknown')
```

### DON'T:
```python
# Don't use text matching
if 'class' in code_text:  # ❌ What about "className" or comments?
    element_type = 'class'
```

## 9. The Fail Gracefully Rule

**When language-specific features fail, fall back to universal extraction:**

```python
def extract_structure(self, chunk):
    try:
        # Try enhanced extraction
        return self._enhanced_extraction(chunk)
    except Exception as e:
        logger.warning(f"Enhanced extraction failed: {e}")
        # Fall back to basic universal extraction
        return self._universal_extraction(chunk)
```

## 10. The Clear Boundaries Rule

**Keep clear boundaries between different types of extraction:**

```python
# ✅ Each method has a single, clear purpose
def extract_structure() -> Iterator[ExtractedElement]     # What exists
def extract_call_relationships() -> Iterator[CallRelationship]  # Who calls whom
def extract_import_relationships() -> Iterator[ImportRelationship]  # Dependencies
def extract_custom_metadata() -> Dict[str, Any]  # Boolean flags & counts

# ❌ Don't mix concerns
def extract_everything() -> Dict[str, Any]  # Too broad, unclear
```

## 11. The Documentation Rule

**Document what's universal vs language-specific:**

```python
class ExtractedElement:
    """
    Universal fields (available for all languages):
    - element_type: The kind of element ('function', 'class', etc.)
    - name: The element's name
    - start_line, end_line: Location in source

    Language-specific metadata examples:
    - TypeScript: generics, decorators, type_parameters
    - Python: decorators, async_with, type_hints
    - Java: annotations, modifiers, throws
    """
```

## 12. The Future-Proofing Rule

**Design for languages you haven't implemented yet:**

Ask yourself:
- Would this work for Rust? (Different syntax)
- Would this work for Lisp? (Very different structure)
- Would this work for SQL? (Not even imperative)

If the answer is "no" for the universal layer, reconsider the design.

## Example: Adding a New Language

Following these rules, here's how to add support for a new language:

```python
# 1. Create basic analyzer with universal extraction
class RustAnalyzer(LanguageAnalyzer):
    def __init__(self):
        self._rust_language = get_language("rust")
        self._universal_extractor = UniversalExtractor(self._rust_language)

    def extract_structure(self, chunk):
        # This alone gives basic support!
        tree = parser.parse(chunk.text)
        return self._universal_extractor.extract_all(tree)

# 2. Gradually add Rust-specific enhancements
class RustExtractor(UniversalExtractor):
    def _enrich_element(self, element, node):
        if element.element_type == "function":
            # Add Rust-specific metadata
            element.metadata["unsafe"] = self._is_unsafe_fn(node)
            element.metadata["visibility"] = self._get_visibility(node)
            element.metadata["lifetimes"] = self._extract_lifetimes(node)
```

## Summary

These rules ensure that CodeSitter remains:
- **Extensible**: New languages are easy to add
- **Maintainable**: Clear separation of concerns
- **Robust**: Graceful degradation when features aren't available
- **Consistent**: Same API across all languages
- **Semantic**: We add meaning, not just syntax

The key insight to remember: **Tree-sitter handles syntax, we handle semantics.**
