"""Index command for codesitter CLI."""

import click
import os
import sys
import subprocess
import json
import time
import re
import threading
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.text import Text

from ..config import BASIC_FLOW_PATH, ENHANCED_FLOW_PATH, FLEXIBLE_FLOW_PATH, SIMPLE_FLOW_PATH, MINIMAL_FLEXIBLE_FLOW_PATH, MINIMAL_FLOW_PATH

console = Console()


def discover_files(target_path: Path, verbose: bool = False):
    """Discover files that will be processed by the flow."""
    console.print("[blue]Scanning for files to index...[/blue]")
    
    # Common file extensions that will be processed
    supported_extensions = {
        '.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs',  # JavaScript/TypeScript
        '.py', '.pyw',  # Python
        '.html', '.htm',  # HTML
        '.css', '.scss', '.sass',  # CSS
        '.json', '.yaml', '.yml', '.toml',  # Config files
        '.xml', '.sh', '.bash',  # Other
        '.c', '.cpp', '.cc', '.cxx',  # C/C++
        '.rs', '.go', '.rb', '.php', '.swift', '.kt', '.java'  # Other languages
    }
    
    files_to_process = []
    total_size = 0
    
    for ext in supported_extensions:
        for file_path in target_path.rglob(f"*{ext}"):
            # Skip common directories to ignore
            if any(ignore in str(file_path) for ignore in [
                'node_modules', '.git', 'dist', 'build', '.venv', 'venv',
                '__pycache__', '.pytest_cache', '.coverage'
            ]):
                continue
            
            try:
                file_size = file_path.stat().st_size
                files_to_process.append({
                    'path': file_path,
                    'size': file_size,
                    'ext': ext
                })
                total_size += file_size
            except (OSError, PermissionError):
                continue
    
    # Sort by size (largest first) for better progress indication
    files_to_process.sort(key=lambda x: x['size'], reverse=True)
    
    if verbose:
        console.print(f"[green]Found {len(files_to_process)} files to process[/green]")
        
        # Show file breakdown by extension
        ext_counts = {}
        for file_info in files_to_process:
            ext = file_info['ext']
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
        
        ext_table = Table(title="Files by Extension")
        ext_table.add_column("Extension", style="cyan")
        ext_table.add_column("Count", style="magenta")
        ext_table.add_column("Total Size", style="green")
        
        for ext, count in sorted(ext_counts.items()):
            ext_size = sum(f['size'] for f in files_to_process if f['ext'] == ext)
            ext_table.add_row(ext, str(count), f"{ext_size / 1024:.1f} KB")
        
        console.print(ext_table)
        
        # Show largest files
        if files_to_process:
            console.print(f"[blue]Largest files to process:[/blue]")
            for i, file_info in enumerate(files_to_process[:5]):
                rel_path = file_info['path'].relative_to(target_path)
                size_kb = file_info['size'] / 1024
                console.print(f"  {i+1}. {rel_path} ({size_kb:.1f} KB)")
    
    return files_to_process, total_size


@click.command()
@click.option('--path', '-p', default='.', help='Path to codebase to index')
@click.option('--watch', '-w', is_flag=True, help='Watch for file changes')
@click.option('--postgres', is_flag=True, help='Use PostgreSQL for storage')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output with detailed logging')
@click.option('--timeout', '-t', default=300, help='Timeout in seconds for indexing process')
@click.option('--json-only', is_flag=True, help='Use direct JSON indexing (bypasses cocoindex)')
@click.option('--max-files', default=100, help='Maximum number of files to process (for JSON indexing)')
@click.option('--flow', '-f',
              type=click.Choice(['basic', 'simple', 'enhanced', 'flexible', 'minimal_flexible', 'minimal']),
              default='simple',
              help='Which flow to use for indexing')
