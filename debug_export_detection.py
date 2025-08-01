#!/usr/bin/env python3
"""Debug export detection for createUserService."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tree_sitter import Parser
from tree_sitter_language_pack import get_language

# Test just the export const line
test_code = """
export const createUserService = () => {
  return new UserService();
};
"""

# Parse
ts_language = get_language("typescript")
parser = Parser(ts_language)
tree = parser.parse(bytes(test_code, "utf8"))

print("AST STRUCTURE FOR: export const createUserService")
print("=" * 60)

def print_tree(node, indent=0, show_all=False):
    """Print tree structure."""
    if show_all or node.is_named:
        prefix = "  " * indent
        name = ""
        if node.type in ['identifier', 'type_identifier']:
            name = f" '{node.text.decode('utf-8')}'"
        print(f"{prefix}{node.type}{name}")

    for child in node.children:
        print_tree(child, indent + 1, show_all)

print_tree(tree.root_node)

print("\n\nPARENT CHAIN ANALYSIS:")
print("=" * 60)

def find_and_analyze(node, target_name):
    """Find a node and analyze its parent chain."""
    if node.type == 'variable_declarator':
        for child in node.children:
            if child.type == 'identifier' and child.text.decode('utf-8') == target_name:
                print(f"Found variable_declarator for '{target_name}'")

                # Walk up parent chain
                current = node
                depth = 0
                while current:
                    print(f"  {'→' if depth > 0 else ''} {current.type}")
                    current = current.parent
                    depth += 1

                # Check specific parents
                print(f"\nDirect parent: {node.parent.type if node.parent else 'None'}")
                if node.parent and node.parent.parent:
                    print(f"Grandparent: {node.parent.parent.type}")
                    if node.parent.parent.parent:
                        print(f"Great-grandparent: {node.parent.parent.parent.type}")

                return

    for child in node.children:
        find_and_analyze(child, target_name)

find_and_analyze(tree.root_node, 'createUserService')

print("\n\nSOLUTION:")
print("=" * 60)
print("The export check needs to look at more than just the direct parent.")
print("For 'export const x', the chain is:")
print("  export_statement → lexical_declaration → variable_declarator")
print("\nWe need to check parent AND grandparent for export_statement!")
