# Code-Sitter Quick Start Guide

## 🚀 Getting Started

### Why uv?

Code-Sitter uses [`uv`](https://github.com/astral-sh/uv) for dependency management because it's:
- **Fast**: 10-100x faster than pip for dependency installation
- **Reliable**: Consistent lockfile format ensures reproducible builds
- **Modern**: Built-in support for PEP 517/518 and pyproject.toml
- **Simple**: Single tool for virtual environments and package management

### 1. Setup Python Environment

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install all dependencies from pyproject.toml
uv pip install -e .
```

### 2. Configure Environment (Optional)

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env if you want to use PostgreSQL
# Otherwise, it will use JSON file storage by default
```

## 📖 Usage Examples

### Understanding the Different Flows

Code-Sitter provides four different indexing flows, each with different capabilities:

1. **`simple` (default)** - Reliable multi-language indexing
   - ✅ Supports 20+ languages out of the box
   - ✅ Syntax-aware chunking for all languages
   - ✅ No complex dependencies or imports
   - ✅ Works reliably with CocoIndex
   - ❌ No advanced analysis (call extraction, imports)

2. **`basic`** - Minimal single-file indexing
   - ✅ Very simple and fast
   - ✅ Good for quick tests
   - ❌ Limited language support
   - ❌ No advanced features

3. **`enhanced`** - JavaScript/TypeScript focused with call extraction
   - ✅ Extracts function calls and relationships
   - ✅ Advanced AST analysis for JS/TS
   - ✅ Builds call graphs
   - ❌ Only supports JavaScript/TypeScript family

4. **`flexible`** - Advanced pluggable analyzer system
   - ✅ Language-specific analyzers
   - ✅ Extensible architecture
   - ✅ Most advanced analysis capabilities
   - ⚠️  May have import issues in some environments
   - ⚠️  More complex setup

For most users, the `simple` flow (default) provides the best balance of features and reliability.

### Basic Indexing

```bash
# Index current directory (uses simple multi-language flow by default)
code-sitter index

# Index a specific TypeScript project
code-sitter index --path /path/to/typescript/project

# Use basic flow (minimal, single file output)
code-sitter index --flow basic

# Use simple flow (multi-language support, reliable - default)
code-sitter index --flow simple

# Use enhanced flow (with call-site extraction for JS/TS)
code-sitter index --flow enhanced

# Use flexible flow (with pluggable language analyzers - advanced)
code-sitter index --flow flexible

# Watch for changes (real-time indexing)
code-sitter index --watch
```

### Searching Code

```bash
# Symbol search
code-sitter search "useState" --type symbol

# Semantic search
code-sitter search "authentication validation" --type semantic

# Find function calls
code-sitter search "processData" --type calls

# Get function definition
code-sitter search "handleSubmit" --type definition
```

### View Statistics

```bash
# Show indexed codebase statistics
code-sitter stats
```

### Analyze Dependencies

```bash
# Analyze a specific file
code-sitter analyze src/components/Button.tsx
```

## 🔧 Advanced Usage

### Using Enhanced Flow (with call-site extraction)

```bash
# Run the enhanced flow directly
python -c "from code_sitter.flows.enhanced import flow; flow.update()"

# Or use with CocoIndex CLI
cocoindex update src/code_sitter/flows/enhanced.py

# For the flexible flow with language analyzers
cocoindex update src/code_sitter/flows/flexible.py
```

### Programmatic Usage

```python
from code_sitter.query import CodeSearchEngine

# Initialize search engine
engine = CodeSearchEngine()

# Search for symbols
results = engine.search_symbol("useState")

# Semantic search
results = engine.semantic_search("user authentication", k=5)

# Find function calls
calls = engine.find_function_calls("fetchData")

# Clean up
engine.close()
```

## 🗄️ Using PostgreSQL (Optional)

1. Install PostgreSQL with pgvector extension:
```bash
# macOS
brew install postgresql
brew install pgvector

# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib
# Follow pgvector installation guide
```

2. Create database:
```sql
CREATE DATABASE code_index;
\c code_index;
CREATE EXTENSION vector;
```

3. Set environment variables:
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/code_index"
export USE_POSTGRES=true
```

## 📊 Output Files

When using JSON storage (default), the following files are created:

- `code_index.json` - Main index with code chunks and embeddings
- `symbol_index.json` - Symbol to location mapping
- `call_relationships.json` - Function call relationships (enhanced flow only)

## 🎯 Next Steps

1. **Index a TypeScript project**: Start with a small project to test
2. **Experiment with searches**: Try different search types
3. **Integrate with your workflow**: Use the API in your tools
4. **Enable PostgreSQL**: For better performance with large codebases
5. **Customize the flow**: Modify `src/code_sitter/coco_flow.py` for your needs

## 🐛 Troubleshooting

### Common Issues
- **Import errors**: Make sure all dependencies are installed with `uv pip install -e .`
- **"No known parent package" error**: Use `--flow simple` instead of `--flow flexible`
- **No results**: Check if indexing completed successfully
- **Performance issues**: Consider using PostgreSQL instead of JSON
- **Memory errors**: Reduce chunk size in the flow configuration

### Useful uv Commands
```bash
# Add a new dependency
uv pip install package-name
uv add package-name  # Adds to pyproject.toml

# Update dependencies
uv pip install -e . --upgrade

# Show installed packages
uv pip list

# Create lock file for reproducible builds
uv pip compile pyproject.toml -o requirements.lock
```

### Migration Note
If you're upgrading from an older version that used `tree-sitter-languages`, note that we've migrated to `tree-sitter-language-pack` which:
- Supports Python 3.13 and newer versions
- Includes 165+ languages in a single package
- Is actively maintained with regular updates
- No need to install separate language packages

### Build System Note
This project uses Hatchling as its build backend with a flat module structure (Python files at the root level). The `pyproject.toml` is configured to include all root-level `.py` files and the `analyzers` package. If you encounter build issues, ensure the `[tool.hatch.build.targets.wheel]` section is present in `pyproject.toml`.

## 📚 Resources

- [CocoIndex Documentation](https://cocoindex.io/docs/)
- [Tree-sitter Documentation](https://tree-sitter.github.io/tree-sitter/)
- [Project README](README.md) for detailed information
