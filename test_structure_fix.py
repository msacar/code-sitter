#!/usr/bin/env python3
"""Test the fixed structure extraction."""

import subprocess
import json
import sys

# Run the analyze command
result = subprocess.run(
    [sys.executable, "-m", "codesitter", "analyze", "file", "test_calls.ts", "--json"],
    capture_output=True,
    text=True
)

if result.returncode != 0:
    print(f"Error: {result.stderr}")
    sys.exit(1)

data = json.loads(result.stdout)

print("Structure extraction after fix:")
print("=" * 60)

if 'structure' in data:
    print(f"Total elements extracted: {len(data['structure'])}")

    # Group by type
    by_type = {}
    for elem in data['structure']:
        elem_type = elem['type']
        if elem_type not in by_type:
            by_type[elem_type] = []
        by_type[elem_type].append(elem)

    # Display by type
    for elem_type, elements in sorted(by_type.items()):
        print(f"\n{elem_type.upper()}S ({len(elements)}):")
        for elem in elements:
            export_status = "exported" if elem.get('metadata', {}).get('exported') else "private"
            print(f"  - {elem['name']} ({export_status}) at lines {elem['lines']}")
            if elem.get('children'):
                for child in elem['children']:
                    print(f"    • {child['type']}: {child['name']}")

# Expected vs actual
print("\n" + "=" * 60)
print("EXPECTED:")
print("  - Interface: User")
print("  - Class: UserService (with 3 methods)")
print("  - Variable: createUserService")
print("  - Function: testCalls")
print("\nCheck if all are present above ↑")
