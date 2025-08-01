#!/usr/bin/env python3
"""Test the analyze command with calls in function metadata."""

import subprocess
import json
import sys

# Run the codesitter analyze command
result = subprocess.run(
    ["python", "-m", "codesitter", "analyze", "file", "test_calls.ts", "--json"],
    capture_output=True,
    text=True
)

if result.returncode != 0:
    print(f"Error running command: {result.stderr}")
    sys.exit(1)

# Parse the JSON output
try:
    output = json.loads(result.stdout)
    print(json.dumps(output, indent=2))
except json.JSONDecodeError as e:
    print(f"Error parsing JSON: {e}")
    print(f"Raw output: {result.stdout}")
    sys.exit(1)

# Verify the structure contains calls in function metadata
print("\n--- Verification ---")
for elem in output.get("structure", []):
    if elem["type"] == "function":
        func_name = elem["name"]
        calls = elem.get("metadata", {}).get("calls", [])
        print(f"Function '{func_name}' has {len(calls)} calls:")
        for call in calls:
            print(f"  - {call['callee']}() at line {call['line']}")
