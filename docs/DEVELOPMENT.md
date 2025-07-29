# Development Guide

## Project Structure

Code-Sitter follows the **src layout** pattern, which is the modern best practice for Python projects:

```
code-sitter/
├── src/code_sitter/     # Main package code
├── scripts/             # Standalone scripts
├── tests/              # Test suite
├── docs/               # Documentation
└── pyproject.toml      # Project configuration
```

## Development Setup

1. **Install uv** (fast Python package manager):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Create virtual environment**:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install in development mode**:
   ```bash
   uv pip install -e ".[dev]"
   ```

## Running the Project

### As a CLI tool:
```bash
# After installation
code-sitter --help
code-sitter index --path /path/to/project

# Or directly as a module
python -m code_sitter --help
```

### Programmatically:
```python
from code_sitter.query import CodeSearchEngine
from code_sitter.analyzers import get_analyzer

# Use the API
engine = CodeSearchEngine()
results = engine.search_symbol("useState")
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=code_sitter

# Run specific test
pytest tests/test_analyzers.py::test_typescript_analyzer
```

## Code Style

The project uses:
- **Ruff** for linting and formatting
- **MyPy** for type checking

```bash
# Format code
ruff format src/ tests/

# Check linting
ruff check src/ tests/

# Type checking
mypy src/code_sitter
```

## Adding New Features

### Adding a Language Analyzer

1. Create a new file in `src/code_sitter/analyzers/languages/`
2. Implement the `LanguageAnalyzer` interface
3. The analyzer will be auto-discovered

See [docs/ADDING_LANGUAGES.md](ADDING_LANGUAGES.md) for details.

### Adding New Commands

1. Add new command functions in `src/code_sitter/cli.py`
2. Use Click decorators for command definition
3. Update help text and documentation

## Project Layout Benefits

The **src layout** provides several advantages:

1. **Clear separation**: Package code is isolated in `src/`
2. **Import safety**: Prevents accidentally importing from development directory
3. **Tool compatibility**: Works well with all Python packaging tools
4. **Testing isolation**: Tests can't accidentally import local files

## Common Tasks

### Building a Distribution
```bash
# Build wheel and sdist
uv build

# Files will be in dist/
ls dist/
```

### Installing from Source
```bash
# Install from local source
uv pip install .

# Install with dev dependencies
uv pip install -e ".[dev]"
```

### Running Scripts
```bash
# Example scripts are in scripts/
python scripts/example.py
```

## CLI Architecture

The CLI is organized into a modular structure:

```
cli/
├── __init__.py       # Main CLI group and entry point
├── commands/         # Individual command modules
│   ├── index.py     # Indexing commands
│   ├── search.py    # Search functionality
│   ├── stats.py     # Statistics display
│   └── analyze.py   # File analysis
├── config.py        # CLI configuration and constants
└── utils.py         # Display utilities and formatters
```

### Adding a New Command

1. Create a new file in `src/code_sitter/cli/commands/`
2. Define your command using Click decorators
3. Import and register it in `cli/__init__.py`

Example:
```python
# src/code_sitter/cli/commands/mycommand.py
import click

@click.command()
@click.option('--flag', is_flag=True)
def mycommand(flag):
    """Description of my command."""
    # Implementation

# In cli/__init__.py
from .commands import mycommand
cli.add_command(mycommand.mycommand)
```

## Tips

- Always use relative imports within the package (e.g., `from .query import ...`)
- Scripts should use absolute imports (e.g., `from code_sitter.query import ...`)
- Keep configuration files at the project root
- Put all package code under `src/code_sitter/`
