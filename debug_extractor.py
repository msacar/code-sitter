#!/usr/bin/env python3
"""Debug the UniversalExtractor step by step."""

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

# Create extractor with debug
class DebugExtractor(TypeScriptExtractor):
    def _extract_from_node(self, node, depth=0):
        """Override to add debug output."""
        indent = "  " * depth

        if node.is_named:
            print(f"{indent}Visiting: {node.type}")

            if node.type in self._node_type_to_element:
                print(f"{indent}  -> MATCHES pattern for: {self._node_type_to_element[node.type]}")
                element = self._create_element(node)
                if element:
                    print(f"{indent}  -> Created element: {element.element_type} '{element.name}'")
                else:
                    print(f"{indent}  -> Failed to create element (no name?)")

        # Call parent implementation
        yield from super()._extract_from_node(node, depth)

print("DEBUGGING UNIVERSAL EXTRACTOR:")
print("=" * 60)

extractor = DebugExtractor(ts_language)
elements = list(extractor.extract_all(tree))

print("\n" + "=" * 60)
print(f"FINAL RESULT: {len(elements)} elements extracted")
for elem in elements:
    print(f"  - {elem.element_type}: {elem.name}")
    if elem.children:
        for child in elem.children:
            print(f"    • {child.element_type}: {child.name}")
