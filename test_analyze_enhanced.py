#!/usr/bin/env python3

import subprocess
import json
import sys

# Run the analyze command
result = subprocess.run(
    ["python", "-m", "codesitter", "analyze", "file", "test_calls_enhanced.ts", "--json"],
    capture_output=True,
    text=True,
    cwd="/Users/mustafaacar/codesitter"
)

if result.returncode != 0:
    print(f"Error: {result.stderr}")
    sys.exit(1)

# Parse and display the JSON output
try:
    data = json.loads(result.stdout)
    print(json.dumps(data, indent=2))

    # Check if calls are associated with functions
    print("\n=== Function Call Associations ===")
    for elem in data.get("structure", []):
        if elem["type"] == "function" and "calls" in elem.get("metadata", {}):
            print(f"\nFunction: {elem['name']}")
            print(f"  Has {len(elem['metadata']['calls'])} calls:")
            for call in elem['metadata']['calls']:
                print(f"    - {call['callee']}({', '.join(call['arguments'])}) at line {call['line']}")
except json.JSONDecodeError as e:
    print(f"Failed to parse JSON: {e}")
    print("Output:", result.stdout)
