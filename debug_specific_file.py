#!/usr/bin/env python3
"""Debug why analyzer shows minimal output for a specific file."""

import sys
import os
from pathlib import Path

# Add codesitter to path
sys.path.insert(0, '/Users/mustafaacar/codesitter/src')

from codesitter.analyzers import get_analyzer, register_defaults, auto_discover_analyzers
from codesitter.analyzers.base import CodeChunk

# Initialize analyzers
register_defaults()
auto_discover_analyzers()

# The file path from the user's project
file_path = sys.argv[1] if len(sys.argv) > 1 else "modules/shortlink-api/src/services/instanceService.ts"

# Convert to absolute path if relative
if not os.path.isabs(file_path):
    file_path = os.path.abspath(file_path)

print(f"Analyzing: {file_path}")
print("-" * 80)

if not os.path.exists(file_path):
    print(f"ERROR: File not found: {file_path}")
    sys.exit(1)

# Read file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"File size: {len(content)} bytes")
print(f"Lines: {len(content.split('\n'))}")
print(f"First 500 chars:\n{content[:500]}...")
print("-" * 80)

# Get analyzer
analyzer = get_analyzer(file_path)
if not analyzer:
    print("ERROR: No analyzer found")
    sys.exit(1)

print(f"Analyzer: {analyzer.__class__.__name__}")
print(f"Language: {analyzer.language_name}")

# Create chunk
chunk = CodeChunk(
    text=content,
    filename=file_path,
    start_line=1,
    end_line=len(content.split('\n')),
    node_type="file",
    symbols=[],
    metadata={}
)

# Test tree-sitter parsing
print("\nTesting tree-sitter parsing...")
try:
    from tree_sitter import Parser
    parser, language = analyzer._get_parser_and_language(file_path)
    tree = parser.parse(bytes(content, "utf8"))
    print(f"✓ Parsing successful. Root node type: {tree.root_node.type}")
    print(f"  Tree has errors: {tree.root_node.has_error}")

    # Show first few nodes
    print("\n  First level children:")
    for i, child in enumerate(tree.root_node.children[:5]):
        print(f"    {i}: {child.type} [{child.start_byte}:{child.end_byte}]")
        if child.type == "ERROR":
            print(f"       ERROR NODE: {content[child.start_byte:child.end_byte][:50]}...")

except Exception as e:
    print(f"✗ Parsing failed: {e}")
    import traceback
    traceback.print_exc()

# Extract imports
print("\n\nExtracting imports...")
try:
    imports = list(analyzer.extract_import_relationships(chunk))
    print(f"Found {len(imports)} imports:")
    for imp in imports:
        print(f"  - {imp.imported_from} -> {imp.imported_items} (line {imp.line})")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

# Extract function calls
print("\n\nExtracting function calls...")
try:
    calls = list(analyzer.extract_call_relationships(chunk))
    print(f"Found {len(calls)} function calls:")
    for i, call in enumerate(calls[:10]):
        print(f"  {i+1}. {call.caller or '<module>'} -> {call.callee}({', '.join(call.arguments)}) at line {call.line}")
    if len(calls) > 10:
        print(f"  ... and {len(calls) - 10} more")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

# Extract metadata
print("\n\nExtracting metadata...")
try:
    metadata = analyzer.extract_custom_metadata(chunk)
    print(f"Metadata: {metadata}")
except Exception as e:
    print(f"ERROR: {e}")

# Test queries directly
print("\n\nTesting queries directly...")
try:
    tree = parser.parse(bytes(content, "utf8"))

    # Test import query
    import_query = language.query(analyzer._import_query)
    import_captures = import_query.captures(tree.root_node)
    print(f"\nImport query captures: {len(import_captures)}")
    for name, node in import_captures[:5]:
        print(f"  - {name}: {node.text.decode('utf8')[:50]}...")

    # Test function query
    func_query = language.query(analyzer._function_query)
    func_captures = func_query.captures(tree.root_node)
    print(f"\nFunction query captures: {len(func_captures)}")
    for name, node in func_captures[:5]:
        print(f"  - {name}: {node.text.decode('utf8')[:50]}...")

    # Test call query
    call_query = language.query(analyzer._call_query)
    call_captures = call_query.captures(tree.root_node)
    print(f"\nCall query captures: {len(call_captures)}")
    for name, node in call_captures[:5]:
        print(f"  - {name}: {node.text.decode('utf8')[:50]}...")

except Exception as e:
    print(f"Query testing failed: {e}")
    import traceback
    traceback.print_exc()
