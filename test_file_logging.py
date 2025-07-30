#!/usr/bin/env python3
"""Test script to verify file logging in analyzer_aware flow."""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✓ Loaded environment from {env_path}")
else:
    print(f"⚠️  No .env file found at {env_path}")

# Import the flow
from src.codesitter.flows.analyzer_aware import analyzer_aware_flow

def test_file_logging():
    """Test the file logging functionality of analyzer_aware flow."""
    print("\n=== Testing File Logging in AnalyzerAwareCodeIndex ===\n")

    # Check if PostgreSQL is configured
    use_postgres = os.getenv("USE_POSTGRES", "false").lower() == "true"
    if use_postgres:
        db_url = os.getenv("COCOINDEX_DATABASE_URL")
        if db_url:
            print(f"✓ PostgreSQL configured: {db_url.split('@')[-1]}")
        else:
            print("⚠️  USE_POSTGRES=true but COCOINDEX_DATABASE_URL not set")
    else:
        print("ℹ️  Running without PostgreSQL (file logging will still work)")

    # Create a test directory with sample files
    test_dir = Path("test_project")
    test_dir.mkdir(exist_ok=True)

    # Create some test files
    test_files = [
        ("index.ts", "export const hello = 'world';"),
        ("utils.js", "function add(a, b) { return a + b; }"),
        ("component.tsx", "export const App = () => <div>Hello</div>;"),
        ("test.py", "def test_example(): assert True"),
        ("README.md", "# Test Project"),
    ]

    for filename, content in test_files:
        (test_dir / filename).write_text(content)

    print(f"✓ Created test directory with {len(test_files)} sample files")

    # Change to test directory and run the flow
    original_dir = os.getcwd()
    try:
        os.chdir(test_dir)
        print(f"✓ Changed to test directory: {test_dir.absolute()}")

        # Run the flow setup if using PostgreSQL
        if use_postgres and db_url:
            flow_path = Path(__file__).parent / "src" / "codesitter" / "flows" / "analyzer_aware.py"
            print(f"\nSetting up database tables...")
            result = subprocess.run(
                ["cocoindex", "setup", str(flow_path)],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✓ Database setup complete")
            else:
                print(f"⚠️  Database setup warning: {result.stderr}")

        print("\nRunning analyzer_aware_flow...")
        print("-" * 50)
        print("Watch for 'Processing file:' log messages below:")
        print("-" * 50)

        # Run the flow
        analyzer_aware_flow.run()

        print("-" * 50)
        print("\n✓ Flow execution complete!")

        if use_postgres and db_url:
            print("\nTo view file counts, run these SQL queries:")
            print("  SELECT COUNT(DISTINCT filename) FROM code_chunks_with_metadata;")
            print("  SELECT language, COUNT(DISTINCT filename) FROM code_chunks_with_metadata GROUP BY language;")

    finally:
        os.chdir(original_dir)
        # Cleanup test directory
        import shutil
        shutil.rmtree(test_dir)
        print(f"\n✓ Cleaned up test directory")

if __name__ == "__main__":
    test_file_logging()
