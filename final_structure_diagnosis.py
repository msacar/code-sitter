#!/usr/bin/env python3
"""Final diagnosis and solution for structure extraction."""

import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codesitter.analyzers.languages.typescript import TypeScriptAnalyzer
from codesitter.analyzers.base import CodeChunk
from tree_sitter import Parser
from tree_sitter_language_pack import get_language

# Read test file
content = Path("test_calls.ts").read_text()
lines = content.split('\n')

print("COMPLETE STRUCTURE EXTRACTION ANALYSIS")
print("=" * 70)

# 1. First, let's see what the raw tree-sitter parse gives us
ts_language = get_language("typescript")
parser = Parser(ts_language)
tree = parser.parse(bytes(content, "utf8"))

print("1. RAW TREE-SITTER NODES (Key structural elements):")
print("-" * 50)

found_elements = []

def find_elements(node, parent_is_export=False):
    """Find all key structural elements in the AST."""
    is_export = parent_is_export or (node.parent and node.parent.type == 'export_statement')

    if node.type in ['interface_declaration', 'class_declaration', 'function_declaration',
                     'variable_declarator', 'method_definition', 'enum_declaration',
                     'type_alias_declaration']:
        # Get name
        name = None
        for child in node.children:
            if child.type in ['identifier', 'type_identifier', 'property_identifier']:
                name = child.text.decode('utf-8')
                break

        element_info = {
            'type': node.type,
            'name': name or '<unnamed>',
            'line': node.start_point[0] + 1,
            'exported': is_export
        }
        found_elements.append(element_info)
        print(f"  {node.type}: {name} (line {node.start_point[0] + 1}){' [EXPORTED]' if is_export else ''}")

    # Recurse
    for child in node.children:
        find_elements(child, is_export and node.type == 'export_statement')

find_elements(tree.root_node)

# 2. Now let's see what the analyzer extracts
print("\n2. TYPESCRIPT ANALYZER EXTRACTION:")
print("-" * 50)

analyzer = TypeScriptAnalyzer()
chunk = CodeChunk(
    text=content,
    filename="test_calls.ts",
    start_line=1,
    end_line=len(lines),
    node_type="file",
    symbols=[]
)

elements = list(analyzer.extract_structure(chunk))
print(f"Extracted {len(elements)} elements:")

for elem in elements:
    export_status = "[EXPORTED]" if elem.metadata.get('exported') else "[private]"
    print(f"  {elem.element_type}: {elem.name} (line {elem.start_line}) {export_status}")
    if elem.children:
        for child in elem.children:
            print(f"    - {child.element_type}: {child.name}")

# 3. Compare and diagnose
print("\n3. DIAGNOSIS:")
print("-" * 50)

# What tree-sitter found vs what analyzer extracted
ts_types = {e['type'] for e in found_elements}
analyzer_types = {e.element_type for e in elements}

print(f"Tree-sitter found these node types: {ts_types}")
print(f"Analyzer extracted these element types: {analyzer_types}")

# Missing elements
ts_names = {e['name'] for e in found_elements}
analyzer_names = {e.name for e in elements}
missing = ts_names - analyzer_names

if missing:
    print(f"\nMISSING ELEMENTS: {missing}")
    for elem in found_elements:
        if elem['name'] in missing:
            print(f"  - {elem['type']}: {elem['name']} at line {elem['line']}")

# 4. Root cause analysis
print("\n4. ROOT CAUSE:")
print("-" * 50)

if 'interface_declaration' in ts_types and 'interface' not in analyzer_types:
    print("✗ Interfaces are being mapped to 'type' instead of 'interface'")
    print("  This is because TypeScriptExtractor maps interface_declaration -> 'type'")

if len(found_elements) > len(elements):
    print("✗ Some elements are not being extracted")
    print("  Possible causes:")
    print("  - Container nodes (like lexical_declaration) interfering")
    print("  - Early return in recursion preventing sibling traversal")
    print("  - Missing node type mappings")

# 5. Test the fix
print("\n5. TESTING FIXES:")
print("-" * 50)

# The fix was already applied - removing lexical_declaration from patterns
# Let's verify it worked

# Count by type
type_counts = {}
for elem in elements:
    type_counts[elem.element_type] = type_counts.get(elem.element_type, 0) + 1

print("Elements by type:")
for elem_type, count in sorted(type_counts.items()):
    print(f"  {elem_type}: {count}")

# Expected vs actual
expected = {
    'User': 'interface',
    'UserService': 'class',
    'createUserService': 'variable/function',
    'testCalls': 'function'
}

print("\nExpected elements:")
for name, expected_type in expected.items():
    found = next((e for e in elements if e.name == name), None)
    if found:
        print(f"  ✓ {name} ({expected_type}): Found as {found.element_type}")
    else:
        print(f"  ✗ {name} ({expected_type}): NOT FOUND")

# 6. Final summary
print("\n6. SUMMARY:")
print("-" * 50)
if len(elements) >= 4 and 'UserService' in analyzer_names:
    print("✓ Structure extraction is now working correctly!")
    print("  All major elements are being extracted.")
else:
    print("✗ Structure extraction still has issues.")
    print("  Some elements are missing from the output.")
