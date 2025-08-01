#!/usr/bin/env python3
"""Debug visibility detection."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tree_sitter import Parser
from tree_sitter_language_pack import get_language

# Test code with visibility modifiers
test_code = """
class Test {
    public publicMethod() {}
    private privateMethod() {}
    protected protectedMethod() {}
    defaultMethod() {}
}
"""

# Parse
ts_language = get_language("typescript")
parser = Parser(ts_language)
tree = parser.parse(bytes(test_code, "utf8"))

print("AST STRUCTURE FOR METHODS WITH VISIBILITY:")
print("=" * 60)

def analyze_method(node, indent=0):
    if node.type == 'method_definition':
        print(f"\nMethod: {node.child_by_field_name('name').text.decode('utf-8')}")
        print(f"  Node children: {[c.type for c in node.children]}")

        # Check siblings
        parent = node.parent
        if parent:
            print(f"  Parent type: {parent.type}")
            for i, sibling in enumerate(parent.children):
                if sibling == node:
                    print(f"  Position {i}: {node.type}")
                    if i > 0:
                        prev = parent.children[i-1]
                        print(f"  Previous sibling: {prev.type} = '{prev.text.decode('utf-8')}'")
                    break

    for child in node.children:
        analyze_method(child, indent + 1)

analyze_method(tree.root_node)
