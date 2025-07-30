#!/usr/bin/env python3
"""Debug TypeScript analyzer loading."""

import os
import sys
import logging

# Set up logging to see all messages
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=" * 60)
print("TypeScript Analyzer Debug")
print("=" * 60)

# First, test if tree-sitter languages are available
print("\n1. Testing tree-sitter language availability:")
try:
    from tree_sitter_language_pack import get_language

    test_langs = ["typescript", "tsx", "javascript", "jsx"]
    for lang in test_langs:
        try:
            get_language(lang)
            print(f"  ✓ {lang} - Available")
        except Exception as e:
            print(f"  ✗ {lang} - Error: {e}")
except Exception as e:
    print(f"  ✗ Failed to import tree_sitter_language_pack: {e}")

# Test loading the TypeScript analyzer directly
print("\n2. Testing TypeScript analyzer direct import:")
try:
    from codesitter.analyzers.languages.typescript import TypeScriptAnalyzer
    analyzer = TypeScriptAnalyzer()
    print(f"  ✓ TypeScript analyzer loaded successfully")
    print(f"  ✓ Supported extensions: {analyzer.supported_extensions}")
    print(f"  ✓ Language name: {analyzer.language_name}")
except Exception as e:
    print(f"  ✗ Failed to load TypeScript analyzer: {e}")
    import traceback
    traceback.print_exc()

# Test the registry
print("\n3. Testing analyzer registry:")
try:
    from codesitter.analyzers import register_defaults, auto_discover_analyzers, get_registry

    # Clear and re-initialize
    print("  - Registering defaults...")
    register_defaults()

    print("  - Auto-discovering analyzers...")
    auto_discover_analyzers()

    registry = get_registry()
    supported = registry.list_supported_extensions()

    print(f"\n  Total extensions supported: {len(supported)}")

    # Check TypeScript/JavaScript specifically
    ts_js_exts = ['.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs']
    for ext in ts_js_exts:
        if ext in supported:
            print(f"  ✓ {ext} -> {supported[ext]}")
        else:
            print(f"  ✗ {ext} -> Not registered")

except Exception as e:
    print(f"  ✗ Registry error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
