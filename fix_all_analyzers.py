#!/usr/bin/env python3
"""Apply the tree-sitter API fix to all analyzers."""

import os
import re
from pathlib import Path

# Path to the analyzers directory
analyzers_dir = Path("/Users/mustafaacar/codesitter/src/codesitter/analyzers/languages")

# Pattern replacements
replacements = [
    # Replace language.query() with Query()
    (r'(\s+)query = self\._(\w+)_language\.query\(self\._(\w+)_query\)',
     r'\1query = Query(self._\2_language, self._\3_query)'),

    # Replace language.query() for simple cases
    (r'(\s+)query = language\.query\(self\._(\w+)_query\)',
     r'\1query = Query(language, self._\2_query)'),

    # Replace self._language.query()
    (r'(\s+)query = self\._language\.query\(self\._(\w+)_query\)',
     r'\1query = Query(self._language, self._\2_query)'),

    # Replace query.captures() with query_captures()
    (r'(\s+)captures = query\.captures\(([^)]+)\)',
     r'\1captures = query_captures(query, \2)'),

    # Replace inline query.captures()
    (r'query\.captures\(([^)]+)\)',
     r'query_captures(query, \1)'),
]

# Process each Python file
for py_file in analyzers_dir.glob("*.py"):
    if py_file.name == "__init__.py":
        continue

    print(f"Processing {py_file.name}...")

    with open(py_file, 'r') as f:
        content = f.read()

    original = content

    # Apply replacements
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    # Check if we need to add imports
    if "Query(" in content and "from tree_sitter import" in content:
        # Add Query to imports if not already there
        if ", Query" not in content and " Query" not in content:
            content = re.sub(
                r'from tree_sitter import ([^)\n]+)',
                r'from tree_sitter import \1, Query',
                content
            )

    if "query_captures(" in content and "from ..parser_utils import" in content:
        # Add query_captures to imports if not already there
        if ", query_captures" not in content and " query_captures" not in content:
            content = re.sub(
                r'from \.\.parser_utils import ([^)\n]+)',
                r'from ..parser_utils import \1, query_captures',
                content
            )

    if content != original:
        with open(py_file, 'w') as f:
            f.write(content)
        print(f"  ✓ Updated {py_file.name}")
    else:
        print(f"  - No changes needed for {py_file.name}")

print("\nDone!")
