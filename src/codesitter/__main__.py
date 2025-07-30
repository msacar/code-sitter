"""Main entry point for codesitter CLI."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the current directory or project root
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try current working directory
    load_dotenv()

from .cli import cli

if __name__ == "__main__":
    cli()
