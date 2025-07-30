#!/usr/bin/env python3
"""Check available tree-sitter languages."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tree_sitter_language_pack import get_language

# List of languages to check
languages_to_check = [
    "typescript",
    "tsx",
    "javascript",
    "jsx",
    "python",
    "java",
    "go",
    "rust",
    "c",
    "cpp"
]

print("Checking available tree-sitter languages...")
print("-" * 50)

for lang in languages_to_check:
    try:
        language = get_language(lang)
        print(f"✓ {lang:<15} - Available")
    except Exception as e:
        print(f"✗ {lang:<15} - Not found: {e}")

print("-" * 50)
print("\nNote: JSX might be included within JavaScript/TypeScript parsers")
print("rather than being a separate language.")
