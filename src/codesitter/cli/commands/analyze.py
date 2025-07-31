"""Analyze command for codesitter CLI."""

import click
import json
from pathlib import Path
from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax

from ...analyzers import get_analyzer, get_registry, auto_discover_analyzers, register_defaults
from ...analyzers.base import CodeChunk

console = Console()


@click.group()
def analyze():
    """Run analyzers standalone without indexing."""
    # Initialize analyzer registry
    register_defaults()
    auto_discover_analyzers()


@analyze.command()
def list():
    """List all available analyzers and their capabilities."""
    registry = get_registry()

    table = Table(title="Available Analyzers")
    table.add_column("Analyzer", style="cyan", no_wrap=True)
    table.add_column("Extensions", style="green")
    table.add_column("Capabilities", style="yellow")

    supported = registry.list_supported_extensions()

    for analyzer_class, extensions in supported.items():
        # Get an instance to check capabilities
        analyzer = get_analyzer(extensions[0])
        capabilities = []

        if hasattr(analyzer, 'extract_call_relationships'):
            capabilities.append("calls")
        if hasattr(analyzer, 'extract_import_relationships'):
            capabilities.append("imports")
        if hasattr(analyzer, 'extract_custom_metadata'):
            capabilities.append("metadata")

        table.add_row(
            analyzer_class,
            ", ".join(extensions),
            ", ".join(capabilities) or "basic only"
        )

    console.print(table)


@analyze.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option('--calls-only', is_flag=True, help='Show only function calls')
@click.option('--imports-only', is_flag=True, help='Show only imports')
def file(file_path: str, output_json: bool, calls_only: bool, imports_only: bool):
    """Analyze a single file."""
    path = Path(file_path)

    with open(path, 'r') as f:
        content = f.read()

    ext = path.suffix
    analyzer = get_analyzer(ext)

    if not analyzer:
        console.print(f"[red]No analyzer found for {ext} files[/red]")
        return

    # Create chunk for whole file
    chunk = CodeChunk(
        content=content,
        start_line=1,
        end_line=len(content.split('\n')),
        file_path=str(path),
        chunk_index=0,
        total_chunks=1,
        language=analyzer.language_name,
        node_type="file"
    )

    # Extract data
    result = {
        "file": str(path),
        "language": analyzer.language_name,
        "analyzer": analyzer.__class__.__name__,
        "calls": [],
        "imports": [],
        "metadata": {}
    }

    try:
        if not imports_only:
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
        if output_json:
            result["errors"] = {"calls": str(e)}

    try:
        if not calls_only:
            result["imports"] = [
                {
                    "source": imp.source,
                    "items": imp.imported_items,
                    "type": imp.import_type,
                    "line": imp.line
                }
                for imp in analyzer.extract_import_relationships(chunk)
            ]
    except Exception as e:
        if output_json:
            result["errors"] = result.get("errors", {})
            result["errors"]["imports"] = str(e)

    try:
        if not calls_only and not imports_only:
            result["metadata"] = analyzer.extract_custom_metadata(chunk)
    except Exception as e:
        if output_json:
            result["errors"] = result.get("errors", {})
            result["errors"]["metadata"] = str(e)

    # Output results
    if output_json:
        console.print(json.dumps(result, indent=2))
    else:
        _pretty_print_analysis(result, calls_only, imports_only)


@analyze.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False))
@click.option('--ext', help='File extension filter (e.g., .ts)')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def directory(directory: str, ext: str, output_json: bool):
    """Analyze all files in a directory."""
    path = Path(directory)
    registry = get_registry()

    # Get supported extensions
    supported_exts = set()
    for exts in registry.list_supported_extensions().values():
        supported_exts.update(exts)

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

                analyzer = get_analyzer(file_path.suffix)
                if not analyzer:
                    continue

                chunk = CodeChunk(
                    content=content,
                    start_line=1,
                    end_line=len(content.split('\n')),
                    file_path=str(file_path),
                    chunk_index=0,
                    total_chunks=1,
                    language=analyzer.language_name,
                    node_type="file"
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


def _pretty_print_analysis(result: Dict[str, Any], calls_only: bool, imports_only: bool):
    """Pretty print analysis results."""
    console.print(f"\n[bold blue]Analysis:[/bold blue] {result['file']}")
    console.print(f"Language: {result['language']} | Analyzer: {result['analyzer']}")
    console.print("=" * 80)

    if not imports_only and result['imports']:
        console.print(f"\n[bold green]📦 Imports ({len(result['imports'])}):[/bold green]")
        for imp in result['imports']:
            items = ', '.join(imp['items']) if imp['items'] else '*'
            console.print(f"  {imp['source']} → {items} (line {imp['line']})")

    if not calls_only and result['calls']:
        console.print(f"\n[bold yellow]📞 Function Calls ({len(result['calls'])}):[/bold yellow]")
        for call in result['calls'][:10]:
            caller = call['caller'] or '<module>'
            args = ', '.join(call['arguments']) if call['arguments'] else ''
            console.print(f"  {caller} → {call['callee']}({args}) at line {call['line']}")
        if len(result['calls']) > 10:
            console.print(f"  [dim]... and {len(result['calls']) - 10} more[/dim]")

    if not calls_only and not imports_only and result['metadata']:
        console.print(f"\n[bold cyan]📊 Metadata:[/bold cyan]")
        for key, value in result['metadata'].items():
            if isinstance(value, bool):
                console.print(f"  {key}: {'✓' if value else '✗'}")
            elif isinstance(value, list):
                console.print(f"  {key}: {len(value)} items")
            else:
                console.print(f"  {key}: {value}")


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
