#!/usr/bin/env python3
"""Test running debug script via subprocess."""

import subprocess
import sys

result = subprocess.run(
    [sys.executable, "debug_missing_elements.py"],
    capture_output=True,
    text=True,
    cwd="/Users/mustafaacar/codesitter"
)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")
