#!/bin/bash
# Fix analyzer_aware flow setup and indexing issues

echo "=== Fixing Analyzer Aware Flow ==="
echo

# Set environment
export USE_POSTGRES=true
export COCOINDEX_DATABASE_URL="${COCOINDEX_DATABASE_URL:-postgresql://cocoindex:cocoindex@localhost:5432/cocoindex}"

echo "Environment:"
echo "  USE_POSTGRES=$USE_POSTGRES"
echo "  COCOINDEX_DATABASE_URL=$COCOINDEX_DATABASE_URL"
echo

FLOW_PATH="/Users/mustafaacar/codesitter/src/codesitter/flows/analyzer_aware.py"
PROJECT_PATH="/Users/mustafaacar/retter/shortlink"

echo "Paths:"
echo "  Flow: $FLOW_PATH"
echo "  Project: $PROJECT_PATH"
echo

# Step 1: Force setup
echo "Step 1: Force setup to ensure synchronization..."
cocoindex setup --force "$FLOW_PATH"
echo

# Step 2: Run update from the project directory
echo "Step 2: Running update from project directory..."
cd "$PROJECT_PATH" || exit 1

# Run with explicit output
cocoindex update "$FLOW_PATH" 2>&1 | tee /tmp/cocoindex_update.log

# Check for statistics
if grep -q "added\|updated\|removed" /tmp/cocoindex_update.log; then
    echo
    echo "✓ Update completed with changes"
else
    echo
    echo "⚠ No changes detected. Running with --force..."
    cocoindex update --force "$FLOW_PATH"
fi

# Step 3: Verify data
echo
echo "Step 3: Verifying indexed data..."
psql "$COCOINDEX_DATABASE_URL" -c "
SELECT
    COUNT(DISTINCT filename) as files,
    COUNT(*) as chunks,
    COUNT(CASE WHEN is_react_component THEN 1 END) as react_components,
    COUNT(CASE WHEN has_interfaces THEN 1 END) as with_interfaces
FROM analyzerawarecodeindex__code_chunks_with_metadata;
"

echo
echo "=== Fix Complete ==="
echo
echo "Next steps:"
echo "1. Restart the server:"
echo "   cd $PROJECT_PATH"
echo "   cocoindex server $FLOW_PATH -ci --address 0.0.0.0:3000"
echo
echo "2. Check the UI again at https://cocoindex.io/cocoinsight"
echo
echo "If the warning persists, try clearing browser cache or use incognito mode."
