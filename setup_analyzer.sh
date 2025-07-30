#!/bin/bash
# Quick setup script for analyzer_simple flow

echo "=== CodeSitter Analyzer Setup ==="
echo
echo "This script shows how to use the working analyzer_simple flow."
echo

# Set environment variables
export USE_POSTGRES=true
export COCOINDEX_DATABASE_URL="${COCOINDEX_DATABASE_URL:-postgresql://cocoindex:cocoindex@localhost:5432/cocoindex}"
export DATABASE_URL="$COCOINDEX_DATABASE_URL"

echo "Environment:"
echo "  USE_POSTGRES=$USE_POSTGRES"
echo "  DATABASE_URL=$DATABASE_URL"
echo

# Get paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FLOW_PATH="$SCRIPT_DIR/src/codesitter/flows/analyzer_simple.py"

echo "Flow path: $FLOW_PATH"
echo

# Show commands
echo "Commands to run:"
echo
echo "1. Setup database tables (run once):"
echo "   cocoindex setup $FLOW_PATH"
echo
echo "2. Index a TypeScript project:"
echo "   cd /path/to/your/typescript/project"
echo "   codesitter index -p . --flow analyzer_simple --postgres --verbose"
echo
echo "3. Query the results:"
echo "   psql $DATABASE_URL"
echo "   SELECT filename, code FROM code_analysis WHERE is_react_component = true LIMIT 5;"
echo "   SELECT filename, code FROM code_analysis WHERE has_interfaces = true LIMIT 5;"
echo
echo "Note: The analyzer_simple flow is the only working analyzer flow that properly"
echo "      extracts TypeScript metadata. Use it instead of analyzer_aware or analyzer_advanced."
