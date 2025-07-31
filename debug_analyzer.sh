#!/bin/bash
# Debug script for codesitter analyzer

echo "=== Codesitter Analyzer Debug ==="
echo

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "Error: Not in codesitter directory"
    exit 1
fi

# Check if virtual environment is active
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Warning: Virtual environment not active"
    echo "Run: source .venv/bin/activate"
    echo
fi

# Test tree-sitter installation
echo "1. Testing tree-sitter installation..."
python -c "
try:
    from tree_sitter_language_pack import get_language
    print('  ✓ tree_sitter_language_pack installed')
    ts = get_language('typescript')
    print('  ✓ TypeScript language available')
except Exception as e:
    print(f'  ✗ Error: {e}')
"

echo
echo "2. Testing analyzer on test file..."
if [ -f "test_file.ts" ]; then
    echo "  Running: codesitter analyze file test_file.ts"
    codesitter analyze file test_file.ts
else
    echo "  ✗ test_file.ts not found"
fi

echo
echo "3. Testing with Python directly..."
python -c "
import sys
sys.path.insert(0, 'src')
from codesitter.analyzers import register_defaults, auto_discover_analyzers, get_analyzer
from codesitter.analyzers.base import CodeChunk

# Initialize
register_defaults()
auto_discover_analyzers()

# Test
analyzer = get_analyzer('test.ts')
if analyzer:
    print(f'  ✓ Analyzer found: {analyzer.__class__.__name__}')
else:
    print('  ✗ No analyzer found')
"

echo
echo "4. Available analyzers:"
codesitter analyze list

echo
echo "=== Debug complete ==="
