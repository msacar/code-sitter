# Code-Sitter: Pluggable Multi-Language Code Intelligence

Code-Sitter delivers a real‑time, syntax‑aware indexing and retrieval system for codebases across multiple programming languages. Built with a **pluggable analyzer architecture**, it leverages Tree‑sitter for precise parsing and CocoIndex's Python SDK for incremental chunking, embedding, and storage. This enables fast lookup of code symbols, functions, call‑site details, and cross-language dependencies while staying in sync with live code changes.

## ✨ Key Features

- **🔌 Pluggable Language Support**: Each language can have custom analyzers or use defaults
- **🚀 Real-time Indexing**: Watch mode for instant updates as code changes
- **🔍 Multiple Search Types**: Symbol, semantic, call-site, and definition search
- **🌐 Multi-Language**: TypeScript, JavaScript, Python, Java, and easily extensible
- **📊 Advanced Analysis**: Function calls, imports, language-specific metadata
- **💾 Flexible Storage**: JSON files or PostgreSQL with pgvector

## 🏗️ Architecture

Code-Sitter uses a modular architecture where each programming language can optionally provide:

```
Language → Analyzer → Extracted Data
   ↓          ↓            ↓
TypeScript → Full AST → Calls, Imports, React Components
Python → Full AST → Calls, Imports, Decorators
Java → Basic → Imports, Annotations
Go → Default → Basic chunking only
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed information.

## 🚀 Quick Start

### Installation

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate

# Install all dependencies from pyproject.toml
uv pip install -e .
```

### Basic Usage

```bash
# Index a multi-language project
code-sitter index --path /path/to/project

# Search across languages
code-sitter search "database connection" --type semantic
code-sitter search "useState" --type symbol
code-sitter search "processData" --type calls

# Watch for changes
code-sitter index --watch

# View statistics
code-sitter stats
```

See [docs/QUICKSTART.md](docs/QUICKSTART.md) for more detailed getting started instructions.

## 🔧 Language Support

### Built-in Analyzers

| Language | Extensions | Features |
|----------|------------|----------|
| TypeScript/JavaScript | `.ts`, `.tsx`, `.js`, `.jsx` | Full AST analysis, call extraction, imports, React detection |
| Python | `.py`, `.pyw` | Full AST analysis, call extraction, imports, decorators |
| Java | `.java` | Import extraction, annotations |

### Default Support

These languages get basic syntax-aware chunking without custom analysis:

- C/C++ (`.c`, `.cpp`, `.cc`, `.h`, `.hpp`)
- Go (`.go`)
- Rust (`.rs`)
- Ruby (`.rb`)
- PHP (`.php`)
- Swift (`.swift`)
- Kotlin (`.kt`)
- And more...

### Adding a New Language

Create a file in `codesitter/analyzers/languages/`:

```python
from ..base import LanguageAnalyzer, CodeChunk, CallRelationship

class MyLanguageAnalyzer(LanguageAnalyzer):
    @property
    def supported_extensions(self) -> List[str]:
        return [".mylang"]

    @property
    def language_name(self) -> str:
        return "mylang"

    def extract_call_relationships(self, chunk: CodeChunk) -> Iterator[CallRelationship]:
        # Your custom logic here
        pass
```

The analyzer will be auto-discovered on startup! See [docs/ADDING_LANGUAGES.md](docs/ADDING_LANGUAGES.md) for a complete guide.

## 📊 Search Capabilities

### 1. Symbol Search
Find functions, classes, and variables by name:
```bash
code-sitter search "UserController" --type symbol
```

### 2. Semantic Search
Use natural language to find relevant code:
```bash
code-sitter search "code that handles user authentication" --type semantic
```

### 3. Call Site Analysis
Find where functions are called:
```bash
code-sitter search "validateUser" --type calls
```

### 4. Definition Lookup
Jump to function definitions:
```bash
code-sitter search "handleSubmit" --type definition
```

### 5. Dependency Analysis
Analyze file imports and exports:
```bash
code-sitter analyze src/components/Button.tsx
```

## 💾 Storage Options

### JSON Files (Default)
Simple setup for development:
- `code_index.json` - Main index with chunks and embeddings
- `symbol_index.json` - Symbol to location mapping
- `call_relationships.json` - Function call graph
- `import_relationships.json` - Import dependencies

### PostgreSQL with pgvector
For production and large codebases:
```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/code_index"
export USE_POSTGRES=true
code-sitter index
```

## 🛠️ Programmatic Usage

```python
from codesitter.query import CodeSearchEngine

# Initialize search engine
engine = CodeSearchEngine()

# Search for symbols
results = engine.search_symbol("useState")

# Semantic search
results = engine.semantic_search("database connection logic", k=5)

# Find function calls
calls = engine.find_function_calls("fetchData")

# Analyze dependencies
deps = engine.analyze_dependencies("src/app.ts")

engine.close()
```

## 📚 Documentation

- [docs/QUICKSTART.md](docs/QUICKSTART.md) - Detailed getting started guide
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) - Development setup and project structure
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design and architecture
- [docs/ADDING_LANGUAGES.md](docs/ADDING_LANGUAGES.md) - Guide for adding new language support
- [docs/PROJECT_DESCRIPTION.md](docs/PROJECT_DESCRIPTION.md) - Original project planning
- [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md) - Advanced features and call-site extraction

## 📁 Project Structure

```
code-sitter/
├── codesitter/          # Main package (src layout)
│   ├── __init__.py
│   ├── __main__.py           # Module entry point
│   ├── cli/                  # CLI interface
│   │   ├── __init__.py       # Main CLI group
│   │   ├── commands/         # Individual commands
│   │   │   ├── index.py
│   │   │   ├── search.py
│   │   │   ├── stats.py
│   │   │   └── analyze.py
│   │   ├── config.py         # CLI configuration
│   │   └── utils.py          # Display helpers
│   ├── query.py              # Search engine
│   ├── flows/                # CocoIndex flow definitions
│   │   ├── __init__.py
│   │   ├── basic.py          # Basic minimal flow
│   │   ├── simple.py         # Simple multi-language flow (default)
│   │   ├── enhanced.py       # Enhanced flow with call extraction
│   │   └── flexible.py       # Advanced flow with pluggable analyzers
│   └── analyzers/            # Language analyzer system
│       ├── __init__.py
│       ├── base.py           # Base classes and interfaces
│       ├── registry.py       # Analyzer registration
│       └── languages/        # Language implementations
│           ├── __init__.py
│           ├── python.py
│           ├── typescript.py
│           └── java.py
├── scripts/                  # Example scripts
│   └── example.py           # Usage examples
├── tests/                   # Test suite
│   ├── test_analyzers.py
│   └── test_cli.py
├── docs/                    # Documentation
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your language analyzer in `codesitter/analyzers/languages/`
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- [Tree-sitter](https://tree-sitter.github.io/tree-sitter/) for syntax parsing
- [CocoIndex](https://cocoindex.io/) for incremental indexing
- [pgvector](https://github.com/pgvector/pgvector) for vector search
