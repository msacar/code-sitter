"""Search command for Code-Sitter CLI."""

import click
import sys
import logging
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

from ...query import CodeSearchEngine
from ..utils import (
    display_symbol_results,
    display_semantic_results,
    display_call_results,
    display_definition_result
)

console = Console()
logger = logging.getLogger(__name__)


@click.command()
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
            display_symbol_results(results[:limit], console)

        elif type == 'semantic':
            results = engine.semantic_search(query, k=limit, threshold=threshold)
            display_semantic_results(results, console)

        elif type == 'calls':
            results = engine.find_function_calls(query)
            display_call_results(results[:limit], console)

        elif type == 'definition':
            result = engine.get_function_definition(query)
            if result:
                display_definition_result(result, console)
            else:
                console.print(f"[yellow]No definition found for '{query}'[/yellow]")

        engine.close()

    except Exception as e:
        console.print(f"[red]Error during search: {e}[/red]")
        logger.exception("Search error")
        sys.exit(1)
