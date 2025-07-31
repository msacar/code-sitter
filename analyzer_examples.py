#!/usr/bin/env python3
"""
Example: Using analyzer-cli.py in scripts

Shows how to integrate the analyzer CLI into your workflow.
"""

import subprocess
import json
import sys
from pathlib import Path


def run_analyzer(command: list) -> dict:
    """Run codesitter analyze and parse JSON output."""
    # Ensure we're using the analyze file command with JSON
    if len(command) >= 3 and command[1] == "analyze" and command[2] != "list":
        # Insert "file" if not present
        if command[2] != "file" and command[2] != "directory":
            command.insert(2, "file")
        # Add --json flag if not present
        if "--json" not in command:
            command.append("--json")

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return {}

    try:
        return json.loads(result.stdout)
    except:
        return {}


def find_react_components(directory: str):
    """Find all React components in a directory."""
    print(f"🔍 Finding React components in {directory}")

    # Get all TypeScript files
    ts_files = list(Path(directory).rglob("*.tsx"))
    ts_files.extend(Path(directory).rglob("*.jsx"))

    react_components = []

    for file_path in ts_files:
        result = run_analyzer(["codesitter", "analyze", str(file_path)])

        if result.get("metadata", {}).get("is_react_component"):
            react_components.append({
                "file": str(file_path),
                "has_jsx": result["metadata"].get("has_jsx_elements", False),
                "imports": [imp["source"] for imp in result.get("imports", [])]
            })

    print(f"\nFound {len(react_components)} React components:")
    for comp in react_components:
        print(f"  📁 {comp['file']}")
        if "react" in comp["imports"]:
            print(f"     ✓ Imports React")
        if comp["has_jsx"]:
            print(f"     ✓ Contains JSX")


def analyze_dependencies(file_path: str):
    """Analyze what a file depends on."""
    print(f"📦 Analyzing dependencies for {file_path}")

    result = run_analyzer(["codesitter", "analyze", file_path])

    if not result:
        return

    imports = result.get("imports", [])

    # Categorize imports
    external = []
    internal = []

    for imp in imports:
        source = imp["source"]
        if source.startswith("."):
            internal.append(source)
        else:
            external.append(source)

    print(f"\nExternal dependencies ({len(external)}):")
    for dep in sorted(set(external)):
        print(f"  📦 {dep}")

    print(f"\nInternal dependencies ({len(internal)}):")
    for dep in sorted(set(internal)):
        print(f"  📁 {dep}")


def find_unused_functions(file_path: str):
    """Find potentially unused functions (basic check)."""
    print(f"🔍 Finding potentially unused functions in {file_path}")

    with open(file_path, 'r') as f:
        content = f.read()

    result = run_analyzer(["codesitter", "analyze", file_path])

    if not result:
        return

    # Get all function calls
    called_functions = set()
    for call in result.get("calls", []):
        called_functions.add(call["callee"])

    # Check metadata for functions
    metadata = result.get("metadata", {})

    # This is a simple check - in real use, you'd need to check across files
    print("\nNote: This only checks within the same file!")
    print("Functions that might be unused:")

    # For TypeScript files, we can check the content
    import re
    function_pattern = r'(?:export\s+)?(?:async\s+)?function\s+(\w+)'
    functions = re.findall(function_pattern, content)

    for func_name in functions:
        if func_name not in called_functions:
            # Check if it's exported
            if f"export.*function.*{func_name}" in content:
                print(f"  ⚠️  {func_name} (exported - might be used elsewhere)")
            else:
                print(f"  ❌ {func_name} (not called in this file)")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  ./analyzer_examples.py react-components <directory>")
        print("  ./analyzer_examples.py dependencies <file>")
        print("  ./analyzer_examples.py unused <file>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "react-components" and len(sys.argv) > 2:
        find_react_components(sys.argv[2])
    elif command == "dependencies" and len(sys.argv) > 2:
        analyze_dependencies(sys.argv[2])
    elif command == "unused" and len(sys.argv) > 2:
        find_unused_functions(sys.argv[2])
    else:
        print("Invalid command or missing arguments")


if __name__ == "__main__":
    main()
