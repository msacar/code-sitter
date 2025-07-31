#!/usr/bin/env python3
"""Fix all language analyzers to use the correct tree-sitter API."""

import os
import re
from pathlib import Path

# Path to the analyzers directory
analyzers_dir = Path("/Users/mustafaacar/codesitter/src/codesitter/analyzers/languages")

def fix_analyzer_file(file_path):
    """Fix a single analyzer file to use the correct API."""
    print(f"Processing {file_path.name}...")

    with open(file_path, 'r') as f:
        content = f.read()

    original = content
    changes_made = []

    # 1. Add QueryCursor to imports if Query is imported
    if "from tree_sitter import" in content and "Query" in content:
        if "QueryCursor" not in content:
            content = re.sub(
                r'from tree_sitter import ([^)\n]+)',
                lambda m: f'from tree_sitter import {m.group(1)}, QueryCursor' if 'QueryCursor' not in m.group(1) else m.group(0),
                content
            )
            changes_made.append("Added QueryCursor import")

    # 2. Replace language.query() with Query()
    if "language.query(" in content:
        content = re.sub(
            r'(\s+)query = language\.query\(self\._(\w+)_query\)',
            r'\1query = Query(language, self._\2_query)',
            content
        )
        changes_made.append("Replaced language.query() with Query()")

    if "self._language.query(" in content:
        content = re.sub(
            r'(\s+)query = self\._language\.query\(self\._(\w+)_query\)',
            r'\1query = Query(self._language, self._\2_query)',
            content
        )
        changes_made.append("Replaced self._language.query() with Query()")

    # 3. Replace query.captures() with query_captures()
    if "query.captures(" in content:
        content = re.sub(
            r'(\s+)captures = query\.captures\(([^)]+)\)',
            r'\1captures = query_captures(query, \2)',
            content
        )
        changes_made.append("Replaced query.captures() with query_captures()")

    # 4. Add query_captures to parser_utils imports if needed
    if "query_captures(" in content and "from ..parser_utils import" in content:
        if "query_captures" not in content:
            content = re.sub(
                r'from \.\.parser_utils import ([^)\n]+)',
                lambda m: f'from ..parser_utils import {m.group(1)}, query_captures' if 'query_captures' not in m.group(1) else m.group(0),
                content
            )
            changes_made.append("Added query_captures import")

    # 5. Fix the order of captures (old API was (name, node), new is (node, name))
    # This is handled in parser_utils.py to maintain compatibility

    if content != original:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"  ✓ Fixed {file_path.name}: {', '.join(changes_made)}")
        return True
    else:
        print(f"  - No changes needed for {file_path.name}")
        return False

# Process all Python files in the languages directory
fixed_count = 0
for py_file in analyzers_dir.glob("*.py"):
    if py_file.name == "__init__.py":
        continue

    if fix_analyzer_file(py_file):
        fixed_count += 1

print(f"\nFixed {fixed_count} analyzer files.")
print("\nNow testing the TypeScript analyzer...")

# Test the fix
import sys
sys.path.insert(0, "/Users/mustafaacar/codesitter/src")

from codesitter.analyzers import register_defaults, auto_discover_analyzers, get_analyzer
from codesitter.analyzers.base import CodeChunk

# Initialize
register_defaults()
auto_discover_analyzers()

# Test with the test file
test_file = "/Users/mustafaacar/codesitter/test_file.ts"
if os.path.exists(test_file):
    with open(test_file, 'r') as f:
        content = f.read()

    analyzer = get_analyzer(test_file)
    if analyzer:
        chunk = CodeChunk(
            text=content,
            filename=test_file,
            start_line=1,
            end_line=len(content.split('\n')),
            node_type="file",
            symbols=[],
            metadata={}
        )

        try:
            imports = list(analyzer.extract_import_relationships(chunk))
            calls = list(analyzer.extract_call_relationships(chunk))
            metadata = analyzer.extract_custom_metadata(chunk)

            print(f"\n✓ TypeScript analyzer is working!")
            print(f"  Found {len(imports)} imports")
            print(f"  Found {len(calls)} function calls")
            print(f"  Metadata: {metadata}")
        except Exception as e:
            print(f"\n✗ Error testing analyzer: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n✗ No analyzer found for TypeScript")
else:
    print(f"\n✗ Test file not found: {test_file}")
