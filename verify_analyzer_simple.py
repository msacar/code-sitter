#!/usr/bin/env python3
"""
Verify analyzer_simple flow can be loaded and used by CocoIndex.
"""

import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

def test_flow_loading():
    """Test that the flow can be loaded properly."""
    print("=== Testing analyzer_simple Flow Loading ===\n")

    # Set required environment
    os.environ['USE_POSTGRES'] = 'true'
    if not os.environ.get('COCOINDEX_DATABASE_URL'):
        os.environ['COCOINDEX_DATABASE_URL'] = 'postgresql://cocoindex:cocoindex@localhost:5432/cocoindex'

    try:
        # Import CocoIndex
        import cocoindex
        print("✓ CocoIndex imported")

        # Initialize
        cocoindex.init()
        print("✓ CocoIndex initialized")

        # Import our flow
        from src.codesitter.flows import analyzer_simple
        print("✓ analyzer_simple flow imported")

        # Get the flow
        flow = analyzer_simple.flow
        print(f"✓ Flow loaded: {flow.name}")

        # Check flow structure
        print("\nFlow details:")
        print(f"  Name: {flow.name}")
        print(f"  Type: {type(flow)}")

        # Try to get flow info (this validates the flow definition)
        try:
            flows = flow.flows()
            print(f"  Number of flows: {len(flows)}")
            print("✓ Flow structure is valid")
        except Exception as e:
            print(f"✗ Flow structure error: {e}")
            return False

        print("\n✅ SUCCESS: analyzer_simple flow is properly configured!")
        print("\nNext steps:")
        print("1. Run: cocoindex setup src/codesitter/flows/analyzer_simple.py")
        print("2. Run: codesitter index -p /your/project --flow analyzer_simple --postgres")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_flow_loading()
    sys.exit(0 if success else 1)
