# Code-Sitter Architecture

## Overview

Code-Sitter uses a **pluggable analyzer architecture** that allows different programming languages to have custom analysis capabilities while sharing a common indexing infrastructure.

## Architecture Components

### 1. Core Components

```
code-sitter/
├── analyzers/              # Language analyzer system
│   ├── base.py            # Base classes and interfaces
│   ├── registry.py        # Analyzer registration and discovery
│   └── languages/         # Language-specific implementations
│       ├── typescript.py  # TypeScript/JavaScript analyzer
│       ├── python.py      # Python analyzer
│       └── java.py        # Java analyzer (example)
├── flexible_flow.py       # Main flow using analyzer system
├── query.py              # Search engine
└── cli.py                # Command-line interface
```

### 2. Language Analyzer Interface

Every language analyzer implements the `LanguageAnalyzer` abstract base class:

```python
class LanguageAnalyzer(ABC):
    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """File extensions this analyzer handles"""

    @property
    @abstractmethod
    def language_name(self) -> str:
        """Language name for Tree-sitter"""

    @abstractmethod
    def extract_call_relationships(self, chunk: CodeChunk) -> Iterator[CallRelationship]:
        """Extract function calls (optional)"""

    def extract_import_relationships(self, chunk: CodeChunk) -> Iterator[ImportRelationship]:
        """Extract imports/dependencies (optional)"""

    def extract_custom_metadata(self, chunk: CodeChunk) -> Dict[str, Any]:
        """Extract language-specific metadata (optional)"""
```

### 3. Analyzer Capabilities by Language

| Language | Call Extraction | Import Extraction | Custom Metadata | Tree-sitter AST |
|----------|----------------|-------------------|-----------------|-----------------|
| TypeScript/JS | ✅ Full AST | ✅ ES6/CommonJS | ✅ React, Types | ✅ Yes |
| Python | ✅ Full AST | ✅ import/from | ✅ Decorators | ✅ Yes |
| Java | ❌ Basic only | ✅ Regex-based | ✅ Annotations | ❌ No |
| Go | ❌ Default | ❌ Default | ❌ Default | ❌ No |
| Ruby | ❌ Default | ❌ Default | ❌ Default | ❌ No |

### 4. Adding a New Language

#### Option 1: Use Default Analyzer (No Custom Logic)

Languages that don't need special analysis automatically get:
- Syntax-aware chunking from CocoIndex
- Basic symbol extraction
- Vector embeddings for semantic search

No code needed! The language is registered in `registry.py`:

```python
DefaultAnalyzer([".go"], "go"),
DefaultAnalyzer([".rs"], "rust"),
```

#### Option 2: Create Custom Analyzer

Create a new file in `analyzers/languages/`:

```python
# analyzers/languages/mylang.py
from ..base import LanguageAnalyzer, CodeChunk, CallRelationship

class MyLangAnalyzer(LanguageAnalyzer):
    @property
    def supported_extensions(self) -> List[str]:
        return [".ml", ".mli"]

    @property
    def language_name(self) -> str:
        return "mylang"

    def extract_call_relationships(self, chunk: CodeChunk) -> Iterator[CallRelationship]:
        # Custom logic here
        pass
```

The analyzer will be **auto-discovered** on startup!

## Data Flow

1. **File Discovery**: CocoIndex finds all supported files
2. **Language Detection**: Registry maps file → analyzer
3. **Chunking**: CocoIndex splits files into syntax-aware chunks
4. **Analysis**: Language analyzer extracts relationships and metadata
5. **Embedding**: Generate vector embeddings for semantic search
6. **Storage**: Save to PostgreSQL or JSON files

```
File → Analyzer Selection → Chunking → Analysis → Embedding → Storage
         ↓                              ↓
   (TypeScript)                  (Call extraction,
   (Python)                       Import tracking,
   (Default)                      Custom metadata)
```

## Benefits of This Architecture

### 1. **Flexibility**
- Each language can have custom analysis
- Languages can opt-in to only what they need
- Easy to add new languages

### 2. **Maintainability**
- Language logic is isolated in separate modules
- Common functionality is shared
- Clear interfaces and contracts

### 3. **Performance**
- Only run expensive AST parsing when needed
- Languages can use simple regex when sufficient
- Default analyzer has minimal overhead

### 4. **Extensibility**
- New analysis types can be added to the interface
- Third-party analyzers can be plugged in
- Community can contribute language support

## Storage Schema

### Code Chunks Table
```sql
CREATE TABLE code_chunks (
    filename TEXT,
    chunk_index INTEGER,
    chunk_text TEXT,
    start_line INTEGER,
    end_line INTEGER,
    node_type TEXT,
    symbols TEXT[],
    embedding VECTOR(384),
    language TEXT,
    custom_metadata JSONB
);
```

### Call Relationships Table
```sql
CREATE TABLE call_relationships (
    filename TEXT,
    chunk_index INTEGER,
    caller TEXT,
    callee TEXT,
    arguments TEXT[],
    line INTEGER,
    column INTEGER,
    context TEXT,
    language TEXT
);
```

### Import Relationships Table
```sql
CREATE TABLE import_relationships (
    filename TEXT,
    chunk_index INTEGER,
    imported_from TEXT,
    imported_items TEXT[],
    import_type TEXT,
    line INTEGER,
    language TEXT
);
```

## Query Capabilities

The search engine (`query.py`) can now:

1. **Language-aware search**: Filter by language
2. **Cross-language analysis**: Find where Python calls JavaScript
3. **Import tracking**: Understand dependencies across languages
4. **Custom metadata search**: Find React components, Python decorators, etc.

## Future Enhancements

1. **More Language Analyzers**
   - C/C++ with full AST support
   - Go with interface tracking
   - Rust with trait implementations

2. **Advanced Analysis**
   - Type inference and tracking
   - Data flow analysis
   - Security vulnerability detection

3. **Cross-Language Features**
   - FFI boundary detection
   - API compatibility checking
   - Multi-language refactoring

4. **Performance Optimizations**
   - Parallel analysis
   - Incremental AST updates
   - Caching parsed trees
