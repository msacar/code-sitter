#!/usr/bin/env python3
"""Test the structure extraction feature."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from codesitter.cli.commands.analyze import file as analyze_file
from codesitter.analyzers import get_analyzer
from codesitter.analyzers.base import CodeChunk
from pathlib import Path

# Test file path
test_file = Path("test_structure.ts")

# Get analyzer
analyzer = get_analyzer(str(test_file))
if not analyzer:
    print("No analyzer found for TypeScript files!")
    sys.exit(1)

print(f"Using analyzer: {analyzer.__class__.__name__}")

# Read file content
with open(test_file, 'r') as f:
    content = f.read()

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

# Test structure extraction
print("\n=== Testing extract_structure ===")
try:
    elements = list(analyzer.extract_structure(chunk))
    print(f"Extracted {len(elements)} elements:")
    for elem in elements:
        print(f"  - {elem.element_type}: {elem.name} (lines {elem.start_line}-{elem.end_line})")
        if elem.metadata:
            for key, value in elem.metadata.items():
                if key != 'filename':  # Skip filename
                    print(f"    {key}: {value}")
        if elem.children:
            print(f"    Children: {len(elem.children)}")
            for child in elem.children:
                print(f"      - {child.element_type}: {child.name}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Testing through CLI command ===")
# Now test through the CLI
from click.testing import CliRunner
from codesitter.cli.commands.analyze import analyze

runner = CliRunner()
result = runner.invoke(analyze, ['file', 'test_structure.ts'])
print(result.output)
