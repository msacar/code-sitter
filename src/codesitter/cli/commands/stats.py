"""Stats command for codesitter CLI."""

import click
import json
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table

from ..config import (
    DEFAULT_CODE_INDEX_PATH,
    DEFAULT_SYMBOL_INDEX_PATH,
    MAX_TOP_SYMBOLS,
    MAX_NODE_TYPES_DISPLAY,
    DATABASE_URL,
    USE_POSTGRES
)

console = Console()


def get_postgres_stats():
    """Get statistics from PostgreSQL database."""
    import psycopg2

    try:
        # Use the same database URL as the indexing
        db_url = os.getenv("DATABASE_URL", DATABASE_URL)
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        stats = {}

        # Get total chunks
        cur.execute("SELECT COUNT(*) FROM FlexibleCodeIndex__code_chunks")
        stats['total_chunks'] = cur.fetchone()[0]

        # Get unique files
        cur.execute("SELECT COUNT(DISTINCT filename) FROM FlexibleCodeIndex__code_chunks")
        stats['total_files'] = cur.fetchone()[0]

        # Get language distribution
        cur.execute("""
            SELECT language, COUNT(*) as count
            FROM FlexibleCodeIndex__code_chunks
            GROUP BY language
            ORDER BY count DESC
        """)
        stats['languages'] = cur.fetchall()

        # Get total text size (approximate)
        cur.execute("SELECT SUM(LENGTH(chunk_text)) FROM FlexibleCodeIndex__code_chunks")
        total_chars = cur.fetchone()[0] or 0
        stats['total_chars'] = total_chars
        stats['estimated_lines'] = total_chars // 80  # Rough estimate

        # Get file extensions
        cur.execute("""
            SELECT
                SUBSTRING(filename FROM '\\.[^.]+$') as ext,
                COUNT(DISTINCT filename) as count
            FROM FlexibleCodeIndex__code_chunks
            WHERE filename LIKE '%.%'
            GROUP BY ext
            ORDER BY count DESC
            LIMIT 10
        """)
        stats['extensions'] = cur.fetchall()

        cur.close()
        conn.close()

        return stats

    except Exception as e:
        console.print(f"[red]Error connecting to PostgreSQL: {e}[/red]")
        console.print("[yellow]Make sure PostgreSQL is running and DATABASE_URL is set correctly.[/yellow]")
        return None


@click.command()
@click.option('--postgres', is_flag=True, help='Read stats from PostgreSQL')
def stats(postgres):
    """Show statistics about the indexed codebase."""

    # Check if we should use PostgreSQL
    use_pg = postgres or os.getenv("USE_POSTGRES", "false").lower() == "true"

    if use_pg:
        # Get stats from PostgreSQL
        pg_stats = get_postgres_stats()
        if not pg_stats:
            return

        # Display main statistics
        stats_table = Table(title="Codebase Statistics (PostgreSQL)")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")

        stats_table.add_row("Total files", str(pg_stats['total_files']))
        stats_table.add_row("Total chunks", str(pg_stats['total_chunks']))
        stats_table.add_row("Total characters", f"{pg_stats['total_chars']:,}")
        stats_table.add_row("Estimated lines", f"{pg_stats['estimated_lines']:,}")

        console.print(stats_table)

        # Display language distribution
        if pg_stats['languages']:
            lang_table = Table(title="Language Distribution")
            lang_table.add_column("Language", style="cyan")
            lang_table.add_column("Chunks", style="green")

            for lang, count in pg_stats['languages']:
                lang_table.add_row(lang or "unknown", str(count))

            console.print("\n")
            console.print(lang_table)

        # Display file extensions
        if pg_stats['extensions']:
            ext_table = Table(title="File Extensions")
            ext_table.add_column("Extension", style="cyan")
            ext_table.add_column("Files", style="green")

            for ext, count in pg_stats['extensions']:
                ext_table.add_row(ext or "no extension", str(count))

            console.print("\n")
            console.print(ext_table)

    else:
        # Original JSON-based stats
        symbol_index_path = Path(DEFAULT_SYMBOL_INDEX_PATH)
        code_index_path = Path(DEFAULT_CODE_INDEX_PATH)

        if not symbol_index_path.exists() and not code_index_path.exists():
            console.print("[yellow]No index files found. Run 'codesitter index' first.[/yellow]")
            console.print("[info]Tip: If you used PostgreSQL, add --postgres flag or set USE_POSTGRES=true[/info]")
            return

        stats_table = Table(title="Codebase Statistics (JSON)")
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
