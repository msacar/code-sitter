"""
# Comparison: extract_structure() vs Enriched extract_custom_metadata()

## Option 1: Add extract_structure() Method

### Implementation
```python
class LanguageAnalyzer(ABC):
    # Existing methods remain unchanged
    def extract_call_relationships(self, chunk: CodeChunk) -> Iterator[CallRelationship]:
        pass

    def extract_import_relationships(self, chunk: CodeChunk) -> Iterator[ImportRelationship]:
        pass

    def extract_custom_metadata(self, chunk: CodeChunk) -> Dict[str, Any]:
        # Still returns boolean flags
        return {"has_interfaces": True, "is_react_component": False}

    # NEW METHOD
    @abstractmethod
    def extract_structure(self, chunk: CodeChunk) -> Iterator[ExtractedElement]:
        """Extract structural elements (functions, classes, etc.)"""
        pass
```

### Usage in analyze.py
```python
# In analyze command
result = {
    "calls": list(analyzer.extract_call_relationships(chunk)),
    "imports": list(analyzer.extract_import_relationships(chunk)),
    "metadata": analyzer.extract_custom_metadata(chunk),
    "structure": list(analyzer.extract_structure(chunk))  # NEW
}
```

### Pros
1. **Clean Separation of Concerns**
   - Structure extraction is conceptually different from metadata flags
   - Each method has a single, clear responsibility

2. **Type Safety**
   - Returns `Iterator[ExtractedElement]` - strongly typed
   - No mixing of different data types in one dict

3. **Backward Compatible**
   - Existing code using `extract_custom_metadata()` continues to work
   - No breaking changes to current API

4. **Easier to Test**
   - Can test structure extraction independently
   - Clear contract for what each method should return

5. **Performance Control**
   - Can choose to skip structure extraction if not needed
   - Lazy evaluation with iterators

### Cons
1. **More Methods to Implement**
   - Every analyzer needs to implement another method
   - More boilerplate for simple analyzers

2. **Potential Duplication**
   - Might parse the same AST multiple times
   - Structure and metadata might have overlapping logic

3. **API Surface Growth**
   - More methods = more complexity
   - Need to document and maintain another method

---

## Option 2: Enrich extract_custom_metadata()

### Implementation
```python
class LanguageAnalyzer(ABC):
    # Existing methods remain unchanged
    def extract_call_relationships(self, chunk: CodeChunk) -> Iterator[CallRelationship]:
        pass

    def extract_import_relationships(self, chunk: CodeChunk) -> Iterator[ImportRelationship]:
        pass

    # MODIFIED METHOD - now returns rich data
    def extract_custom_metadata(self, chunk: CodeChunk) -> Dict[str, Any]:
        return {
            # Keep boolean flags for compatibility
            "has_interfaces": True,
            "is_react_component": False,

            # NEW: Add structural elements
            "functions": [
                {
                    "name": "getUser",
                    "async": True,
                    "parameters": [...],
                    "return_type": "Promise<User>"
                }
            ],
            "classes": [...],
            "interfaces": [...],
            "types": [...]
        }
```

### Usage in analyze.py
```python
# In analyze command - no changes needed!
result = {
    "calls": list(analyzer.extract_call_relationships(chunk)),
    "imports": list(analyzer.extract_import_relationships(chunk)),
    "metadata": analyzer.extract_custom_metadata(chunk)  # Now includes structure
}

# Access structure via metadata
functions = result["metadata"].get("functions", [])
```

### Pros
1. **No API Changes**
   - Works with existing code
   - No new methods to implement

2. **Single Parse**
   - Can extract everything in one AST traversal
   - More efficient, no duplication

3. **Flexible Schema**
   - Can add new fields without changing method signature
   - Easy to extend with more data types

4. **Simpler for Basic Analyzers**
   - Can return empty lists if no structure support
   - Gradual enhancement possible

### Cons
1. **Type Safety Issues**
   - Returns `Dict[str, Any]` - not strongly typed
   - Mix of booleans, lists, and complex objects

2. **Backward Compatibility Risk**
   - Existing code might break if it expects only booleans
   - Need careful key naming to avoid conflicts

3. **Unclear Semantics**
   - "metadata" now means both flags AND structure
   - Method name doesn't reflect its true purpose

4. **Potential Performance Impact**
   - Always extracts everything even if not needed
   - Can't opt-out of expensive structure extraction

---

## Comparison Matrix

| Aspect | extract_structure() | Enriched metadata |
|--------|-------------------|-------------------|
| **Type Safety** | ✅ Strong (ExtractedElement) | ⚠️ Weak (Dict[str, Any]) |
| **Backward Compatibility** | ✅ Full | ⚠️ Risky |
| **Performance** | ✅ On-demand | ❌ Always runs |
| **Implementation Effort** | ❌ New method | ✅ Modify existing |
| **API Clarity** | ✅ Clear purpose | ❌ Mixed concerns |
| **Testing** | ✅ Isolated | ⚠️ Complex |
| **Extensibility** | ✅ Add more methods | ✅ Add more keys |

---

## Real-World Usage Examples

### With extract_structure()
```python
# Clear what we're getting
structure = analyzer.extract_structure(chunk)
for element in structure:
    if element.element_type == "function" and element.metadata.get("async"):
        print(f"Async function: {element.name}")

# Can skip if not needed
if user_wants_structure:
    result["structure"] = list(analyzer.extract_structure(chunk))
```

### With Enriched Metadata
```python
# Need to know the schema
metadata = analyzer.extract_custom_metadata(chunk)
functions = metadata.get("functions", [])  # Defensive coding
for func in functions:
    if func.get("async"):  # More defensive coding
        print(f"Async function: {func.get('name', 'unknown')}")

# Always computed even if not used
metadata = analyzer.extract_custom_metadata(chunk)  # Extracts everything
user_only_wanted_boolean_flags = metadata["has_interfaces"]
```

---

## Hybrid Approach (Best of Both?)

```python
class LanguageAnalyzer(ABC):
    def extract_custom_metadata(self, chunk: CodeChunk) -> Dict[str, Any]:
        """Extract simple metadata flags."""
        return {"has_interfaces": True}  # Keep it simple

    def extract_structure(self, chunk: CodeChunk) -> Iterator[ExtractedElement]:
        """Extract structural elements. Default returns empty."""
        return []  # Not abstract, has default implementation

    def extract_all(self, chunk: CodeChunk) -> Dict[str, Any]:
        """Convenience method that combines everything."""
        return {
            "calls": list(self.extract_call_relationships(chunk)),
            "imports": list(self.extract_import_relationships(chunk)),
            "metadata": self.extract_custom_metadata(chunk),
            "structure": list(self.extract_structure(chunk))
        }
```

---

## Recommendation

**I recommend Option 1: Add extract_structure()**

Reasons:
1. **Clean Architecture**: Each method has one clear responsibility
2. **Type Safety**: Strongly typed returns prevent bugs
3. **Future Proof**: Easy to add more extraction methods later
4. **Performance**: Only compute what you need
5. **Testing**: Easier to test each aspect independently

The only downside is more methods to implement, but we can provide a default implementation that returns an empty list for analyzers that don't support structure extraction.
"""
