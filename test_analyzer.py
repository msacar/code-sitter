#!/usr/bin/env python3
"""Test the TypeScript analyzer directly."""

from pathlib import Path
from src.codesitter.analyzers import get_analyzer, register_defaults, auto_discover_analyzers
from src.codesitter.analyzers.base import CodeChunk

# Initialize analyzers
register_defaults()
auto_discover_analyzers()

# Test file content
test_file = Path("test_file.ts")
if not test_file.exists():
    print(f"Error: {test_file} does not exist")
    exit(1)

with open(test_file, 'r') as f:
    content = f.read()

# Get analyzer
analyzer = get_analyzer(str(test_file))
if not analyzer:
    print(f"No analyzer found for {test_file}")
    exit(1)

print(f"Analyzer: {analyzer.__class__.__name__}")
print(f"Language: {analyzer.language_name}")
print("-" * 60)

# Create chunk
chunk = CodeChunk(
    text=content,
    filename=str(test_file),
    start_line=1,
    end_line=len(content.split('\n')),
    node_type="file",
    symbols=[],
    metadata={}
)

# Extract imports
print("\nImports:")
try:
    imports = list(analyzer.extract_import_relationships(chunk))
    for imp in imports:
        print(f"  - {imp.imported_from} -> {imp.imported_items} (line {imp.line})")
    if not imports:
        print("  (none found)")
except Exception as e:
    print(f"  Error: {e}")

# Extract calls
print("\nFunction Calls:")
try:
    calls = list(analyzer.extract_call_relationships(chunk))
    for call in calls[:10]:  # Show first 10
        print(f"  - {call.caller or '<module>'} -> {call.callee}({', '.join(call.arguments)}) at line {call.line}")
    if len(calls) > 10:
        print(f"  ... and {len(calls) - 10} more")
    if not calls:
        print("  (none found)")
except Exception as e:
    print(f"  Error: {e}")

# Extract metadata
print("\nMetadata:")
try:
    metadata = analyzer.extract_custom_metadata(chunk)
    for k, v in metadata.items():
        print(f"  - {k}: {v}")
    if not metadata:
        print("  (none found)")
except Exception as e:
    print(f"  Error: {e}")
