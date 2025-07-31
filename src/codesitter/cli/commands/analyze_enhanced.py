"""Enhanced analyze command with better error handling and verbose output."""

import click
import json
from pathlib import Path
from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
import traceback

from ...analyzers import get_analyzer, get_registry, auto_discover_analyzers, register_defaults
from ...analyzers.base import CodeChunk

console = Console()

# Initialize analyzer registry once at module load
_initialized = False

def _ensure_initialized():
    """Ensure analyzers are initialized only once."""
    global _initialized
    if not _initialized:
        register_defaults()
        auto_discover_analyzers()
        _initialized = True


@click.group()
def analyze():
    """Run analyzers standalone without indexing."""
    _ensure_initialized()


@analyze.command()
def list():
    """List all available analyzers and their capabilities."""
    _ensure_initialized()
    registry = get_registry()

    table = Table(title="Available Analyzers")
    table.add_column("Analyzer", style="cyan", no_wrap=True)
    table.add_column("Extensions", style="green")
    table.add_column("Capabilities", style="yellow")

    # Get analyzers by class name
    analyzer_info = {}

    # Group by analyzer class
    for ext, language in registry.list_supported_extensions().items():
        # Create a dummy filename for this extension
        dummy_file = f"dummy{ext}"
        analyzer = get_analyzer(dummy_file)

        if analyzer:
            class_name = analyzer.__class__.__name__
            if class_name not in analyzer_info:
                analyzer_info[class_name] = {
                    "extensions": [],
                    "analyzer": analyzer
                }
            analyzer_info[class_name]["extensions"].append(ext)

    # Display grouped by analyzer
    for class_name, info in analyzer_info.items():
        analyzer = info["analyzer"]
        capabilities = []

        if hasattr(analyzer, 'extract_call_relationships'):
            capabilities.append("calls")
        if hasattr(analyzer, 'extract_import_relationships'):
            capabilities.append("imports")
        if hasattr(analyzer, 'extract_custom_metadata'):
            capabilities.append("metadata")

        table.add_row(
            class_name,
            ", ".join(sorted(info["extensions"])),
            ", ".join(capabilities) or "basic only"
        )

    console.print(table)


@analyze.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option('--calls-only', is_flag=True, help='Show only function calls')
@click.option('--imports-only', is_flag=True, help='Show only imports')
@click.option('--verbose', '-v', is_flag=True, help='Show verbose output including empty sections')
def file(file_path: str, output_json: bool, calls_only: bool, imports_only: bool, verbose: bool):
    """Analyze a single file."""
    _ensure_initialized()
    path = Path(file_path)

    # Verify file exists and is readable
    if not path.exists():
        console.print(f"[red]Error: File not found: {file_path}[/red]")
        return

    if not path.is_file():
        console.print(f"[red]Error: Path is not a file: {file_path}[/red]")
        return

    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        console.print(f"[red]Error reading file: {e}[/red]")
        return

    ext = path.suffix
    analyzer = get_analyzer(str(path))  # Pass full filename, not just extension

    if not analyzer:
        console.print(f"[red]No analyzer found for {ext} files[/red]")
        return

    # Create chunk for whole file
    chunk = CodeChunk(
        text=content,
        filename=str(path),
        start_line=1,
        end_line=len(content.split('\n')),
        node_type="file",
        symbols=[],  # Empty list for now
        metadata={}
    )

    # Extract data
    result = {
        "file": str(path),
        "language": analyzer.language_name,
        "analyzer": analyzer.__class__.__name__,
        "calls": [],
        "imports": [],
        "metadata": {},
        "errors": {}
    }

    # Show file info if verbose
    if verbose and not output_json:
        console.print(f"\n[bold blue]File Info:[/bold blue]")
        console.print(f"  Size: {len(content)} bytes")
        console.print(f"  Lines: {len(content.split('\n'))}")
        console.print(f"  Extension: {ext}")

    try:
        if not imports_only:
            if verbose and not output_json:
                console.print(f"\n[dim]Extracting function calls...[/dim]")
            result["calls"] = [
                {
                    "caller": call.caller,
                    "callee": call.callee,
                    "arguments": call.arguments,
                    "line": call.line
                }
                for call in analyzer.extract_call_relationships(chunk)
            ]
    except Exception as e:
        result["errors"]["calls"] = str(e)
        if verbose and not output_json:
            console.print(f"[red]Error extracting calls: {e}[/red]")
            if verbose:
                console.print(f"[dim]{traceback.format_exc()}[/dim]")

    try:
        if not calls_only:
            if verbose and not output_json:
                console.print(f"\n[dim]Extracting imports...[/dim]")
            result["imports"] = [
                {
                    "source": imp.imported_from,
                    "items": imp.imported_items,
                    "type": imp.import_type,
                    "line": imp.line
                }
                for imp in analyzer.extract_import_relationships(chunk)
            ]
    except Exception as e:
        result["errors"]["imports"] = str(e)
        if verbose and not output_json:
            console.print(f"[red]Error extracting imports: {e}[/red]")
            if verbose:
                console.print(f"[dim]{traceback.format_exc()}[/dim]")

    try:
        if not calls_only and not imports_only:
            if verbose and not output_json:
                console.print(f"\n[dim]Extracting metadata...[/dim]")
            result["metadata"] = analyzer.extract_custom_metadata(chunk)
    except Exception as e:
        result["errors"]["metadata"] = str(e)
        if verbose and not output_json:
            console.print(f"[red]Error extracting metadata: {e}[/red]")
            if verbose:
                console.print(f"[dim]{traceback.format_exc()}[/dim]")

    # Output results
    if output_json:
        console.print(json.dumps(result, indent=2))
    else:
        _pretty_print_analysis(result, calls_only, imports_only, verbose)


