import sys
sys.path.insert(0, '/Users/mustafaacar/codesitter/src')

from codesitter.cli.commands.analyze import _ensure_initialized, file
from pathlib import Path
import json
import click

# Initialize
_ensure_initialized()

# Create a mock context and run the command
ctx = click.Context(click.Command('file'))
output = []

# Monkey patch console.print to capture output
from codesitter.cli.commands import analyze
original_print = analyze.console.print
analyze.console.print = lambda x: output.append(x)

try:
    # Run the analyze file command
    ctx.invoke(file, file_path='test_calls.ts', output_json=True)

    # Parse and print the result
    result = json.loads(output[0])
    print(json.dumps(result, indent=2))

    # Verify the structure
    print("\n--- Verification ---")
    for elem in result.get("structure", []):
        if elem["type"] == "function":
            func_name = elem["name"]
            calls = elem.get("metadata", {}).get("calls", [])
            print(f"Function '{func_name}' has {len(calls)} calls:")
            for call in calls:
                print(f"  - {call['callee']}() at line {call['line']}")

finally:
    # Restore original print
    analyze.console.print = original_print
