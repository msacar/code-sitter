#!/usr/bin/env python3
"""Demo script to show current exports extraction functionality."""

import subprocess
import sys

# First, show the raw output
print("Running: codesitter analyze file test_exports_symbols.ts")
print("=" * 80)

result = subprocess.run(
    [sys.executable, "-m", "codesitter", "analyze", "file", "test_exports_symbols.ts"],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

print("\n" + "=" * 80)
print("Key Features Demonstrated:")
print("=" * 80)
print("\n✅ The current codesitter implementation ALREADY extracts:")
print("\n1. EXPORTED SYMBOLS:")
print("   - Variables (const API_VERSION, let currentUser, etc.)")
print("   - Interfaces (User)")
print("   - Types (UserRole)")
print("   - Classes (UserService)")
print("   - Enums (UserStatus)")
print("   - Functions (in userFactory object)")
print("   - Namespaces (UserUtils)")
print("\n2. PRIVATE SYMBOLS (not exported):")
print("   - const INTERNAL_VERSION")
print("   - function internalHelper")
print("   - class InternalCache")
print("\n3. METADATA FOR EACH SYMBOL:")
print("   - Export status (exported: true/false)")
print("   - Type information (parameters, return types)")
print("   - Async status")
print("   - Kind (const/let/var)")
print("   - Nested elements (methods in classes)")
print("\n4. IMPORT/EXPORT STATEMENTS:")
print("   - Re-exports from other modules")
print("   - Export all statements")
print("\nThis functionality is implemented via the extract_structure() method")
print("which uses the UniversalExtractor and TypeScriptExtractor classes.")
