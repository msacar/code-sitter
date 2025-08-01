#!/usr/bin/env python3
"""Direct test of structure extraction."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codesitter.analyzers.languages.typescript import TypeScriptAnalyzer
from codesitter.analyzers.base import CodeChunk

# Read test file
content = Path("test_calls.ts").read_text()
lines = content.split('\n')

# Create analyzer and chunk
analyzer = TypeScriptAnalyzer()
chunk = CodeChunk(
    text=content,
    filename="test_calls.ts",
    start_line=1,
    end_line=len(lines),
    node_type="file",
    symbols=[]
)

# Extract structure
elements = list(analyzer.extract_structure(chunk))

print("STRUCTURE EXTRACTION RESULTS:")
print("=" * 60)
print(f"Total elements: {len(elements)}\n")

for elem in elements:
    export_marker = "✓ EXPORTED" if elem.metadata.get('exported') else "  private"
    print(f"{export_marker} | {elem.element_type}: {elem.name} (lines {elem.start_line}-{elem.end_line})")

    # Show details for some types
    if elem.element_type == 'class' and elem.children:
        print(f"         Methods:")
        for child in elem.children:
            if child.element_type == 'function':
                async_marker = "async " if child.metadata.get('async') else ""
                print(f"           - {async_marker}{child.name}()")

    elif elem.element_type == 'variable' and elem.metadata.get('kind'):
        print(f"         Kind: {elem.metadata['kind']}")

    elif elem.element_type == 'function' and elem.metadata.get('parameters'):
        params = [p['name'] for p in elem.metadata['parameters']]
        print(f"         Parameters: ({', '.join(params)})")

print("\n" + "=" * 60)
print("SUMMARY:")
by_type = {}
for elem in elements:
    by_type[elem.element_type] = by_type.get(elem.element_type, 0) + 1

for elem_type, count in sorted(by_type.items()):
    print(f"  {elem_type}s: {count}")
