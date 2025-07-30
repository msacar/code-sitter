#!/usr/bin/env python3
"""
Example: How to properly index TypeScript code with analyzers

This shows the correct way to use codesitter with your TypeScript project.
"""

import os
import subprocess
import sys
from pathlib import Path

def setup_environment():
    """Set up required environment variables."""
    # PostgreSQL connection (adjust as needed)
    os.environ['USE_POSTGRES'] = 'true'
    os.environ['COCOINDEX_DATABASE_URL'] = 'postgresql://cocoindex:cocoindex@localhost:5432/cocoindex'
    os.environ['DATABASE_URL'] = os.environ['COCOINDEX_DATABASE_URL']

    print("Environment configured:")
    print(f"  USE_POSTGRES: {os.environ['USE_POSTGRES']}")
    print(f"  DATABASE_URL: {os.environ['DATABASE_URL']}")

def run_command(cmd: list[str], cwd: str = None) -> int:
    """Run a command and return exit code."""
    print(f"\n> {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode

def main():
    """Main example workflow."""
    print("=== TypeScript Code Indexing Example ===\n")

    # 1. Setup environment
    setup_environment()

    # 2. Get paths
    codesitter_path = Path(__file__).parent
    analyzer_aware_flow = codesitter_path / "src/codesitter/flows/analyzer_aware.py"
    analyzer_advanced_flow = codesitter_path / "src/codesitter/flows/analyzer_advanced.py"

    # Example project path (adjust as needed)
    project_path = Path.home() / "retter/shortlink"

    if not project_path.exists():
        print(f"\nProject path not found: {project_path}")
        print("Please adjust the project_path variable to point to your TypeScript project.")
        return 1

    print(f"\nProject to index: {project_path}")

    # 3. Setup database tables (only needed once)
    print("\n--- Step 1: Setup Database Tables ---")

    print("\nSetting up analyzer_aware flow tables...")
    if run_command(['cocoindex', 'setup', str(analyzer_aware_flow)]) != 0:
        print("Failed to setup analyzer_aware flow")
        return 1

    print("\nSetting up analyzer_advanced flow tables...")
    if run_command(['cocoindex', 'setup', str(analyzer_advanced_flow)]) != 0:
        print("Failed to setup analyzer_advanced flow")
        return 1

    # 4. Index with analyzer_aware (metadata only)
    print("\n--- Step 2: Index with Metadata Extraction ---")
    print("This extracts React components, TypeScript features, etc.")

    if run_command([
        'codesitter', 'index',
        '-p', str(project_path),
        '--flow', 'analyzer_aware',
        '--postgres',
        '--verbose'
    ]) != 0:
        print("Failed to index with analyzer_aware")
        return 1

    # 5. Example queries
    print("\n--- Step 3: Example Queries ---")
    print("\nYou can now query your indexed code:")
    print("""
    -- Find React components
    SELECT filename, chunk_text
    FROM code_chunks_with_metadata
    WHERE is_react_component = true
    LIMIT 5;

    -- Find TypeScript interfaces
    SELECT filename, chunk_text
    FROM code_chunks_with_metadata
    WHERE has_interfaces = true
    LIMIT 5;

    -- Find async functions
    SELECT filename, chunk_text
    FROM code_chunks_with_metadata
    WHERE has_async_functions = true
    LIMIT 5;

    -- Semantic search (after installing pgvector extension)
    SELECT filename, chunk_text,
           1 - (embedding <=> (SELECT embedding FROM code_chunks_with_metadata LIMIT 1)) as similarity
    FROM code_chunks_with_metadata
    ORDER BY embedding <=> (SELECT embedding FROM code_chunks_with_metadata LIMIT 1)
    LIMIT 10;
    """)

    # 6. Optional: Index with full analysis
    print("\n--- Step 4 (Optional): Full Analysis ---")
    print("To also extract call relationships and imports, run:")
    print(f"\ncodesitter index -p {project_path} --flow analyzer_advanced --postgres")

    print("\n=== Example Complete ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
