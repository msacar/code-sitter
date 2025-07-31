#!/usr/bin/env python3
"""Test tree-sitter Parser initialization to debug the error."""

import sys
from tree_sitter import Language, Parser, Query
from tree_sitter_language_pack import get_language

def test_parser_creation():
    """Test different ways to create a parser."""
    print("Testing tree-sitter Parser creation...")

    # Get TypeScript language
    ts_language = get_language("typescript")
    print(f"Got TypeScript language: {type(ts_language)}")

    # Method 1: Parser() then set_language (old way)
    try:
        parser1 = Parser()
        print(f"Parser created: {type(parser1)}")
        print(f"Parser methods: {[m for m in dir(parser1) if not m.startswith('_')]}")

        if hasattr(parser1, 'set_language'):
            parser1.set_language(ts_language)
            print("✓ Method 1: Parser() + set_language() works")
        else:
            print("✗ Method 1: Parser has no set_language method")
    except Exception as e:
        print(f"✗ Method 1 failed: {e}")

    # Method 2: Parser(language) (newer way?)
    try:
        parser2 = Parser(ts_language)
        print("✓ Method 2: Parser(language) works")
    except Exception as e:
        print(f"✗ Method 2 failed: {e}")

    # Method 3: Check tree-sitter-language-pack specific method
    try:
        # Maybe language pack has its own parser creation
        if hasattr(ts_language, 'parser'):
            parser3 = ts_language.parser()
            print("✓ Method 3: language.parser() works")
        else:
            print("✗ Method 3: Language has no parser method")
    except Exception as e:
        print(f"✗ Method 3 failed: {e}")

    # Test parsing
    print("\nTesting actual parsing...")
    test_code = "function hello() { return 'world'; }"

    for i, parser in enumerate([p for p in [parser1, parser2] if 'p' in locals()], 1):
        try:
            tree = parser.parse(bytes(test_code, 'utf8'))
            print(f"✓ Parser {i} can parse code. Root node: {tree.root_node.type}")
        except Exception as e:
            print(f"✗ Parser {i} failed to parse: {e}")

if __name__ == "__main__":
    test_parser_creation()
