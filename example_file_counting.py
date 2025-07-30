#!/usr/bin/env python3
"""
Example demonstrating the enhanced file counting and progress tracking
in the analyzer_aware flow.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the flow
from src.codesitter.flows.analyzer_aware import analyzer_aware_flow

def demonstrate_file_counting():
    """
    Shows the enhanced file counting and progress tracking features.
    """
    print("=== Analyzer Aware Flow - File Counting Demo ===\n")

    print("The analyzer_aware flow now provides:")
    print("1. Pre-scan file counting before processing")
    print("2. File breakdown by extension")
    print("3. Progress tracking during processing")
    print("\nExample output:")
    print("-" * 50)
    print("Searching for files with patterns: ['**/*.ts', '**/*.tsx', '**/*.js', '**/*.jsx', '**/*.py']")
    print("Found 25 files to process")
    print("Files by extension: {'.js': 10, '.py': 8, '.ts': 5, '.tsx': 2}")
    print("[1/25] Processing file: src/index.ts [Language: typescript]")
    print("[2/25] Processing file: src/utils.js [Language: javascript]")
    print("[3/25] Processing file: tests/test_main.py [Language: python]")
    print("...")
    print("-" * 50)

    print("\nTo run this on your project:")
    print("1. Set up environment variables:")
    print("   export USE_POSTGRES=true")
    print("   export COCOINDEX_DATABASE_URL='postgresql://...'")
    print("\n2. Change to your project directory:")
    print("   cd /path/to/your/project")
    print("\n3. Run the flow:")
    print("   cocoindex update /path/to/analyzer_aware.py")
    print("\n4. Or use the codesitter CLI:")
    print("   codesitter index -p . --flow analyzer_aware --postgres")

if __name__ == "__main__":
    demonstrate_file_counting()
