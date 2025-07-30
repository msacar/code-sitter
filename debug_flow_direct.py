#!/usr/bin/env python3
"""Direct debug script for flexible flow."""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set environment variables if needed
# os.environ['USE_POSTGRES'] = 'true'
# os.environ['DATABASE_URL'] = 'postgresql://localhost:5432/code_index'

# Change to target directory
target_dir = '/Users/mustafaacar/retter/shortlink'
os.chdir(target_dir)

# Import and run the flow directly
from codesitter.flows import flexible

# The flow module will be executed when imported
# You can set breakpoints in the flexible.py file
print(f"Flow initialized for directory: {target_dir}")
print("Set breakpoints in flexible.py to debug the flow execution")

# To trigger the flow, you would need to run cocoindex commands
# But for debugging purposes, you can inspect the flow setup
