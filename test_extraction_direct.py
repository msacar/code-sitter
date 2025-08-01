#!/usr/bin/env python3
"""Direct test of extraction issue."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tree_sitter import Parser
from tree_sitter_language_pack import get_language
from codesitter.analyzers.universal_extractor import UniversalExtractor, TypeScriptExtractor

# Simple test code with interface and class
test_code = """
interface User {
  id: number;
  name: string;
}

export class UserService {
  private logger: Logger;

  constructor() {
    this.logger = new Logger('UserService');
  }

  async getUser(id: number): Promise<User> {
    return null;
  }
}
"""

# Parse
ts_language = get_language("typescript")
parser = Parser(ts_language)
tree = parser.parse(bytes(test_code, "utf8"))

print("TEST 1: Base UniversalExtractor")
print("=" * 60)

# Test with base UniversalExtractor
base_extractor = UniversalExtractor(ts_language)
base_elements = list(base_extractor.extract_all(tree))

print(f"Base extractor found {len(base_elements)} elements:")
for elem in base_elements:
    print(f"  - {elem.element_type}: {elem.name}")

# Check patterns
print("\nBase extractor patterns include:")
print(f"  interface patterns: {base_extractor._node_type_to_element.get('interface_declaration', 'NOT FOUND')}")
print(f"  class patterns: {base_extractor._node_type_to_element.get('class_declaration', 'NOT FOUND')}")

print("\n\nTEST 2: TypeScriptExtractor")
print("=" * 60)

# Test with TypeScriptExtractor
ts_extractor = TypeScriptExtractor(ts_language)
ts_elements = list(ts_extractor.extract_all(tree))

print(f"TypeScript extractor found {len(ts_elements)} elements:")
for elem in ts_elements:
    exported = " [EXPORTED]" if elem.metadata.get('exported') else ""
    print(f"  - {elem.element_type}: {elem.name}{exported}")

# Check patterns after TS additions
print("\nTypeScript extractor patterns include:")
print(f"  interface_declaration maps to: {ts_extractor._node_type_to_element.get('interface_declaration', 'NOT FOUND')}")
print(f"  class_declaration maps to: {ts_extractor._node_type_to_element.get('class_declaration', 'NOT FOUND')}")

print("\n\nTEST 3: Direct AST inspection")
print("=" * 60)

def print_ast(node, indent=0):
    if node.is_named and node.type in ['interface_declaration', 'class_declaration', 'method_definition']:
        name = "?"
        for child in node.children:
            if child.type in ['identifier', 'type_identifier', 'property_identifier']:
                name = child.text.decode('utf-8')
                break
        print(f"{'  ' * indent}{node.type}: {name}")

    for child in node.children:
        print_ast(child, indent + 1)

print_ast(tree.root_node)

# Test name extraction directly
print("\n\nTEST 4: Direct name extraction")
print("=" * 60)

for node in tree.root_node.children:
    if node.type == 'interface_declaration':
        print(f"Found interface node, children: {[c.type for c in node.children]}")
        name = ts_extractor._extract_name(node)
        print(f"  _extract_name returned: {name}")

        # Try manual extraction
        for child in node.children:
            print(f"  Child: {child.type} = '{child.text.decode('utf-8')}'")
