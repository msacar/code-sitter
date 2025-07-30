#!/usr/bin/env python3
"""Test the analyzer_simple flow setup."""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd):
    """Run command and print output."""
    print(f"\n> {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    return result.returncode

def main():
    """Test analyzer_simple flow."""
    print("=== Testing analyzer_simple Flow ===\n")

    # Get flow path
    flow_path = Path(__file__).parent / "src/codesitter/flows/analyzer_simple.py"

    if not flow_path.exists():
        print(f"Error: Flow not found at {flow_path}")
        return 1

    print(f"Flow path: {flow_path}")

    # Test 1: Check syntax
    print("\n1. Checking Python syntax...")
    if run_cmd([sys.executable, "-m", "py_compile", str(flow_path)]) == 0:
        print("✓ Syntax is valid")
    else:
        print("✗ Syntax error")
        return 1

    # Test 2: Try to import
    print("\n2. Testing import...")
    try:
        sys.path.insert(0, str(flow_path.parent.parent.parent))
        from src.codesitter.flows import analyzer_simple
        print("✓ Import successful")
        print(f"  Flow name: {analyzer_simple.flow.name}")
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return 1

    # Test 3: Setup flow (dry run)
    print("\n3. Testing cocoindex setup...")
    print("Run this command to set up the flow:")
    print(f"\ncocoindex setup {flow_path}")

    print("\n4. To index a project, run:")
    print("\ncodesitter index -p /path/to/project --flow analyzer_simple --postgres")

    print("\n=== Test Complete ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
