# Codesitter - Quick Reference

## Installation
```bash
# Clone and setup
git clone <repo>
cd codesitter
uv venv
source .venv/bin/activate
uv pip install -e .
```

## Main Features

### 1. Smart Chunking
Create intelligent chunks that preserve context:

```bash
# Index with smart chunking
codesitter index --flow smart_chunking

# Demo smart chunking
./demo_smart_chunking.py

# Compare with traditional
./compare_chunking.py
```

### 2. Standalone Analysis
Analyze code without indexing:

```bash
# List available analyzers
codesitter analyze list

# Analyze a file
codesitter analyze file src/auth.ts

# Analyze with options
codesitter analyze file src/auth.ts --json
codesitter analyze file src/auth.ts --imports-only
codesitter analyze file src/auth.ts --calls-only

# Analyze directory
codesitter analyze directory ./src --ext .ts
```

### 3. Traditional Indexing & Search
```bash
# Index codebase
codesitter index

# Search
codesitter search "database connection" --type semantic
codesitter search "useState" --type symbol
codesitter search "processData" --type calls

# View stats
codesitter stats
```

## Architecture
```
src/codesitter/
├── analyzers/     # Language understanding
├── chunkers/      # Smart chunking
├── flows/         # CocoIndex integration
├── cli/           # User interface
└── query.py       # Search engine
```

## Testing
```bash
# Test analyzer
./test_integrated_analyzer.sh

# Test smart chunking
./test_smart_chunking.py

# Run examples
./analyzer_examples.py react-components ./src
```

## Documentation
- `README.md` - Main documentation
- `docs/ARCHITECTURE.md` - System design
- `docs/SMART_CHUNKING.md` - Smart chunking details
- `docs/ANALYZER_CLI.md` - Analyzer usage
- `docs/QUICKSTART.md` - Getting started

## Key Commands Summary
```bash
# Indexing
codesitter index [--flow smart_chunking] [--postgres] [--watch]

# Analysis
codesitter analyze list
codesitter analyze file <path> [--json] [--calls-only] [--imports-only]
codesitter analyze directory <path> [--ext .ts] [--json]

# Search
codesitter search <query> [--type symbol|semantic|calls|definition]

# Stats
codesitter stats
```

Enjoy your code intelligence! 🚀
