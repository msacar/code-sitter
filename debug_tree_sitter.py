#!/usr/bin/env python3
"""Debug tree-sitter installation and TypeScript parsing."""

import sys
try:
    from tree_sitter_language_pack import get_language
    print("✓ tree_sitter_language_pack imported successfully")

    # Test TypeScript language
    ts_lang = get_language("typescript")
    print("✓ TypeScript language loaded")

    # Test parser creation
    from tree_sitter import Parser
    parser = Parser()
    parser.set_language(ts_lang)
    print("✓ Parser created successfully")

    # Test parsing
    code = b"const x = 42;"
    tree = parser.parse(code)
    print("✓ Basic parsing works")
    print(f"  Root node type: {tree.root_node.type}")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nAll checks passed! Tree-sitter is properly installed.")