def index(path: str, watch: bool, postgres: bool, verbose: bool, timeout: int, json_only: bool, max_files: int, flow: str):
    """Index a codebase with pluggable language analyzers."""
    path = Path(path).resolve()

    if not path.exists():
        console.print(f"[red]Error: Path {path} does not exist[/red]")
        sys.exit(1)

    # If json-only is specified, use direct JSON indexing
    if json_only:
        console.print(Panel(
            f"[bold blue]Basic JSON Indexing[/bold blue]\n"
            f"[bold]Path:[/bold] {path}\n"
            f"[bold]Output:[/bold] code_index.json\n"
            f"[bold]Mode:[/bold] File list only (no content processing)",
            title="codesitter Basic JSON Indexer"
        ))
        
        # Import and run the safe JSON indexing
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "flows"))
        
        try:
            from json_basic import index_to_json_basic
            
            # Change to target directory
            original_dir = os.getcwd()
            os.chdir(path)
            
            try:
                # Run the indexing
                output_data = index_to_json_basic(".", "code_index.json")
                
                # Show statistics
                show_indexing_stats(console)
                
                console.print(f"[green]✓ Basic JSON indexing completed successfully![/green]")
                console.print(f"[blue]Output file: code_index.json[/blue]")
                
            finally:
                os.chdir(original_dir)
                
        except ImportError as e:
            console.print(f"[red]Error importing JSON direct indexing: {e}[/red]")
            sys.exit(1)
        
        return

    # Select the appropriate flow
    flow_map = {
        'basic': BASIC_FLOW_PATH,
        'simple': SIMPLE_FLOW_PATH,
        'enhanced': ENHANCED_FLOW_PATH,
        'flexible': FLEXIBLE_FLOW_PATH,
        'minimal_flexible': MINIMAL_FLEXIBLE_FLOW_PATH,
        'minimal': MINIMAL_FLOW_PATH
    }
    flow_path = flow_map[flow]

    console.print(Panel(
        f"[bold blue]Indexing codebase at:[/bold blue] {path}\n"
        f"[bold]Storage:[/bold] {'PostgreSQL' if postgres else 'JSON file'}\n"
        f"[bold]Watch mode:[/bold] {'Enabled' if watch else 'Disabled'}\n"
        f"[bold]Verbose:[/bold] {'Enabled' if verbose else 'Disabled'}\n"
        f"[bold]Timeout:[/bold] {timeout}s\n"
        f"[bold]Flow:[/bold] {flow} ({flow_path.name})",
        title="codesitter Indexer"
    ))

    # Discover files first
    files_to_process, total_size = discover_files(path, verbose)

    # Set environment variables
    if postgres:
        os.environ['USE_POSTGRES'] = 'true'
        # Set COCOINDEX_DATABASE_URL if not already set
        if not os.getenv('COCOINDEX_DATABASE_URL'):
            database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:secret@localhost:5432/cocoindex')
            os.environ['COCOINDEX_DATABASE_URL'] = database_url
        # Check if DATABASE_URL is set
        if not os.getenv('DATABASE_URL'):
            console.print("[yellow]Warning: DATABASE_URL not set. Using default localhost[/yellow]")

    # Change to target directory
    original_dir = os.getcwd()
    os.chdir(path)

    try:
        if watch:
            # Watch mode - run server
            console.print("[green]Starting file watcher...[/green]")
            cmd = ["cocoindex", "server", str(flow_path)]
            console.print(f"[blue]Running: {' '.join(cmd)}[/blue]")
            subprocess.run(cmd)
        else:
            # Index mode with detailed progress
            console.print("[blue]Starting indexing process...[/blue]")
            cmd = ["cocoindex", "update", "--setup", str(flow_path)]
            
            console.print(f"[blue]Executing: {' '.join(cmd)}[/blue]")
            console.print(f"[yellow]Will process {len(files_to_process)} files ({total_size / 1024 / 1024:.1f} MB total)[/yellow]")
            console.print(f"[yellow]Timeout set to {timeout} seconds[/yellow]")
            
            # Run with real-time output for verbose mode
            if verbose:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # Real-time output with progress tracking
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=console
                ) as progress:
                    task = progress.add_task("Indexing files...", total=len(files_to_process) if files_to_process else None)
                    
                    # Track file processing
                    files_processed = 0
                    start_time = time.time()
                    last_update_time = start_time
                    last_output_time = start_time
                    
                    # Timeout tracking
                    timeout_reached = False
                    
                    for line in process.stdout:
                        line = line.strip()
                        current_time = time.time()
                        
                        # Check for timeout
                        if current_time - start_time > timeout:
                            console.print(f"[red]⚠ TIMEOUT: Process exceeded {timeout}s timeout[/red]")
                            timeout_reached = True
                            process.terminate()
                            break
                        
                        if line:
                            # Show all output in verbose mode
                            console.print(f"[dim]{line}[/dim]")
                            last_output_time = current_time
                            
                            # Update progress based on various patterns
                            if any(keyword in line.lower() for keyword in ["processing", "found", "indexing", "chunk", "file"]):
                                files_processed += 1
                                elapsed = current_time - start_time
                                
                                # Try to extract filename from the line
                                filename = "unknown"
                                if "file" in line.lower():
                                    # Look for file paths in the line
                                    path_match = re.search(r'[\/\\]([^\/\\]+\.(ts|js|tsx|jsx|py|html|css|json|yaml|yml|toml|xml|sh|bash|c|cpp|cc|cxx|rs|go|rb|php|swift|kt|java))', line)
                                    if path_match:
                                        filename = path_match.group(1)
                                
                                progress.update(
                                    task, 
                                    description=f"Processing {filename}... ({files_processed}/{len(files_to_process) if files_to_process else '?'} files, {elapsed:.1f}s)"
                                )
                            elif "error" in line.lower():
                                console.print(f"[red]✗ ERROR: {line}[/red]")
                            elif "warning" in line.lower():
                                console.print(f"[yellow]⚠ WARNING: {line}[/yellow]")
                            elif "setup" in line.lower() or "database" in line.lower():
                                console.print(f"[blue]→ SETUP: {line}[/blue]")
                            elif "create" in line.lower() or "table" in line.lower():
                                console.print(f"[cyan]→ DB: {line}[/cyan]")
                            
                            # Update progress every 2 seconds even if no new files
                            if current_time - last_update_time > 2:
                                elapsed = current_time - start_time
                                progress.update(
                                    task, 
                                    description=f"Processing files... ({files_processed}/{len(files_to_process) if files_to_process else '?'} files, {elapsed:.1f}s)"
                                )
                                last_update_time = current_time
                        
                        # Show warning if no output for a while
                        if current_time - last_output_time > 30:
                            console.print(f"[yellow]⚠ No output for {current_time - last_output_time:.0f}s - process may be stuck[/yellow]")
                            last_output_time = current_time
                    
                    if not timeout_reached:
                        process.wait()
                    
                    if process.returncode == 0 and not timeout_reached:
                        elapsed = time.time() - start_time
                        progress.update(task, completed=True)
                        console.print(f"[green]✓ Indexing completed successfully in {elapsed:.1f}s![/green]")
                        console.print(f"[blue]Processed {files_processed} files[/blue]")
                        
                        # Show statistics
                        show_indexing_stats(console)
                    elif timeout_reached:
                        console.print(f"[red]✗ Indexing timed out after {timeout}s[/red]")
                        console.print(f"[yellow]Processed {files_processed} files before timeout[/yellow]")
                        sys.exit(1)
                    else:
                        console.print(f"[red]✗ Indexing failed with return code {process.returncode}[/red]")
                        sys.exit(1)
            else:
                # Non-verbose mode with simple progress
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task("Indexing files...", total=len(files_to_process) if files_to_process else None)
                    start_time = time.time()
                    
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
                        
                        if result.returncode == 0:
                            elapsed = time.time() - start_time
                            progress.update(task, completed=True)
                            console.print(f"[green]✓ Indexing completed successfully in {elapsed:.1f}s![/green]")
                            
                            # Show statistics
                            show_indexing_stats(console)
                        else:
                            console.print(f"[red]Error during indexing:[/red]\n{result.stderr}")
                            if verbose:
                                console.print(f"[red]Stdout:[/red]\n{result.stdout}")
                            sys.exit(1)
                    except subprocess.TimeoutExpired:
                        console.print(f"[red]✗ Indexing timed out after {timeout}s[/red]")
                        sys.exit(1)
    finally:
        os.chdir(original_dir)


