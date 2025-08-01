#!/usr/bin/env python
"""Debug script for testing analyze command directly."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from codesitter.cli import cli

if __name__ == '__main__':
    # Simulate the command line arguments
    sys.argv = ['codesitter', 'analyze', 'file', 'test_calls.ts', '--json']

    # You can set a breakpoint here or inside the analyze function
    cli()
