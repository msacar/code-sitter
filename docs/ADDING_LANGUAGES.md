# Adding Custom Language Analyzers

This guide explains how to add support for new programming languages to Code-Sitter.

## Overview

Code-Sitter uses a pluggable architecture where each language can have its own analyzer. Languages without custom analyzers automatically get basic syntax-aware chunking from CocoIndex.

## Quick Example: Adding Ruby Support

### 1. Create the Analyzer File

Create `codesitter/analyzers/languages/ruby.py`:

```python
from typing import Iterator, List, Dict, Any
from ..base import LanguageAnalyzer, CodeChunk, CallRelationship, ImportRelationship

class RubyAnalyzer(LanguageAnalyzer):
    @property
    def supported_extensions(self) -> List[str]:
        return [".rb", ".rake", ".gemspec"]

    @property
    def language_name(self) -> str:
        return "ruby"

    def extract_call_relationships(self, chunk: CodeChunk) -> Iterator[CallRelationship]:
        # Ruby doesn't need complex call extraction for now
        return []

    def extract_import_relationships(self, chunk: CodeChunk) -> Iterator[ImportRelationship]:
        import re

        # Match require statements
        require_pattern = r"require\s+['\"]([^'\"]+)['\"]"

        for match in re.finditer(require_pattern, chunk.text):
            module_name = match.group(1)

            yield ImportRelationship(
                filename=chunk.filename,
                imported_from=module_name,
                imported_items=[module_name],
                import_type="require",
                line=chunk.text[:match.start()].count('\n') + chunk.start_line
            )
```

### 2. That's It!

The analyzer will be auto-discovered when Code-Sitter starts. No registration needed!

## Advanced Example: Adding Go Support with AST

For languages where you want full AST analysis:

### 1. Install Tree-sitter Grammar

```bash
pip install tree-sitter-go
```

### 2. Create Advanced Analyzer

```python
# codesitter/analyzers/languages/go.py
from tree_sitter import Language, Parser, Query
import tree_sitter_go as ts_go
from ..base import LanguageAnalyzer, CodeChunk, CallRelationship

class GoAnalyzer(LanguageAnalyzer):
    def __init__(self):
        self._language = Language(ts_go.language(), "go")

        self._call_query = """
        (call_expression
          function: (identifier) @callee
          arguments: (argument_list) @args
        ) @call
        """

    @property
    def supported_extensions(self) -> List[str]:
        return [".go"]

    @property
    def language_name(self) -> str:
        return "go"

    def extract_call_relationships(self, chunk: CodeChunk) -> Iterator[CallRelationship]:
        parser = Parser()
        parser.set_language(self._language)
        tree = parser.parse(bytes(chunk.text, "utf8"))

        query = Query(self._language, self._call_query)
        captures = query.captures(tree.root_node)

        # Process captures...
```

## Available Methods to Override

### Required Methods

- `supported_extensions()` - File extensions to handle
- `language_name()` - Language identifier for Tree-sitter
- `extract_call_relationships()` - Extract function calls

### Optional Methods

- `extract_import_relationships()` - Extract imports/requires
- `extract_custom_metadata()` - Language-specific metadata
- `should_analyze_chunk()` - Filter chunks before analysis
- `preprocess_chunk()` - Transform chunks before analysis

## Language-Specific Metadata Examples

### React Components (TypeScript)
```python
def extract_custom_metadata(self, chunk: CodeChunk) -> Dict[str, Any]:
    if "React" in chunk.text and "return" in chunk.text and "<" in chunk.text:
        return {"is_react_component": True}
```

### Test Detection (Python)
```python
def extract_custom_metadata(self, chunk: CodeChunk) -> Dict[str, Any]:
    if any(p in chunk.text for p in ["def test_", "pytest", "unittest"]):
        return {"is_test_file": True}
```

### Annotations (Java)
```python
def extract_custom_metadata(self, chunk: CodeChunk) -> Dict[str, Any]:
    annotations = re.findall(r'@([A-Z][a-zA-Z0-9]*)', chunk.text)
    if annotations:
        return {"annotations": list(set(annotations))}
```

## Best Practices

1. **Start Simple**: Use regex for basic extraction before implementing full AST
2. **Handle Errors**: Wrap parsing in try-except blocks
3. **Be Selective**: Use `should_analyze_chunk()` to skip irrelevant chunks
4. **Document Features**: List what your analyzer extracts in docstrings
5. **Test Thoroughly**: Add test files in multiple styles of the language

## Testing Your Analyzer

```python
# test_my_analyzer.py
from codesitter.analyzers.languages.mylang import MyLangAnalyzer
from codesitter.analyzers.base import CodeChunk

def test_import_extraction():
    analyzer = MyLangAnalyzer()
    chunk = CodeChunk(
        text='import foo from "bar"',
        filename="test.mylang",
        start_line=1,
        end_line=1,
        node_type="module",
        symbols=[]
    )

    imports = list(analyzer.extract_import_relationships(chunk))
    assert len(imports) == 1
    assert imports[0].imported_from == "bar"
```

## Common Patterns

### Import/Require Patterns

```python
# Python
import_pattern = r'(?:from\s+(\S+)\s+)?import\s+(\S+)'

# JavaScript/TypeScript
import_pattern = r'import\s+.*?\s+from\s+["\']([^"\']+)["\']'

# Ruby
require_pattern = r'require\s+["\']([^"\']+)["\']'

# Go
import_pattern = r'import\s+(?:\(\s*)?["]([^"]+)["]'
```

### Function Definition Patterns

```python
# Python
func_pattern = r'def\s+(\w+)\s*\('

# JavaScript
func_pattern = r'function\s+(\w+)\s*\('

# Go
func_pattern = r'func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\('
```

## Debugging Tips

1. **Enable Debug Logging**:
```python
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
```

2. **Print AST Structure**:
```python
def debug_ast(self, chunk: CodeChunk):
    tree = parser.parse(bytes(chunk.text, "utf8"))
    print(tree.root_node.sexp())
```

3. **Test with Small Examples**:
```bash
echo 'print("hello")' | code-sitter index --debug
```

## Contributing Your Analyzer

1. Fork the repository
2. Create your analyzer in `codesitter/analyzers/languages/`
3. Add tests
4. Update the language support table in README
5. Submit a pull request

Your analyzer will help the community analyze codebases in your favorite language!
