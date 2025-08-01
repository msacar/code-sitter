#!/usr/bin/env python3
"""Quick verification of the fixes."""

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

print("STRUCTURE EXTRACTION - AFTER FIXES")
print("=" * 60)

# Check what we got
structure = data.get('structure', [])
print(f"Total elements: {len(structure)}")

# Expected elements
expected = {
    'User': 'interface',
    'UserService': 'class',
    'createUserService': 'variable',
    'testCalls': 'function'
}

print("\nChecking expected elements:")
for name, expected_type in expected.items():
    found = next((e for e in structure if e['name'] == name), None)
    if found:
        actual_type = found['type']
        status = "✓" if actual_type == expected_type else f"⚠ (got {actual_type})"
        exported = " [EXPORTED]" if found.get('metadata', {}).get('exported') else ""
        print(f"  {status} {name} ({expected_type}){exported}")
    else:
        print(f"  ✗ {name} ({expected_type}) - NOT FOUND")

# Show all elements
print("\nAll extracted elements:")
for elem in structure:
    exported = "[EXPORTED]" if elem.get('metadata', {}).get('exported') else "[private]"
    print(f"  {elem['type']}: {elem['name']} {exported} at lines {elem['lines']}")
    if elem.get('children'):
        for child in elem['children']:
            print(f"    - {child['type']}: {child['name']}")

# Summary
print("\n" + "-" * 60)
missing_count = sum(1 for name in expected if not any(e['name'] == name for e in structure))
if missing_count == 0:
    print("✅ ALL EXPECTED ELEMENTS FOUND! Structure extraction is working correctly.")
else:
    print(f"⚠️  {missing_count} expected elements are still missing.")
