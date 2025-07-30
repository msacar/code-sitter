"""Analyze command for codesitter CLI."""

import click
import sys
import logging
from rich.console import Console
from rich.panel import Panel

from ...query import CodeSearchEngine

console = Console()
logger = logging.getLogger(__name__)


@click.command()
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
