#!/usr/bin/env python3
"""Test script to demonstrate exports and symbols extraction."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codesitter.analyzers.languages.typescript import TypeScriptAnalyzer
from codesitter.analyzers.base import CodeChunk

def test_exports_symbols_extraction():
    """Test extraction of exports and symbols from TypeScript file."""

    # Read test file
    test_file = Path("test_exports_symbols.ts")
    content = test_file.read_text()

    # Create analyzer
    analyzer = TypeScriptAnalyzer()

    # Create chunk for whole file
    lines = content.split('\n')
    chunk = CodeChunk(
        text=content,
        filename=str(test_file),
        start_line=1,
        end_line=len(lines),
        node_type="file",
        symbols=[]
    )

    print("\n" + "="*80)
    print("EXPORTS AND SYMBOLS EXTRACTION TEST")
    print("="*80)

    # 1. Extract structural elements
    print("\n📋 EXTRACTED STRUCTURE:")
    print("-" * 40)

    elements = list(analyzer.extract_structure(chunk))

    # Group by export status
    exported_elements = []
    private_elements = []

    for elem in elements:
        if elem.metadata.get('exported'):
            exported_elements.append(elem)
        else:
            private_elements.append(elem)

    print(f"\n✅ EXPORTED SYMBOLS ({len(exported_elements)}):")
    for elem in exported_elements:
        icon = {
            'function': '🔧',
            'class': '🏛️',
            'interface': '📘',
            'type': '📐',
            'enum': '🎯',
            'variable': '📦'
        }.get(elem.element_type, '📄')

        print(f"  {icon} {elem.element_type}: {elem.name}")
        if elem.element_type == 'class' and elem.children:
            print(f"     Methods: {[child.name for child in elem.children if child.element_type == 'function']}")
        if elem.metadata.get('kind'):
            print(f"     Kind: {elem.metadata['kind']}")

    print(f"\n🔒 PRIVATE SYMBOLS ({len(private_elements)}):")
    for elem in private_elements:
        icon = {
            'function': '🔧',
            'class': '🏛️',
            'interface': '📘',
            'type': '📐',
            'enum': '🎯',
            'variable': '📦'
        }.get(elem.element_type, '📄')

        print(f"  {icon} {elem.element_type}: {elem.name}")

    # 2. Extract import relationships
    print("\n\n📦 IMPORT/EXPORT STATEMENTS:")
    print("-" * 40)

    imports = list(analyzer.extract_import_relationships(chunk))
    for imp in imports:
        print(f"  {imp.import_type}: {imp.imported_from}")
        if imp.imported_items:
            print(f"    Items: {', '.join(imp.imported_items)}")

    # 3. Show detailed metadata for some elements
    print("\n\n🔍 DETAILED ELEMENT METADATA:")
    print("-" * 40)

    # Show details for UserService class
    user_service = next((e for e in elements if e.name == "UserService"), None)
    if user_service:
        print(f"\nClass: {user_service.name}")
        print(f"  Exported: {user_service.metadata.get('exported', False)}")
        print(f"  Lines: {user_service.start_line}-{user_service.end_line}")
        print(f"  Methods:")
        for method in user_service.children:
            if method.element_type == 'function':
                print(f"    - {method.name}")
                if method.metadata.get('async'):
                    print(f"      async: True")
                if method.metadata.get('parameters'):
                    params = [f"{p['name']}: {p.get('type', 'any')}" for p in method.metadata['parameters']]
                    print(f"      params: ({', '.join(params)})")
                if method.metadata.get('return_type'):
                    print(f"      returns: {method.metadata['return_type']}")

    # Show export patterns
    print("\n\n📤 EXPORT PATTERNS FOUND:")
    print("-" * 40)

    export_patterns = {
        'default': False,
        'named_values': [],
        'named_types': [],
        'interfaces': [],
        'enums': [],
        're_exports': []
    }

    for elem in exported_elements:
        if elem.element_type == 'class' and 'default' in chunk.text[elem.start_byte-20:elem.start_byte]:
            export_patterns['default'] = elem.name
        elif elem.element_type == 'variable':
            export_patterns['named_values'].append(elem.name)
        elif elem.element_type == 'type':
            export_patterns['named_types'].append(elem.name)
        elif elem.element_type == 'interface':
            export_patterns['interfaces'].append(elem.name)
        elif elem.element_type == 'enum':
            export_patterns['enums'].append(elem.name)

    print(f"  Default export: {export_patterns['default']}")
    print(f"  Named value exports: {export_patterns['named_values']}")
    print(f"  Type exports: {export_patterns['named_types']}")
    print(f"  Interface exports: {export_patterns['interfaces']}")
    print(f"  Enum exports: {export_patterns['enums']}")

    # Summary
    print("\n\n📊 SUMMARY:")
    print("-" * 40)
    print(f"  Total symbols: {len(elements)}")
    print(f"  Exported: {len(exported_elements)}")
    print(f"  Private: {len(private_elements)}")
    print(f"  Has default export: {'Yes' if export_patterns['default'] else 'No'}")

if __name__ == "__main__":
    test_exports_symbols_extraction()
