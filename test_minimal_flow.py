#!/usr/bin/env python3
"""Test minimal flexible flow."""

import os
import sys

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Testing minimal flexible flow...")

try:
    from codesitter.flows.minimal_flexible import minimal_flexible_flow, flow
    print("✓ Minimal flow imports successful")

    print(f"✓ Flow name: {flow.name if hasattr(flow, 'name') else 'MinimalFlexibleFlow'}")

    print("\nYou can now test with:")
    print("  codesitter index -p /Users/mustafaacar/retter/shortlink --flow minimal_flexible")
    print("\nOr run directly:")
    print("  cd /Users/mustafaacar/retter/shortlink")
    print("  python -m codesitter.flows.minimal_flexible")

except Exception as e:
    print(f"✗ Error loading flow: {e}")
    import traceback
    traceback.print_exc()
