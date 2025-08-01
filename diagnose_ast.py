#!/usr/bin/env python3
"""Diagnose AST parsing issues."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tree_sitter import Parser
from tree_sitter_language_pack import get_language

# Read test file
content = Path("test_calls.ts").read_text()

# Parse with tree-sitter
ts_language = get_language("typescript")
parser = Parser(ts_language)
tree = parser.parse(bytes(content, "utf8"))

print("AST STRUCTURE OF test_calls.ts:")
print("=" * 60)

def analyze_node(node, indent=0):
    """Print node with relevant info."""
    if node.is_named:
        prefix = "  " * indent
        print(f"{prefix}{node.type} [{node.start_point[0]+1}:{node.start_point[1]} - {node.end_point[0]+1}:{node.end_point[1]}]")

        # For certain types, show the name
        if node.type in ['identifier', 'type_identifier', 'property_identifier']:
            print(f"{prefix}  -> '{node.text.decode('utf-8')}'")

        # Show if it's under an export
        parent = node.parent
        if parent and parent.type == 'export_statement':
            print(f"{prefix}  -> EXPORTED")

# Walk the tree and show structure
def walk_tree(node, indent=0):
    if node.is_named and node.type in [
        'interface_declaration',
        'class_declaration',
        'function_declaration',
        'method_definition',
        'variable_declarator',
        'lexical_declaration',
        'export_statement'
    ]:
        analyze_node(node, indent)

        # For exports, show what's being exported
        if node.type == 'export_statement':
            for child in node.named_children:
                if child.type != 'export':  # Skip the 'export' keyword
                    analyze_node(child, indent + 1)

    # Always recurse
    for child in node.children:
        walk_tree(child, indent + (1 if node.type in ['class_body', 'statement_block'] else 0))

walk_tree(tree.root_node)

print("\n" + "=" * 60)
print("DIRECT CHILD INSPECTION:")

# Look at direct children of root
for i, child in enumerate(tree.root_node.named_children):
    print(f"\nChild {i}: {child.type}")
    if child.type == 'export_statement':
        print("  Contains:")
        for subchild in child.named_children:
            print(f"    - {subchild.type}")
            if subchild.type in ['class_declaration', 'lexical_declaration']:
                # Get the name
                for n in subchild.children:
                    if n.type in ['identifier', 'type_identifier']:
                        print(f"      name: {n.text.decode('utf-8')}")
                        break
                    elif n.type == 'variable_declarator':
                        for nn in n.children:
                            if nn.type == 'identifier':
                                print(f"      name: {nn.text.decode('utf-8')}")
                                break
