#!/usr/bin/env python3
"""Test the fixed flexible flow after applying the DataSlice fixes."""

import os
import sys

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Testing fixed flexible flow...")
print("=" * 60)

try:
    from codesitter.flows.flexible import flexible_code_index_flow, flow
    print("✓ Flow imports successful")

    # Check if analyzers are loaded
    from codesitter.analyzers import get_registry
    registry = get_registry()
    supported_exts = registry.list_supported_extensions()
    print(f"✓ Loaded analyzers for {len(supported_exts)} file extensions")

    # Check if TypeScript/JavaScript is supported
    ts_js_exts = ['.ts', '.tsx', '.js', '.jsx']
    supported_ts_js = [ext for ext in ts_js_exts if ext in supported_exts]

    if supported_ts_js:
        print(f"✓ TypeScript/JavaScript support: {supported_ts_js}")
    else:
        print("⚠ TypeScript/JavaScript extensions not found in registry")
        print("  The default analyzers will be used as fallback")

    print(f"\n✓ Flow name: {flow.name if hasattr(flow, 'name') else 'FlexibleCodeIndex'}")

    print("\n" + "=" * 60)
    print("Flow fixes applied:")
    print("- Removed DataSlice logging outside row context")
    print("- Added debug logging inside row context")
    print("- Fixed f-string quote nesting")

    print("\nYou can now run:")
    print("  codesitter index -p /Users/mustafaacar/retter/shortlink --flow flexible")

except Exception as e:
    print(f"✗ Error loading flow: {e}")
    import traceback
    traceback.print_exc()