def show_indexing_stats(console):
    """Display indexing statistics."""
    stats_table = Table(title="Indexing Statistics")
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="magenta")
    
    # Check for generated files
    if Path("code_index.json").exists():
        with open("code_index.json", 'r') as f:
            data = json.load(f)
            stats_table.add_row("Code Chunks", str(len(data)))
    
    if Path("symbol_index.json").exists():
        with open("symbol_index.json", 'r') as f:
            symbols = json.load(f)
            stats_table.add_row("Unique Symbols", str(len(symbols)))
    
    if Path("call_relationships.json").exists():
        with open("call_relationships.json", 'r') as f:
            calls = json.load(f)
            stats_table.add_row("Call Relationships", str(len(calls)))
    
    if Path("import_relationships.json").exists():
        with open("import_relationships.json", 'r') as f:
            imports = json.load(f)
            stats_table.add_row("Import Relationships", str(len(imports)))
    
    console.print(stats_table)


@click.command()
@click.option('--path', '-p', default='.', help='Path to codebase to watch')
@click.option('--postgres', is_flag=True, help='Use PostgreSQL for storage')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output with detailed logging')
@click.option('--timeout', '-t', default=300, help='Timeout in seconds for indexing process')
def watch(path: str, postgres: bool, verbose: bool, timeout: int):
    """Watch a codebase for changes and auto-index."""
    # This is essentially index with watch=True
    ctx = click.get_current_context()
    ctx.invoke(index, path=path, watch=True, postgres=postgres, verbose=verbose, timeout=timeout)