@analyze.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False))
@click.option('--ext', help='File extension filter (e.g., .ts)')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def directory(directory: str, ext: str, output_json: bool):
    """Analyze all files in a directory."""
    _ensure_initialized()
    path = Path(directory)
    registry = get_registry()

    # Get supported extensions
    supported_exts = set()
    for exts in registry.list_supported_extensions().keys():
        supported_exts.add(exts)

    # Find files
    if ext:
        pattern = f"*{ext}"
    else:
        pattern = "*"

    files = [f for f in path.rglob(pattern) if f.suffix in supported_exts]

    if not files:
        console.print(f"[yellow]No analyzable files found in {directory}[/yellow]")
        return

    console.print(f"[blue]Found {len(files)} files to analyze[/blue]")

    stats = {
        "total_files": len(files),
        "total_imports": 0,
        "total_calls": 0,
        "by_language": {},
        "files": []
    }

    with console.status("[bold green]Analyzing files...") as status:
        for i, file_path in enumerate(files):
            status.update(f"[bold green]Analyzing {i+1}/{len(files)}: {file_path.name}")

            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                analyzer = get_analyzer(str(file_path))
                if not analyzer:
                    continue

                chunk = CodeChunk(
                    text=content,
                    filename=str(file_path),
                    start_line=1,
                    end_line=len(content.split('\n')),
                    node_type="file",
                    symbols=[],  # Empty list for now
                    metadata={}
                )

                # Count items
                imports = list(analyzer.extract_import_relationships(chunk))
                calls = list(analyzer.extract_call_relationships(chunk))

                lang = analyzer.language_name
                stats["by_language"][lang] = stats["by_language"].get(lang, 0) + 1
                stats["total_imports"] += len(imports)
                stats["total_calls"] += len(calls)

                if output_json:
                    stats["files"].append({
                        "file": str(file_path),
                        "language": lang,
                        "imports": len(imports),
                        "calls": len(calls)
                    })

            except Exception as e:
                if output_json:
                    stats["files"].append({
                        "file": str(file_path),
                        "error": str(e)
                    })

    if output_json:
        console.print(json.dumps(stats, indent=2))
    else:
        _print_directory_stats(stats)


def _pretty_print_analysis(result: Dict[str, Any], calls_only: bool, imports_only: bool, verbose: bool = False):
    """Pretty print analysis results."""
    console.print(f"\n[bold blue]Analysis:[/bold blue] {result['file']}")
    console.print(f"Language: {result['language']} | Analyzer: {result['analyzer']}")
    console.print("=" * 80)

    # Show errors if any
    if result.get('errors'):
        console.print(f"\n[bold red]⚠️  Errors:[/bold red]")
        for error_type, error_msg in result['errors'].items():
            console.print(f"  {error_type}: {error_msg}")

    # Always show sections headers if verbose, even if empty
    if not imports_only:
        if result['imports'] or verbose:
            console.print(f"\n[bold green]📦 Imports ({len(result['imports'])}):[/bold green]")
            if result['imports']:
                for imp in result['imports']:
                    items = ', '.join(imp['items']) if imp['items'] else '*'
                    console.print(f"  {imp['source']} → {items} (line {imp['line']})")
            elif verbose:
                console.print("  [dim]No imports found[/dim]")

    if not calls_only:
        if result['calls'] or verbose:
            console.print(f"\n[bold yellow]📞 Function Calls ({len(result['calls'])}):[/bold yellow]")
            if result['calls']:
                for call in result['calls'][:10]:
                    caller = call['caller'] or '<module>'
                    args = ', '.join(call['arguments']) if call['arguments'] else ''
                    console.print(f"  {caller} → {call['callee']}({args}) at line {call['line']}")
                if len(result['calls']) > 10:
                    console.print(f"  [dim]... and {len(result['calls']) - 10} more[/dim]")
            elif verbose:
                console.print("  [dim]No function calls found[/dim]")

    if not calls_only and not imports_only:
        if result['metadata'] or verbose:
            console.print(f"\n[bold cyan]📊 Metadata:[/bold cyan]")
            if result['metadata']:
                for key, value in result['metadata'].items():
                    if isinstance(value, bool):
                        console.print(f"  {key}: {'✓' if value else '✗'}")
                    elif isinstance(value, list):
                        console.print(f"  {key}: {len(value)} items")
                    else:
                        console.print(f"  {key}: {value}")
            elif verbose:
                console.print("  [dim]No metadata found[/dim]")


def _print_directory_stats(stats: Dict[str, Any]):
    """Print directory analysis statistics."""
    console.print(f"\n[bold green]📊 Analysis Summary[/bold green]")
    console.print(f"  Files analyzed: {stats['total_files']}")
    console.print(f"  Total imports: {stats['total_imports']}")
    console.print(f"  Total function calls: {stats['total_calls']}")

    if stats['by_language']:
        console.print(f"\n[bold]By language:[/bold]")
        for lang, count in stats['by_language'].items():
            console.print(f"    {lang}: {count} files")
