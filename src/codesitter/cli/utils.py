"""Utility functions for CLI display and formatting."""

from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel


def display_symbol_results(results: List[Dict[str, Any]], console: Console):
    """Display symbol search results."""
    if not results:
        console.print("[yellow]No symbols found[/yellow]")
        return

    table = Table(title="Symbol Search Results")
    table.add_column("Symbol", style="cyan")
    table.add_column("File", style="green")
    table.add_column("Lines", style="yellow")

    for result in results:
        symbol = result.get('matched_symbol', 'Symbol')
        table.add_row(
            symbol,
            result.get('filename', 'Unknown'),
            f"{result.get('line_start', '?')}-{result.get('line_end', '?')}"
        )

    console.print(table)


def display_semantic_results(results: List[Dict[str, Any]], console: Console):
    """Display semantic search results."""
    if not results:
        console.print("[yellow]No results found[/yellow]")
        return

    console.print(f"\n[bold]Found {len(results)} relevant code chunks:[/bold]\n")

    for i, result in enumerate(results, 1):
        filename = result.get('filename', 'Unknown')
        score = result.get('score', 0.0)
        lines = f"{result.get('line_start', '?')}-{result.get('line_end', '?')}"
        text = result.get('text', '')[:200] + "..." if len(result.get('text', '')) > 200 else result.get('text', '')

        console.print(Panel(
            f"[cyan]File:[/cyan] {filename}\n"
            f"[cyan]Lines:[/cyan] {lines}\n"
            f"[cyan]Score:[/cyan] {score:.3f}\n\n"
            f"{text}",
            title=f"Result {i}"
        ))


def display_call_results(results: List[Dict[str, Any]], console: Console):
    """Display function call results."""
    if not results:
        console.print("[yellow]No function calls found[/yellow]")
        return

    table = Table(title="Function Call Sites")
    table.add_column("Caller", style="cyan")
    table.add_column("File", style="green")
    table.add_column("Line", style="yellow")
    table.add_column("Arguments", style="magenta")

    for result in results:
        table.add_row(
            result.get('caller', 'Unknown'),
            result.get('filename', 'Unknown'),
            str(result.get('line', '?')),
            ", ".join(result.get('arguments', []))
        )

    console.print(table)


def display_definition_result(result: Dict[str, Any], console: Console):
    """Display function definition result."""
    filename = result.get('filename', 'Unknown')
    lines = f"{result.get('line_start', '?')}-{result.get('line_end', '?')}"
    code = result.get('text', '')

    console.print(Panel(
        f"[cyan]File:[/cyan] {filename}\n"
        f"[cyan]Lines:[/cyan] {lines}",
        title="Function Definition"
    ))

    # Use syntax highlighting for the code
    syntax = Syntax(code, "typescript", theme="monokai", line_numbers=True)
    console.print(syntax)


def format_search_results(results: List[Dict[str, Any]], search_type: str) -> str:
    """Format search results for display (legacy function for compatibility)."""
    if not results:
        return "No results found."

    output = []
    for i, result in enumerate(results, 1):
        output.append(f"\n--- Result {i} ---")
        output.append(f"File: {result.get('filename', 'Unknown')}")
        output.append(f"Lines: {result.get('line_start', '?')}-{result.get('line_end', '?')}")

        if search_type == 'semantic':
            output.append(f"Score: {result.get('score', 0.0):.3f}")

        if 'text' in result:
            output.append(f"Code:\n{result['text'][:200]}...")

    return "\n".join(output)
