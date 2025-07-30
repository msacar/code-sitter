#!/usr/bin/env python3
"""Debug script to check analyzer_aware flow status and data."""

import os
import sys
import subprocess
import psycopg2
from pathlib import Path

def run_cmd(cmd):
    """Run command and return output."""
    print(f"\n> {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    return result.returncode, result.stdout, result.stderr

def check_database():
    """Check database contents."""
    db_url = os.getenv("COCOINDEX_DATABASE_URL", "postgresql://cocoindex:cocoindex@localhost:5432/cocoindex")

    print(f"\nConnecting to: {db_url}")

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        # Check tracking table
        print("\n=== Checking CocoIndex Tracking ===")
        cur.execute("""
            SELECT flow_name, table_name, last_updated
            FROM cocoindex_tracking
            WHERE flow_name LIKE '%AnalyzerAware%'
        """)
        for row in cur.fetchall():
            print(f"Flow: {row[0]}, Table: {row[1]}, Updated: {row[2]}")

        # Check if table exists and has data
        print("\n=== Checking Data Table ===")
        cur.execute("""
            SELECT COUNT(*)
            FROM analyzerawarecodeindex__code_chunks_with_metadata
        """)
        count = cur.fetchone()[0]
        print(f"Total chunks indexed: {count}")

        if count > 0:
            # Sample data
            cur.execute("""
                SELECT filename, language, is_react_component, has_interfaces
                FROM analyzerawarecodeindex__code_chunks_with_metadata
                LIMIT 5
            """)
            print("\nSample data:")
            for row in cur.fetchall():
                print(f"  {row[0]} | {row[1]} | React: {row[2]} | Interfaces: {row[3]}")

        # Check for TypeScript files
        cur.execute("""
            SELECT COUNT(DISTINCT filename), COUNT(*)
            FROM analyzerawarecodeindex__code_chunks_with_metadata
            WHERE language = 'typescript'
        """)
        ts_files, ts_chunks = cur.fetchone()
        print(f"\nTypeScript: {ts_files} files, {ts_chunks} chunks")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Database error: {e}")

def main():
    """Main debug function."""
    print("=== Analyzer Aware Flow Debug ===\n")

    # 1. Check environment
    print("1. Environment:")
    print(f"   COCOINDEX_DATABASE_URL: {os.getenv('COCOINDEX_DATABASE_URL', 'Not set')}")
    print(f"   USE_POSTGRES: {os.getenv('USE_POSTGRES', 'Not set')}")

    # 2. Check flow file
    flow_path = "/Users/mustafaacar/codesitter/src/codesitter/flows/analyzer_aware.py"
    print(f"\n2. Flow file: {flow_path}")
    print(f"   Exists: {Path(flow_path).exists()}")

    # 3. Run setup check
    print("\n3. Running setup check...")
    run_cmd(f"cocoindex setup --check {flow_path}")

    # 4. Check database
    check_database()

    # 5. Test direct update
    print("\n5. Testing direct update (from correct directory)...")
    project_path = "/Users/mustafaacar/retter/shortlink"
    print(f"   Project path: {project_path}")
    print(f"   Exists: {Path(project_path).exists()}")

    if Path(project_path).exists():
        # Change to project directory and run update
        original_dir = os.getcwd()
        os.chdir(project_path)

        print("\n   Running update from project directory...")
        returncode, stdout, stderr = run_cmd(f"cocoindex update {flow_path}")

        os.chdir(original_dir)

        # Check for statistics in output
        if "added" in stdout or "updated" in stdout:
            print("\n   ✓ Update found changes")
        else:
            print("\n   ⚠ No changes detected")

    print("\n=== Debug Complete ===")

    print("\nRecommendations:")
    print("1. If setup shows out of date, try:")
    print(f"   cocoindex setup --force {flow_path}")
    print("\n2. To see verbose output during indexing:")
    print("   codesitter index -p /Users/mustafaacar/retter/shortlink --flow analyzer_aware --postgres --verbose")
    print("\n3. To run update directly:")
    print("   cd /Users/mustafaacar/retter/shortlink")
    print(f"   cocoindex update {flow_path}")

if __name__ == "__main__":
    main()
