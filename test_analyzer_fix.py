#!/usr/bin/env python3
"""Test the parser fix for tree-sitter."""

import sys
sys.path.insert(0, '/Users/mustafaacar/codesitter/src')

from codesitter.analyzers import get_analyzer
from codesitter.analyzers.base import CodeChunk

def test_analyzer():
    """Test that analyzers can parse code without errors."""

    # Test TypeScript
    print("Testing TypeScript analyzer...")
    ts_code = """
    function fetchUserData(userId: string): Promise<User> {
        return fetch(`/api/users/${userId}`).then(r => r.json());
    }
    """

    ts_analyzer = get_analyzer("test.ts")
    if ts_analyzer:
        print(f"Got analyzer: {ts_analyzer.language_name}")

        chunk = CodeChunk(
            text=ts_code,
            filename="test.ts",
            start_line=0,
            end_line=5,
            node_type="",
            symbols=[]
        )

        try:
            # Test call extraction
            calls = list(ts_analyzer.extract_call_relationships(chunk))
            print(f"✓ Extracted {len(calls)} function calls")
            for call in calls:
                print(f"  - {call.caller} calls {call.callee}")

            # Test metadata extraction
            metadata = ts_analyzer.extract_custom_metadata(chunk)
            print(f"✓ Extracted metadata: {metadata}")

        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    # Test Python
    print("\nTesting Python analyzer...")
    py_code = """
def process_data(items):
    result = []
    for item in items:
        processed = transform(item)
        result.append(processed)
    return result
"""

    py_analyzer = get_analyzer("test.py")
    if py_analyzer:
        print(f"Got analyzer: {py_analyzer.language_name}")

        chunk = CodeChunk(
            text=py_code,
            filename="test.py",
            start_line=0,
            end_line=7,
            node_type="",
            symbols=[]
        )

        try:
            calls = list(py_analyzer.extract_call_relationships(chunk))
            print(f"✓ Extracted {len(calls)} function calls")
            for call in calls:
                print(f"  - {call.caller} calls {call.callee}")

            metadata = py_analyzer.extract_custom_metadata(chunk)
            print(f"✓ Extracted metadata: {metadata}")

        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    print("\n✓ All tests passed!")
    return True

if __name__ == "__main__":
    test_analyzer()
