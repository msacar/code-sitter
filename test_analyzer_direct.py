#!/usr/bin/env python3
"""Direct test of TypeScript analyzer on user's file."""

import sys
import os

# Add codesitter to path
sys.path.insert(0, '/Users/mustafaacar/codesitter/src')

# Change to user's project directory
os.chdir('/Users/mustafaacar/retter/shortlink')

from codesitter.analyzers import get_analyzer, register_defaults, auto_discover_analyzers
from codesitter.analyzers.base import CodeChunk

# Initialize analyzers
register_defaults()
auto_discover_analyzers()

# The user's file
file_path = "modules/shortlink-api/src/services/instanceService.ts"

print(f"Testing TypeScript analyzer on: {file_path}")
print("=" * 80)

if not os.path.exists(file_path):
    print(f"ERROR: File not found: {file_path}")
    sys.exit(1)

# Read file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"File loaded: {len(content)} bytes, {len(content.split('\n'))} lines")

# Get analyzer
analyzer = get_analyzer(file_path)
if not analyzer:
    print("ERROR: No analyzer found for TypeScript")
    sys.exit(1)

print(f"Using analyzer: {analyzer.__class__.__name__}")

# Create chunk
chunk = CodeChunk(
    text=content,
    filename=file_path,
    start_line=1,
    end_line=len(content.split('\n')),
    node_type="file",
    symbols=[],
    metadata={}
)

# Extract imports
print("\nImports:")
print("-" * 40)
try:
    imports = list(analyzer.extract_import_relationships(chunk))
    if imports:
        for imp in imports:
            print(f"  Line {imp.line}: {imp.imported_from}")
            if imp.imported_items:
                print(f"    Items: {', '.join(imp.imported_items)}")
    else:
        print("  (none found)")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()

# Extract function calls
print("\nFunction Calls:")
print("-" * 40)
try:
    calls = list(analyzer.extract_call_relationships(chunk))
    if calls:
        # Group by caller
        calls_by_caller = {}
        for call in calls:
            caller = call.caller or '<module>'
            if caller not in calls_by_caller:
                calls_by_caller[caller] = []
            calls_by_caller[caller].append(call)

        for caller, caller_calls in calls_by_caller.items():
            print(f"\n  In {caller}:")
            for call in caller_calls[:5]:  # Show first 5 calls per function
                args_str = f"({', '.join(call.arguments)})" if call.arguments else "()"
                print(f"    Line {call.line}: {call.callee}{args_str}")
            if len(caller_calls) > 5:
                print(f"    ... and {len(caller_calls) - 5} more")
    else:
        print("  (none found)")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()

# Extract metadata
print("\nMetadata:")
print("-" * 40)
try:
    metadata = analyzer.extract_custom_metadata(chunk)
    if metadata:
        for key, value in metadata.items():
            print(f"  {key}: {value}")
    else:
        print("  (none found)")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("Test complete.")
