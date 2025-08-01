"""
# Side-by-Side Implementation Comparison

## Current State (What we have now)
```python
# In TypeScriptAnalyzer
def extract_custom_metadata(self, chunk: CodeChunk) -> Dict[str, Any]:
    metadata = {}
    if "interface " in chunk.text:
        metadata["has_interfaces"] = True
    if "React" in chunk.text:
        metadata["is_react_component"] = True
    return metadata

# Output:
{
    "metadata": {
        "has_interfaces": true,
        "is_react_component": false
    }
}
```

---

## Option 1: extract_structure() Method

### Implementation
```python
# In base.py
class LanguageAnalyzer(ABC):
    @abstractmethod
    def extract_structure(self, chunk: CodeChunk) -> Iterator[ExtractedElement]:
        """Extract structural elements from the code."""
        pass

# In typescript.py
class TypeScriptAnalyzer(LanguageAnalyzer):
    def __init__(self):
        self.extractor = TypeScriptExtractor(get_language("typescript"))

    def extract_structure(self, chunk: CodeChunk) -> Iterator[ExtractedElement]:
        parser = create_parser(self._ts_language)
        tree = parser.parse(bytes(chunk.text, "utf8"))
        yield from self.extractor.extract_all(tree)

    def extract_custom_metadata(self, chunk: CodeChunk) -> Dict[str, Any]:
        # Keep existing simple metadata
        metadata = {}
        if "interface " in chunk.text:
            metadata["has_interfaces"] = True
        if "React" in chunk.text:
            metadata["is_react_component"] = True
        return metadata

# In analyze.py
def file(file_path: str, output_json: bool):
    # ... existing code ...

    # Extract everything
    result["calls"] = list(analyzer.extract_call_relationships(chunk))
    result["imports"] = list(analyzer.extract_import_relationships(chunk))
    result["metadata"] = analyzer.extract_custom_metadata(chunk)
    result["structure"] = [
        {
            "type": elem.element_type,
            "name": elem.name,
            "line": elem.start_line,
            "details": elem.metadata
        }
        for elem in analyzer.extract_structure(chunk)
    ]
```

### Output Structure
```json
{
    "calls": [...],
    "imports": [...],
    "metadata": {
        "has_interfaces": true,
        "is_react_component": false
    },
    "structure": [
        {
            "type": "function",
            "name": "getUser",
            "line": 10,
            "details": {
                "async": true,
                "parameters": [{"name": "id", "type": "number"}],
                "return_type": "Promise<User>"
            }
        },
        {
            "type": "interface",
            "name": "User",
            "line": 5,
            "details": {
                "exported": true
            }
        }
    ]
}
```

---

## Option 2: Enriched extract_custom_metadata()

### Implementation
```python
# In typescript.py
class TypeScriptAnalyzer(LanguageAnalyzer):
    def __init__(self):
        self.extractor = TypeScriptExtractor(get_language("typescript"))

    def extract_custom_metadata(self, chunk: CodeChunk) -> Dict[str, Any]:
        # Parse once
        parser = create_parser(self._ts_language)
        tree = parser.parse(bytes(chunk.text, "utf8"))

        # Extract structure
        elements = list(self.extractor.extract_all(tree))

        # Build metadata with both flags and structure
        metadata = {
            # Keep existing flags
            "has_interfaces": any(e.element_type == "interface" for e in elements),
            "is_react_component": "React" in chunk.text and any(
                e.element_type == "function" for e in elements
            ),

            # Add structural data
            "functions": [
                {
                    "name": e.name,
                    "line": e.start_line,
                    "async": e.metadata.get("async", False),
                    "parameters": e.metadata.get("parameters", []),
                    "return_type": e.metadata.get("return_type")
                }
                for e in elements if e.element_type == "function"
            ],
            "classes": [
                {
                    "name": e.name,
                    "line": e.start_line,
                    "extends": e.metadata.get("extends"),
                    "methods": len(e.children)
                }
                for e in elements if e.element_type == "class"
            ],
            "interfaces": [
                {
                    "name": e.name,
                    "line": e.start_line,
                    "exported": e.metadata.get("exported", False)
                }
                for e in elements if e.element_type == "interface"
            ]
        }

        return metadata

# In analyze.py - NO CHANGES NEEDED
def file(file_path: str, output_json: bool):
    # ... existing code remains exactly the same ...
    result["metadata"] = analyzer.extract_custom_metadata(chunk)
```

### Output Structure
```json
{
    "calls": [...],
    "imports": [...],
    "metadata": {
        "has_interfaces": true,
        "is_react_component": false,
        "functions": [
            {
                "name": "getUser",
                "line": 10,
                "async": true,
                "parameters": [{"name": "id", "type": "number"}],
                "return_type": "Promise<User>"
            }
        ],
        "classes": [],
        "interfaces": [
            {
                "name": "User",
                "line": 5,
                "exported": true
            }
        ]
    }
}
```

---

## Migration Path Comparison

### For extract_structure():
```python
# Step 1: Add method with default implementation
class LanguageAnalyzer(ABC):
    def extract_structure(self, chunk: CodeChunk) -> Iterator[ExtractedElement]:
        """Default: no structure extraction."""
        return []

# Step 2: Implement for each analyzer gradually
# TypeScript first, then Python, Java, etc.

# Step 3: Update CLI to display structure
# Old analyzers still work, just return empty structure
```

### For Enriched Metadata:
```python
# Step 1: Update each analyzer's metadata method
# RISKY: Need to ensure we don't break existing consumers

# Step 2: Check all places that use metadata
# Make sure they handle new keys properly

# Step 3: Update documentation about metadata schema
# Need to maintain backward compatibility
```

---

## Usage in Different Scenarios

### Scenario 1: User only wants call relationships
```python
# With extract_structure()
calls = analyzer.extract_call_relationships(chunk)  # ✅ Efficient

# With enriched metadata
metadata = analyzer.extract_custom_metadata(chunk)  # ❌ Computes everything
# But user only wanted calls, wasted computation on structure
```

### Scenario 2: Building a code map
```python
# With extract_structure()
structure = analyzer.extract_structure(chunk)  # ✅ Clear intent
for elem in structure:
    graph.add_node(elem.name, type=elem.element_type)

# With enriched metadata
metadata = analyzer.extract_custom_metadata(chunk)
# ❌ Need to know schema and iterate multiple lists
for func in metadata.get("functions", []):
    graph.add_node(func["name"], type="function")
for cls in metadata.get("classes", []):
    graph.add_node(cls["name"], type="class")
# ... repeat for each type
```

### Scenario 3: Simple boolean check
```python
# With extract_structure()
metadata = analyzer.extract_custom_metadata(chunk)
if metadata["has_interfaces"]:  # ✅ Still simple
    process_typescript_file()

# With enriched metadata
metadata = analyzer.extract_custom_metadata(chunk)
if metadata["has_interfaces"]:  # ✅ Works the same
    process_typescript_file()
# But we computed unnecessary structure data
```
"""
