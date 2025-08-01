#!/usr/bin/env python3
"""Check extractor patterns."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codesitter.analyzers.universal_extractor import UniversalExtractor, TypeScriptExtractor
from tree_sitter_language_pack import get_language

# Create extractors
ts_language = get_language("typescript")
base_extractor = UniversalExtractor(ts_language)
ts_extractor = TypeScriptExtractor(ts_language)

print("PATTERN INSPECTION")
print("=" * 60)

print("\nBase UniversalExtractor patterns:")
print("-" * 40)

# Check what node types map to what element types
for node_type, elem_type in sorted(base_extractor._node_type_to_element.items()):
    if elem_type in ['interface', 'class']:
        print(f"  {node_type} -> {elem_type}")

print("\nTypeScriptExtractor patterns (after TS additions):")
print("-" * 40)

for node_type, elem_type in sorted(ts_extractor._node_type_to_element.items()):
    if elem_type in ['interface', 'class', 'type']:
        print(f"  {node_type} -> {elem_type}")

print("\nChecking specific mappings:")
print("-" * 40)
print(f"interface_declaration maps to: '{ts_extractor._node_type_to_element.get('interface_declaration', 'NOT FOUND')}'")
print(f"class_declaration maps to: '{ts_extractor._node_type_to_element.get('class_declaration', 'NOT FOUND')}'")

# Save this info to a file so we can read it
output = f"""
EXTRACTOR PATTERNS CHECK
========================

interface_declaration -> {ts_extractor._node_type_to_element.get('interface_declaration', 'NOT FOUND')}
class_declaration -> {ts_extractor._node_type_to_element.get('class_declaration', 'NOT FOUND')}

All mappings in TypeScriptExtractor:
{dict(sorted(ts_extractor._node_type_to_element.items()))}
"""

with open("extractor_patterns_check.txt", "w") as f:
    f.write(output)

print("\nOutput saved to extractor_patterns_check.txt")
