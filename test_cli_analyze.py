#!/usr/bin/env python3
"""Test CLI analyze command with structure."""

import subprocess
import sys

# Run the analyze command
print("Running: codesitter analyze file test_structure.ts")
print("=" * 80)

result = subprocess.run(
    [sys.executable, "-m", "codesitter", "analyze", "file", "test_structure.ts"],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

print("\n" + "=" * 80)
print("Running with --json flag:")
print("=" * 80)

result = subprocess.run(
    [sys.executable, "-m", "codesitter", "analyze", "file", "test_structure.ts", "--json"],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
