#!/usr/bin/env python3
"""
Standalone analyzer runner - Run codesitter analyzers independently
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Any
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codesitter.analyzers import (
    get_analyzer,
    get_registry,
    register_defaults,
    auto_discover_analyzers
)
from codesitter.analyzers.base import CodeChunk


def analyze_file(file_path: str, verbose: bool = False) -> Dict[str, Any]:
    """Analyze a single file and return results."""

    # Get analyzer for file
    analyzer = get_analyzer(file_path)
    if not analyzer:
        return {
            "error": f"No analyzer found for {file_path}",
            "file": file_path
        }

    # Read file content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {
            "error": f"Could not read file: {e}",
            "file": file_path
        }

    # Create chunk (whole file as one chunk for simplicity)
    chunk = CodeChunk(
        text=content,
        filename=file_path,
        start_line=0,
        end_line=len(content.split('\n')),
        node_type="file",
        symbols=[]
    )

    results = {
        "file": file_path,
        "language": analyzer.language_name,
        "analyzer": analyzer.__class__.__name__,
        "metadata": {},
        "calls": [],
        "imports": []
    }

    # Extract custom metadata
    try:
        metadata = analyzer.extract_custom_metadata(chunk)
        results["metadata"] = metadata
        if verbose:
            print(f"  ✓ Extracted metadata: {metadata}")
    except Exception as e:
        results["metadata_error"] = str(e)
        if verbose:
            print(f"  ✗ Metadata extraction failed: {e}")

    # Extract call relationships
    try:
        calls = list(analyzer.extract_call_relationships(chunk))
        results["calls"] = [
            {
                "caller": call.caller,
                "callee": call.callee,
                "arguments": call.arguments,
                "line": call.line,
                "column": call.column
            }
            for call in calls
        ]
        if verbose:
            print(f"  ✓ Found {len(calls)} function calls")
    except Exception as e:
        results["calls_error"] = str(e)
        if verbose:
            print(f"  ✗ Call extraction failed: {e}")

    # Extract import relationships
    try:
        imports = list(analyzer.extract_import_relationships(chunk))
        results["imports"] = [
            {
                "from": imp.imported_from,
                "items": imp.imported_items,
                "type": imp.import_type,
                "line": imp.line
            }
            for imp in imports
        ]
        if verbose:
            print(f"  ✓ Found {len(imports)} imports")
    except Exception as e:
        results["imports_error"] = str(e)
        if verbose:
            print(f"  ✗ Import extraction failed: {e}")

    return results


def analyze_directory(dir_path: str, pattern: str = None, verbose: bool = False) -> List[Dict[str, Any]]:
    """Analyze all matching files in a directory."""
    path = Path(dir_path)
    results = []

    # Get supported extensions
    registry = get_registry()
    supported_exts = registry.list_supported_extensions()

    # Find files
    if pattern:
        files = list(path.glob(pattern))
    else:
        files = []
        for ext in supported_exts:
            files.extend(path.rglob(f"*{ext}"))

    # Filter out common directories to skip
    skip_dirs = {'node_modules', '.git', 'dist', 'build', '__pycache__', '.venv', 'venv'}
    files = [f for f in files if not any(skip in str(f) for skip in skip_dirs)]

    print(f"Found {len(files)} files to analyze")

    for i, file_path in enumerate(files):
        print(f"\n[{i+1}/{len(files)}] Analyzing {file_path.relative_to(path)}...")
        result = analyze_file(str(file_path), verbose)
        results.append(result)

    return results


def print_summary(results: List[Dict[str, Any]]):
    """Print a summary of analysis results."""
    print("\n" + "="*60)
    print("ANALYSIS SUMMARY")
    print("="*60)

    # Count by language
    by_language = {}
    for r in results:
        lang = r.get("language", "unknown")
        by_language[lang] = by_language.get(lang, 0) + 1

    print("\nFiles by language:")
    for lang, count in sorted(by_language.items()):
        print(f"  {lang}: {count}")

    # Count features
    total_calls = sum(len(r.get("calls", [])) for r in results)
    total_imports = sum(len(r.get("imports", [])) for r in results)

    print(f"\nTotal function calls found: {total_calls}")
    print(f"Total imports found: {total_imports}")

    # TypeScript/React specific
    ts_results = [r for r in results if r.get("language") in ["typescript", "javascript"]]
    if ts_results:
        react_components = sum(1 for r in ts_results if r.get("metadata", {}).get("is_react_component"))
        async_functions = sum(1 for r in ts_results if r.get("metadata", {}).get("has_async_functions"))
        test_files = sum(1 for r in ts_results if r.get("metadata", {}).get("is_test_file"))

        print(f"\nTypeScript/JavaScript specific:")
        print(f"  React components: {react_components}")
        print(f"  Files with async functions: {async_functions}")
        print(f"  Test files: {test_files}")

    # Errors
    errors = [r for r in results if "error" in r or "metadata_error" in r or "calls_error" in r or "imports_error" in r]
    if errors:
        print(f"\n⚠️  {len(errors)} files had errors during analysis")


def main():
    parser = argparse.ArgumentParser(description="Run codesitter analyzers standalone")
    parser.add_argument("path", help="File or directory to analyze")
    parser.add_argument("-p", "--pattern", help="File pattern to match (e.g., '**/*.ts')")
    parser.add_argument("-o", "--output", help="Output JSON file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON output")

    args = parser.parse_args()

    # Initialize analyzers
    print("Initializing language analyzers...")
    register_defaults()
    auto_discover_analyzers()

    registry = get_registry()
    supported = registry.list_supported_extensions()
    print(f"Supported extensions: {', '.join(supported.keys())}")

    # Analyze
    path = Path(args.path)
    if path.is_file():
        results = [analyze_file(str(path), args.verbose)]
    else:
        results = analyze_directory(str(path), args.pattern, args.verbose)

    # Output
    if args.output:
        with open(args.output, 'w') as f:
            if args.pretty:
                json.dump(results, f, indent=2)
            else:
                json.dump(results, f)
        print(f"\nResults written to {args.output}")

    # Summary
    print_summary(results)


if __name__ == "__main__":
    main()
