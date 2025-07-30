"""
Modified index command for debugging - temporary modification.
Copy this over the original index() function in
/src/codesitter/cli/commands/index.py for debugging
"""

def index(path: str, watch: bool, postgres: bool, flow: str):
    """Index a codebase with pluggable language analyzers."""
    import pdb  # Python debugger

    path = Path(path).resolve()

    if not path.exists():
        console.print(f"[red]Error: Path {path} does not exist[/red]")
        sys.exit(1)

    # Select the appropriate flow
    flow_map = {
        'basic': BASIC_FLOW_PATH,
        'simple': SIMPLE_FLOW_PATH,
        'enhanced': ENHANCED_FLOW_PATH,
        'flexible': FLEXIBLE_FLOW_PATH
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
        # Set a breakpoint here to debug before subprocess call
        pdb.set_trace()  # This will pause execution for debugging

        # Alternative: Import and run the flow directly for debugging
        if os.getenv('DEBUG_FLOW_DIRECT', 'false').lower() == 'true':
            # Direct flow execution for debugging
            import importlib.util
            spec = importlib.util.spec_from_file_location("flow_module", flow_path)
            flow_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(flow_module)

            # Now you can debug the flow directly
            console.print("[yellow]Direct flow debugging mode - flow loaded[/yellow]")
        else:
            # Original subprocess execution
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

                    # Debug: print the exact command being run
                    console.print(f"[yellow]Debug: Running command: {' '.join(cmd)}[/yellow]")
                    console.print(f"[yellow]Debug: Current directory: {os.getcwd()}[/yellow]")
                    console.print(f"[yellow]Debug: Flow path: {flow_path}[/yellow]")

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
                        console.print(f"[red]Stdout:[/red]\n{result.stdout}")
                        sys.exit(1)
    finally:
        os.chdir(original_dir)
