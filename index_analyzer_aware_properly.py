#!/usr/bin/env python3
"""
Quick workaround script to properly index with analyzer_aware flow.
Run this instead of using the CLI until the bug is fixed.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Configuration
    flow_path = "/Users/mustafaacar/codesitter/src/codesitter/flows/analyzer_aware.py"
    project_path = "/Users/mustafaacar/retter/shortlink"

    # Set environment
    os.environ['USE_POSTGRES'] = 'true'
    if not os.environ.get('COCOINDEX_DATABASE_URL'):
        os.environ['COCOINDEX_DATABASE_URL'] = 'postgresql://cocoindex:cocoindex@localhost:5432/cocoindex'

    print("=== Proper Indexing for analyzer_aware ===\n")

    # 1. Ensure setup is current
    print("1. Running setup...")
    result = subprocess.run(['cocoindex', 'setup', '--force', flow_path])
    if result.returncode != 0:
        print("Setup failed!")
        return 1

    # 2. Change to project directory and run update
    print(f"\n2. Changing to project directory: {project_path}")
    original_dir = os.getcwd()
    os.chdir(project_path)

    try:
        print("\n3. Running update...")
        result = subprocess.run(['cocoindex', 'update', flow_path])

        if result.returncode == 0:
            print("\n✓ Indexing completed successfully!")

            # 4. Verify data
            print("\n4. Verifying indexed data...")
            subprocess.run([
                'psql', os.environ['COCOINDEX_DATABASE_URL'], '-c',
                """
                SELECT
                    COUNT(DISTINCT filename) as files,
                    COUNT(*) as chunks,
                    COUNT(CASE WHEN is_react_component THEN 1 END) as react_components,
                    COUNT(CASE WHEN has_interfaces THEN 1 END) as with_interfaces
                FROM analyzerawarecodeindex__code_chunks_with_metadata;
                """
            ])

            print("\n5. To start the server, run:")
            print(f"   cd {project_path}")
            print(f"   cocoindex server {flow_path} -ci --address 0.0.0.0:3000")

        else:
            print("\nIndexing failed!")
            return 1

    finally:
        os.chdir(original_dir)

    return 0

if __name__ == "__main__":
    sys.exit(main())
