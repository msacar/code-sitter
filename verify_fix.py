#!/usr/bin/env python3
"""Verify TypeScript analyzer is now working."""
import sys
import os
os.chdir('/Users/mustafaacar/codesitter')

# Run the analyze command and capture output
import subprocess
result = subprocess.run(
    [sys.executable, '-m', 'codesitter', 'analyze', 'file', 'test_analyzer.ts'],
    capture_output=True,
    text=True
)

print("Output:")
print(result.stdout)

if result.stderr:
    print("\nErrors:")
    print(result.stderr)

# Check if we got meaningful output
if "Imports" in result.stdout and "Function Calls" in result.stdout:
    print("\n✅ SUCCESS: The TypeScript analyzer is now parsing functions, imports, and metadata!")
else:
    print("\n❌ Issue remains - check the output above")
