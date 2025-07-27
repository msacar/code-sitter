#!/usr/bin/env python3
"""
CLI Interface for Code-Sitter

Provides command-line interface for indexing codebases and searching through them.
"""

import click
import os
import sys
from pathlib import Path
from typing import Optional
import subprocess
import json

from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import print as rprint

from query import CodeSearchEngine, format_search_results
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

console = Console()


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
def cli(debug):
    """Code-Sitter: Real-time TypeScript code indexing and search."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)


@cli.command()
@click.option('--path', '-p', default='.', help='Path to codebase to index')
@click.option('--watch', '-w', is_flag=True, help='Watch for file changes')
@click.option('--postgres', is_flag=True, help='Use PostgreSQL for storage')
def index(path: str, watch: bool, postgres: bool):
    """Index a TypeScript codebase."""
    path = Path(path).resolve()

    if not path.exists():
        console.print(f"[red]Error: Path {path} does not exist[/red]")
        sys.exit(1)

    console.print(Panel(
        f"[bold blue]Indexing codebase at:[/bold blue] {path}\n"
        f"[bold]Storage:[/bold] {'PostgreSQL' if postgres else 'JSON file'}\n"
        f"[bold]Watch mode:[/bold] {'Enabled' if watch else 'Disabled'}",
        title="Code-Sitter Indexer"
    ))

    # Set environment variables
    if postgres:
        os.environ['USE_POSTGRES'] = 'true'
        # Check if DATABASE_URL is set
        if not os.getenv('DATABASE_URL'):
            console.print("[yellow]Warning: DATABASE_URL not set. Using default localhost[/yellow]")

    # Change to target directory
    original_dir = os.getcwd()
    os.chdir(path)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Run CocoIndex
            if watch:
                task = progress.add_task("Starting file watcher...", total=None)
                cmd = ["cocoindex", "server", str(Path(__file__).parent / "coco_flow.py")]
                console.print(f"[green]Running: {' '.join(cmd)}[/green]")
                subprocess.run(cmd)
            else:
                task = progress.add_task("Indexing files...", total=None)
                cmd = ["cocoindex", "update", str(Path(__file__).parent / "coco_flow.py")]
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    progress.update(task, completed=True)
                    console.print("[green]✓ Indexing completed successfully![/green]")

                    # Show statistics
                    if Path("code_index.json").exists():
                        with open("code_index.json", 'r') as f:
                            data = json.load(f)
                            console.print(f"[blue]Indexed {len(data)} code chunks[/blue]")

                    if Path("symbol_index.json").exists():
                        with open("symbol_index.json", 'r') as f:
                            symbols = json.load(f)
                            console.print(f"[blue]Found {len(symbols)} unique symbols[/blue]")
                else:
                    console.print(f"[red]Error during indexing:[/red]\n{result.stderr}")
                    sys.exit(1)
    finally:
        os.chdir(original_dir)


@cli.command()
@click.argument('query')
@click.option('--type', '-t',
              type=click.Choice(['symbol', 'semantic', 'calls', 'definition']),
              default='semantic',
              help='Type of search to perform')
@click.option('--limit', '-l', default=5, help='Maximum number of results')
@click.option('--threshold', default=0.5, help='Similarity threshold for semantic search')
def search(query: str, type: str, limit: int, threshold: float):
    """Search through indexed codebase."""
    try:
        engine = CodeSearchEngine()

        console.print(Panel(
            f"[bold]Query:[/bold] {query}\n"
            f"[bold]Search type:[/bold] {type}",
            title="Code Search"
        ))

        results = []

        if type == 'symbol':
            results = engine.search_symbol(query)
            _display_symbol_results(results[:limit])

        elif type == 'semantic':
            results = engine.semantic_search(query, k=limit, threshold=threshold)
            _display_semantic_results(results)

        elif type == 'calls':
            results = engine.find_function_calls(query)
            _display_call_results(results[:limit])

        elif type == 'definition':
            result = engine.get_function_definition(query)
            if result:
                _display_definition_result(result)
            else:
                console.print(f"[yellow]No definition found for '{query}'[/yellow]")

        engine.close()

    except Exception as e:
        console.print(f"[red]Error during search: {e}[/red]")
        logger.exception("Search error")
        sys.exit(1)


@cli.command()
@click.argument('filename')
def analyze(filename: str):
    """Analyze dependencies for a specific file."""
    try:
        engine = CodeSearchEngine()

        console.print(Panel(
            f"[bold]Analyzing:[/bold] {filename}",
            title="Dependency Analysis"
        ))

        deps = engine.analyze_dependencies(filename)

        # Display imports
        if deps['imports']:
            console.print("\n[bold blue]Imports:[/bold blue]")
            for imp in deps['imports']:
                console.print(f"  • {imp}")
        else:
            console.print("\n[yellow]No imports found[/yellow]")

        # Display exports
        if deps['exports']:
            console.print("\n[bold green]Exports:[/bold green]")
            for exp in deps['exports']:
                console.print(f"  • {exp}")
        else:
            console.print("\n[yellow]No exports found[/yellow]")

        engine.close()

    except Exception as e:
        console.print(f"[red]Error during analysis: {e}[/red]")
        logger.exception("Analysis error")
        sys.exit(1)


@cli.command()
def stats():
    """Show statistics about the indexed codebase."""
    symbol_index_path = Path("symbol_index.json")
    code_index_path = Path("code_index.json")

    if not symbol_index_path.exists() and not code_index_path.exists():
        console.print("[yellow]No index files found. Run 'code-sitter index' first.[/yellow]")
        return

    stats_table = Table(title="Codebase Statistics")
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="green")

    # Load and analyze indices
    if code_index_path.exists():
        with open(code_index_path, 'r') as f:
            code_data = json.load(f)

            # Count unique files
            files = set()
            total_lines = 0
            node_types = {}

            for item in code_data:
                chunk_data = item.get('chunk_data', {})
                files.add(chunk_data.get('filename', ''))

                # Count node types
                node_type = chunk_data.get('node_type', 'unknown')
                node_types[node_type] = node_types.get(node_type, 0) + 1

                # Estimate lines
                start = chunk_data.get('start_line', 0)
                end = chunk_data.get('end_line', 0)
                if end > start:
                    total_lines += (end - start)

            stats_table.add_row("Total files", str(len(files)))
            stats_table.add_row("Total chunks", str(len(code_data)))
            stats_table.add_row("Estimated lines", str(total_lines))

    if symbol_index_path.exists():
        with open(symbol_index_path, 'r') as f:
            symbols = json.load(f)
            stats_table.add_row("Unique symbols", str(len(symbols)))

            # Find most referenced symbols
            symbol_counts = [(name, len(locs)) for name, locs in symbols.items()]
            symbol_counts.sort(key=lambda x: x[1], reverse=True)

            if symbol_counts:
                top_symbols = ", ".join([f"{name} ({count})"
                                       for name, count in symbol_counts[:5]])
                stats_table.add_row("Top symbols", top_symbols)

    console.print(stats_table)

    # Show node type distribution if available
    if 'node_types' in locals() and node_types:
        type_table = Table(title="Code Structure Distribution")
        type_table.add_column("Node Type", style="cyan")
        type_table.add_column("Count", style="green")

        for node_type, count in sorted(node_types.items(),
                                      key=lambda x: x[1],
                                      reverse=True)[:10]:
            type_table.add_row(node_type, str(count))

        console.print("\n")
        console.print(type_table)


def _display_symbol_results(results):
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


def _display_semantic_results(results):
    """Display semantic search results."""
    if not results:
        console.print("[yellow]No results found[/yellow]")
        return

    for i, result in enumerate(results):
        console.print(f"\n[bold]Result {i+1}[/bold] (similarity: {result['similarity']:.3f})")
        console.print(f"[dim]{result['filename']}:{result['start_line']}-{result['end_line']}[/dim]")

        # Show code with syntax highlighting
        code_text = result['text'][:300] + "..." if len(result['text']) > 300 else result['text']
        syntax = Syntax(code_text, "typescript", theme="monokai", line_numbers=True,
                       start_line=result['start_line'])
        console.print(syntax)

        if result.get('symbols'):
            console.print(f"[blue]Symbols:[/blue] {', '.join(result['symbols'])}")


def _display_call_results(results):
    """Display function call results."""
    if not results:
        console.print("[yellow]No function calls found[/yellow]")
        return

    table = Table(title="Function Call Sites")
    table.add_column("File", style="green")
    table.add_column("Line", style="yellow")
    table.add_column("Call Context", style="cyan")

    for result in results:
        table.add_row(
            result['filename'],
            str(result['line']),
            result['call_context']
        )

    console.print(table)


def _display_definition_result(result):
    """Display function definition result."""
    console.print(f"\n[bold]Function Definition[/bold]")
    console.print(f"[dim]{result.get('filename', 'Unknown')}:{result.get('line_start', '?')}-{result.get('line_end', '?')}[/dim]")

    # Show full context
    if 'chunk_text' in result:
        syntax = Syntax(result['chunk_text'], "typescript", theme="monokai",
                       line_numbers=True, start_line=result.get('line_start', 1))
        console.print(syntax)


if __name__ == '__main__':
    cli()
