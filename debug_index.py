#!/usr/bin/env python3
"""Debug script for codesitter index command."""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the CLI module
from codesitter.cli import cli

if __name__ == '__main__':
    # Simulate the command line arguments
    sys.argv = [
        'codesitter',
        'index',
        '-p', '/Users/mustafaacar/retter/shortlink',
        '--flow', 'flexible'
    ]

    # Run the CLI
    cli()
