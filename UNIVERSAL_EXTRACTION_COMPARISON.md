"""
Comparison: Universal Extraction Approach

## Current Approach (analyze.py + TypeScriptAnalyzer)

### What it extracts:
- **Function Calls**: Who calls what (caller -> callee relationships)
- **Imports**: What imports what
- **Metadata**: Boolean flags (has_interfaces, is_react_component, etc.)

### What it DOESN'T extract:
- Function declarations themselves
- Class structures
- Method signatures
- Type information
- Parameter details
- Return types

## Universal Extraction Approach

### Core Benefits:

1. **Complete Structural Information**
   - All functions, classes, interfaces, types, enums
   - Full signatures with parameters and types
   - Nested structures (methods within classes)
   - Export status

2. **Language Agnostic**
   ```python
   # Same extractor works for:
   - TypeScript: function getUser(id: number): Promise<User>
   - Python: def get_user(id: int) -> Optional[User]:
   - Java: public User getUser(int id)
   - Go: func getUser(id int) (*User, error)
   ```

3. **Rich Metadata per Element**
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
     "generics": null,
     "decorators": []
   }
   ```

## Integration Strategy

### Option 1: Replace Current Analyzer
```python
class TypeScriptAnalyzer(LanguageAnalyzer):
    def __init__(self):
        self.extractor = TypeScriptExtractor(get_language("typescript"))

    def extract_structure(self, chunk: CodeChunk) -> List[ExtractedElement]:
        tree = parser.parse(chunk.text)
        return list(self.extractor.extract_all(tree))
```

### Option 2: Add as New Method
```python
class LanguageAnalyzer(ABC):
    # Keep existing methods...

    @abstractmethod
    def extract_structure(self, chunk: CodeChunk) -> Iterator[ExtractedElement]:
        '''Extract all structural elements (functions, classes, etc.)'''
        pass
```

### Option 3: Enrich Existing Metadata
```python
def extract_custom_metadata(self, chunk: CodeChunk) -> Dict[str, Any]:
    tree = parser.parse(chunk.text)
    elements = list(self.extractor.extract_all(tree))

    return {
        'functions': [e for e in elements if e.element_type == 'function'],
        'classes': [e for e in elements if e.element_type == 'class'],
        'interfaces': [e for e in elements if e.element_type == 'interface'],
        # ... existing boolean flags
    }
```

## Query Capabilities

With universal extraction, we can answer:

1. **"Show me all async functions"**
   ```python
   [e for e in elements if e.element_type == 'function' and e.metadata.get('async')]
   ```

2. **"Find functions with optional parameters"**
   ```python
   [e for e in elements
    if e.element_type == 'function'
    and any(p.get('optional') for p in e.metadata.get('parameters', []))]
   ```

3. **"List all exported interfaces"**
   ```python
   [e for e in elements
    if e.element_type == 'interface'
    and e.metadata.get('exported')]
   ```

4. **"Find classes that extend other classes"**
   ```python
   [e for e in elements
    if e.element_type == 'class'
    and e.metadata.get('extends')]
   ```

## Language Support Comparison

### TypeScript (Full Support)
- ✅ Functions, Classes, Interfaces
- ✅ Type annotations
- ✅ Generics
- ✅ Decorators
- ✅ Async/await
- ✅ Optional parameters

### Python (Would work automatically)
- ✅ Functions, Classes
- ✅ Type hints (if present)
- ✅ Decorators
- ✅ Async/await
- ✅ Default parameters
- ⚠️ No interfaces (but has protocols)

### Java (Would work automatically)
- ✅ Methods, Classes, Interfaces
- ✅ Type information (always present)
- ✅ Generics
- ✅ Annotations
- ⚠️ Different async pattern (CompletableFuture)
- ✅ Method overloading

### Go (Would work automatically)
- ✅ Functions, Structs, Interfaces
- ✅ Type information
- ⚠️ No classes (but has methods on structs)
- ⚠️ No generics (in older versions)
- ✅ Multiple return values

## Implementation Path

1. **Phase 1**: Add `extract_structure()` to base analyzer
2. **Phase 2**: Implement universal extractor
3. **Phase 3**: Add TypeScript enrichment
4. **Phase 4**: Update CLI to display structure
5. **Phase 5**: Add other language enrichers as needed
"""
