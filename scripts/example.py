#!/usr/bin/env python3
"""
codesitter Example Usage

This script demonstrates how to use codesitter programmatically
for indexing and searching TypeScript codebases.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from codesitter.query import CodeSearchEngine
from rich import print as rprint
from rich.console import Console
from rich.syntax import Syntax

# Load environment variables
load_dotenv()

console = Console()


def example_symbol_search():
    """Example: Search for a specific symbol/function."""
    console.print("\n[bold blue]Example 1: Symbol Search[/bold blue]")

    engine = CodeSearchEngine()

    # Search for a function named "useState"
    results = engine.search_symbol("useState")

    if results:
        console.print(f"Found {len(results)} occurrences of 'useState':")
        for result in results[:3]:  # Show first 3
            console.print(f"  - {result['filename']}:{result['line_start']}")
    else:
        console.print("[yellow]No results found for 'useState'[/yellow]")

    engine.close()


def example_semantic_search():
    """Example: Semantic search for code patterns."""
    console.print("\n[bold blue]Example 2: Semantic Search[/bold blue]")

    engine = CodeSearchEngine()

    # Search for authentication-related code
    query = "user authentication login validation"
    results = engine.semantic_search(query, k=3, threshold=0.4)

    console.print(f"Searching for: '{query}'")

    for i, result in enumerate(results):
        console.print(f"\n[green]Result {i+1}[/green] (similarity: {result['similarity']:.3f})")
        console.print(f"File: {result['filename']}")

        # Show code snippet with syntax highlighting
        code = result['text'][:200] + "..." if len(result['text']) > 200 else result['text']
        syntax = Syntax(code, "typescript", theme="monokai")
        console.print(syntax)


def example_find_function_calls():
    """Example: Find where a function is called."""
    console.print("\n[bold blue]Example 3: Find Function Calls[/bold blue]")

    engine = CodeSearchEngine()

    # Find all calls to a specific function
    function_name = "processData"
    calls = engine.find_function_calls(function_name)

    console.print(f"Looking for calls to '{function_name}':")

    if calls:
        for call in calls[:5]:  # Show first 5
            console.print(f"\n[cyan]{call['filename']}:{call['line']}[/cyan]")
            console.print(f"  → {call['call_context']}")
    else:
        console.print(f"[yellow]No calls found for '{function_name}'[/yellow]")

    engine.close()


def example_analyze_file():
    """Example: Analyze imports/exports of a file."""
    console.print("\n[bold blue]Example 4: Analyze File Dependencies[/bold blue]")

    engine = CodeSearchEngine()

    # Example file to analyze (you'd replace this with an actual file)
    filename = "src/components/Button.tsx"

    console.print(f"Analyzing: {filename}")
    deps = engine.analyze_dependencies(filename)

    if deps['imports']:
        console.print("\n[green]Imports:[/green]")
        for imp in deps['imports'][:5]:
            console.print(f"  • {imp}")

    if deps['exports']:
        console.print("\n[blue]Exports:[/blue]")
        for exp in deps['exports'][:5]:
            console.print(f"  • {exp}")

    engine.close()


def main():
    """Run all examples."""
    console.print("[bold]codesitter Examples[/bold]\n")

    # Check if index exists
    if not Path("code_index.json").exists() and not os.getenv("DATABASE_URL"):
        console.print("[red]Error: No index found![/red]")
        console.print("Run 'codesitter index' first to index your codebase.")
        sys.exit(1)

    try:
        # Run examples
        example_symbol_search()
        example_semantic_search()
        example_find_function_calls()
        example_analyze_file()

        console.print("\n[green]✓ All examples completed![/green]")
        console.print("\nTo use codesitter CLI, run:")
        console.print("  [cyan]codesitter --help[/cyan]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
