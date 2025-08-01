#!/usr/bin/env python3
"""Debug why structure extraction is incomplete."""

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

print("Expected elements in test_calls.ts:")
print("1. Interface: User (lines 5-8)")
print("2. Class: UserService (lines 10-27)")
print("   - constructor method")
print("   - getUser method")
print("   - updateUser method")
print("3. Variable: createUserService (exported const)")
print("4. Function: testCalls")
print("\n" + "="*60 + "\n")

# Extract structure
elements = list(analyzer.extract_structure(chunk))

print(f"Actually extracted: {len(elements)} elements\n")

for i, elem in enumerate(elements):
    print(f"{i+1}. {elem.element_type}: {elem.name} (lines {elem.start_line}-{elem.end_line})")
    print(f"   node_type: {elem.node_type}")
    if elem.metadata.get('exported'):
        print(f"   exported: True")
    if elem.children:
        print(f"   children: {len(elem.children)}")
        for child in elem.children:
            print(f"     - {child.element_type}: {child.name}")
    print()

# Debug: Let's parse and look at the AST directly
from tree_sitter_language_pack import get_language
from tree_sitter import Parser

ts_language = get_language("typescript")
parser = Parser(ts_language)
tree = parser.parse(bytes(content, "utf8"))

print("\nDirect AST inspection:")
print("Root children types:")

def print_tree(node, indent=0):
    if node.is_named:
        print("  " * indent + f"{node.type} ({node.start_point[0]+1}-{node.end_point[0]+1})")
        if node.type in ['class_declaration', 'interface_declaration', 'function_declaration']:
            # Try to get name
            for child in node.children:
                if child.type == 'identifier' or child.type == 'type_identifier':
                    print("  " * indent + f"  name: {child.text.decode('utf-8')}")
                    break

    if indent < 2:  # Limit depth
        for child in node.children:
            print_tree(child, indent + 1)

print_tree(tree.root_node)
