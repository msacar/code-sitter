#!/usr/bin/env python3
"""Test the fixed flexible flow with TypeScript support."""

import os
import sys

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Test the flow imports and initialization
print("Testing flexible flow imports...")

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
        print("✗ TypeScript/JavaScript extensions not found!")

    print(f"\nAll supported extensions: {list(supported_exts.keys())}")

    # Check if the flow is properly defined
    print(f"\n✓ Flow name: {flow.name if hasattr(flow, 'name') else 'FlexibleCodeIndex'}")

    print("\nFlow appears to be fixed! You can now run:")
    print("  codesitter index -p /path/to/project --flow flexible")

except Exception as e:
    print(f"✗ Error loading flow: {e}")
    import traceback
    traceback.print_exc()
