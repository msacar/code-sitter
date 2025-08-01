#!/usr/bin/env python3
"""Debug why interfaces and classes are not being extracted."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tree_sitter import Parser
from tree_sitter_language_pack import get_language
from codesitter.analyzers.universal_extractor import TypeScriptExtractor

# Read test file
content = Path("test_calls.ts").read_text()

# Parse with tree-sitter
ts_language = get_language("typescript")
parser = Parser(ts_language)
tree = parser.parse(bytes(content, "utf8"))

print("DEBUGGING: Why are interface and class missing?")
print("=" * 60)

# First, let's verify they exist in the AST
print("\n1. CHECKING RAW AST:")
print("-" * 40)

def find_nodes(node, types_to_find, indent=0):
    if node.type in types_to_find:
        name = "?"
        for child in node.children:
            if child.type in ['identifier', 'type_identifier']:
                name = child.text.decode('utf-8')
                break
        print(f"{'  ' * indent}Found {node.type}: {name} at line {node.start_point[0] + 1}")

        # Check if it's exported
        if node.parent and node.parent.type == 'export_statement':
            print(f"{'  ' * indent}  -> EXPORTED")

    for child in node.children:
        find_nodes(child, types_to_find, indent + 1)

find_nodes(tree.root_node, ['interface_declaration', 'class_declaration'])

# Now let's trace the extractor
print("\n2. TRACING EXTRACTOR:")
print("-" * 40)

extractor = TypeScriptExtractor(ts_language)

# Check what patterns it's looking for
print("Extractor patterns:")
for elem_type, node_types in extractor._node_type_to_element.items():
    print(f"  {elem_type}: {node_types}")

# Let's manually walk and see what happens
print("\n3. MANUAL EXTRACTION TEST:")
print("-" * 40)

def test_extraction(node, depth=0):
    indent = "  " * depth

    if node.is_named:
        # Check if this node type is in the patterns
        if node.type in extractor._node_type_to_element:
            elem_type = extractor._node_type_to_element[node.type]
            print(f"{indent}{node.type} -> {elem_type}")

            # Try to create element
            element = extractor._create_element(node)
            if element:
                print(f"{indent}  Created: {element.element_type} '{element.name}'")
            else:
                print(f"{indent}  Failed to create element")

                # Debug why it failed
                name = extractor._extract_name(node)
                print(f"{indent}    Name extracted: {name}")

    # Only go 2 levels deep for clarity
    if depth < 2:
        for child in node.children:
            test_extraction(child, depth + 1)

test_extraction(tree.root_node)

# Let's specifically check the interface and class nodes
print("\n4. SPECIFIC NODE INSPECTION:")
print("-" * 40)

def inspect_specific_node(node, target_type, target_name):
    if node.type == target_type:
        for child in node.children:
            if child.type in ['identifier', 'type_identifier'] and child.text.decode('utf-8') == target_name:
                print(f"\nFound {target_type}: {target_name}")
                print(f"  Parent type: {node.parent.type if node.parent else 'None'}")
                print(f"  Is named: {node.is_named}")
                print(f"  Children: {[c.type for c in node.children]}")

                # Check if it would match patterns
                if node.type in extractor._node_type_to_element:
                    print(f"  ✓ Matches pattern for: {extractor._node_type_to_element[node.type]}")
                else:
                    print(f"  ✗ No pattern match for: {node.type}")
                    print(f"  Available patterns: {list(extractor._node_type_to_element.keys())}")
                return

    for child in node.children:
        inspect_specific_node(child, target_type, target_name)

inspect_specific_node(tree.root_node, 'interface_declaration', 'User')
inspect_specific_node(tree.root_node, 'class_declaration', 'UserService')
