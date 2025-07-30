#!/usr/bin/env python3
"""Test script to verify analyzer flows work correctly."""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cocoindex import init
from src.codesitter.flows import analyzer_aware, analyzer_advanced

def test_flows():
    """Test that flows can be loaded and initialized."""
    print("Testing analyzer flows...")

    # Initialize CocoIndex
    init()

    # Test analyzer_aware flow
    try:
        flow1 = analyzer_aware.flow
        print("✓ analyzer_aware flow loaded successfully")
        print(f"  Flow name: {flow1.name}")
    except Exception as e:
        print(f"✗ Error loading analyzer_aware flow: {e}")

    # Test analyzer_advanced flow
    try:
        flow2 = analyzer_advanced.flow
        print("✓ analyzer_advanced flow loaded successfully")
        print(f"  Flow name: {flow2.name}")
    except Exception as e:
        print(f"✗ Error loading analyzer_advanced flow: {e}")

    print("\nNote: To actually run these flows, use:")
    print("  cocoindex setup <flow_file>")
    print("  cocoindex update <flow_file>")

if __name__ == "__main__":
    test_flows()
