"""Index command for codesitter CLI."""

import click
import os
import sys
import subprocess
import json
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from ..config import BASIC_FLOW_PATH, ENHANCED_FLOW_PATH, FLEXIBLE_FLOW_PATH, SIMPLE_FLOW_PATH, MINIMAL_FLEXIBLE_FLOW_PATH

console = Console()


@click.command()
@click.option('--path', '-p', default='.', help='Path to codebase to index')
@click.option('--watch', '-w', is_flag=True, help='Watch for file changes')
@click.option('--postgres', is_flag=True, help='Use PostgreSQL for storage')
@click.option('--flow', '-f',
              type=click.Choice(['basic', 'simple', 'enhanced', 'flexible', 'minimal_flexible']),
              default='simple',
              help='Which flow to use for indexing')
def index(path: str, watch: bool, postgres: bool, flow: str):
    """Index a codebase with pluggable language analyzers."""
    path = Path(path).resolve()

    if not path.exists():
        console.print(f"[red]Error: Path {path} does not exist[/red]")
        sys.exit(1)

    # Select the appropriate flow
    flow_map = {
        'basic': BASIC_FLOW_PATH,
        'simple': SIMPLE_FLOW_PATH,
        'enhanced': ENHANCED_FLOW_PATH,
        'flexible': FLEXIBLE_FLOW_PATH,
        'minimal_flexible': MINIMAL_FLEXIBLE_FLOW_PATH
    }
    flow_path = flow_map[flow]

    console.print(Panel(
        f"[bold blue]Indexing codebase at:[/bold blue] {path}\n"
        f"[bold]Storage:[/bold] {'PostgreSQL' if postgres else 'JSON file'}\n"
        f"[bold]Watch mode:[/bold] {'Enabled' if watch else 'Disabled'}\n"
        f"[bold]Flow:[/bold] {flow} ({flow_path.name})",
        title="codesitter Indexer"
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
                cmd = ["cocoindex", "server", str(flow_path)]
                console.print(f"[green]Running: {' '.join(cmd)}[/green]")
                subprocess.run(cmd)
            else:
                task = progress.add_task("Indexing files...", total=None)
                cmd = ["cocoindex", "update", str(flow_path)]
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


@click.command()
@click.option('--path', '-p', default='.', help='Path to codebase to watch')
@click.option('--postgres', is_flag=True, help='Use PostgreSQL for storage')
def watch(path: str, postgres: bool):
    """Watch a codebase for changes and auto-index."""
    # This is essentially index with watch=True
    ctx = click.get_current_context()
    ctx.invoke(index, path=path, watch=True, postgres=postgres)
