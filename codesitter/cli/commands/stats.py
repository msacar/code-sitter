"""Stats command for Code-Sitter CLI."""

import click
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

from ..config import (
    DEFAULT_CODE_INDEX_PATH,
    DEFAULT_SYMBOL_INDEX_PATH,
    MAX_TOP_SYMBOLS,
    MAX_NODE_TYPES_DISPLAY
)

console = Console()


@click.command()
def stats():
    """Show statistics about the indexed codebase."""
    symbol_index_path = Path(DEFAULT_SYMBOL_INDEX_PATH)
    code_index_path = Path(DEFAULT_CODE_INDEX_PATH)

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
                                       for name, count in symbol_counts[:MAX_TOP_SYMBOLS]])
                stats_table.add_row("Top symbols", top_symbols)

    console.print(stats_table)

    # Show node type distribution if available
    if 'node_types' in locals() and node_types:
        type_table = Table(title="Code Structure Distribution")
        type_table.add_column("Node Type", style="cyan")
        type_table.add_column("Count", style="green")

        for node_type, count in sorted(node_types.items(),
                                      key=lambda x: x[1],
                                      reverse=True)[:MAX_NODE_TYPES_DISPLAY]:
            type_table.add_row(node_type, str(count))

        console.print("\n")
        console.print(type_table)
