#!/usr/bin/env python3
"""Test the updated analyze command with line content."""

import json
import subprocess
import sys

def test_analyze_with_line_content():
    """Run analyze command and display the output."""
    try:
        # Run the analyze command
        result = subprocess.run(
            [sys.executable, "-m", "codesitter", "analyze", "file", "test_calls.ts", "--json"],
            capture_output=True,
            text=True,
            cwd="/Users/mustafaacar/codesitter"
        )

        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return

        # Parse and pretty-print the JSON
        output = json.loads(result.stdout)

        print("=== ANALYZE OUTPUT WITH LINE CONTENT ===\n")

        # Show a few examples of calls with line content
        print("Sample Calls with Line Content:")
        for call in output.get("calls", [])[:3]:
            print(f"\nLine {call['line']}: {call.get('line_content', 'N/A')}")
            print(f"  Caller: {call['caller']}")
            print(f"  Callee: {call['callee']}({', '.join(call['arguments'])})")
            if 'context' in call:
                print(f"  Context preview: {call['context'][:50]}...")

        print("\n\nSample Imports with Line Content:")
        for imp in output.get("imports", []):
            print(f"\nLine {imp['line']}: {imp.get('line_content', 'N/A')}")
            print(f"  From: {imp['source']}")
            print(f"  Items: {', '.join(imp['items'])}")

        print("\n\nSample Structure Elements:")
        for elem in output.get("structure", [])[:2]:
            print(f"\n{elem['type'].capitalize()}: {elem['name']} (lines {elem['lines']})")
            print(f"  First line: {elem.get('first_line', 'N/A')}")
            if elem.get('text'):
                preview = elem['text'][:100].replace('\n', ' ')
                print(f"  Text preview: {preview}...")

        # Also save full output for inspection
        with open("analyze_output_with_line_content.json", "w") as f:
            json.dump(output, f, indent=2)
        print("\n\nFull output saved to: analyze_output_with_line_content.json")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_analyze_with_line_content()
