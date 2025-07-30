#!/usr/bin/env python3
"""
Simple fix: Load environment and run indexing properly.
"""

import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path("/Users/mustafaacar/codesitter/.env")
if env_path.exists():
    print("Loading .env file...")
    load_dotenv(env_path)
    print(f"✓ DATABASE_URL: {os.getenv('DATABASE_URL')[:30]}...")
else:
    print("❌ No .env file found!")
    sys.exit(1)

# Paths
flow_path = "/Users/mustafaacar/codesitter/src/codesitter/flows/analyzer_aware.py"
project_path = "/Users/mustafaacar/retter/shortlink"

# Change to project directory
print(f"\nChanging to: {project_path}")
os.chdir(project_path)

# Run update
print("\nRunning indexing...")
result = subprocess.run(['cocoindex', 'update', flow_path])

if result.returncode == 0:
    print("\n✓ Success!")
    print("\nNow run:")
    print(f"cd {project_path}")
    print(f"cocoindex server {flow_path} -ci --address 0.0.0.0:3000")
else:
    print("\n❌ Failed!")
