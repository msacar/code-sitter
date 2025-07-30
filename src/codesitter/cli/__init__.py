"""codesitter CLI Interface."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the current directory or project root
env_path = Path(__file__).parent.parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try current working directory
    load_dotenv()

import click
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@click.group()
@click.version_option(prog_name='codesitter')
@click.pass_context
def cli(ctx):
    """
    codesitter: Real-time code intelligence for your codebase.

    Index and search through codebases with language-aware analysis.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)


# Import and register commands
from .commands import index, search, stats, analyze

cli.add_command(index.index)
cli.add_command(index.watch)
cli.add_command(search.search)
cli.add_command(stats.stats)
cli.add_command(analyze.analyze)
