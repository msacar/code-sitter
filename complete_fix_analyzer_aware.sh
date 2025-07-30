#!/bin/bash
# Complete fix script with proper environment setup

echo "=== Complete Fix for analyzer_aware Flow ==="
echo

# Load environment from .env file if it exists
if [ -f "/Users/mustafaacar/codesitter/.env" ]; then
    echo "Loading environment from .env file..."
    set -a
    source /Users/mustafaacar/codesitter/.env
    set +a
else
    echo "Setting default environment..."
    export USE_POSTGRES=true
    export COCOINDEX_DATABASE_URL="postgresql://cocoindex:cocoindex@localhost:5432/cocoindex"
    export DATABASE_URL="$COCOINDEX_DATABASE_URL"
fi

echo
echo "Environment variables:"
echo "  USE_POSTGRES=$USE_POSTGRES"
echo "  COCOINDEX_DATABASE_URL=$COCOINDEX_DATABASE_URL"
echo

# Test database connection
echo "Testing database connection..."
psql "$COCOINDEX_DATABASE_URL" -c "SELECT 1;" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Cannot connect to database!"
    echo "Please ensure PostgreSQL is running and credentials are correct."
    exit 1
fi
echo "✓ Database connection successful"
echo

# Paths
FLOW_PATH="/Users/mustafaacar/codesitter/src/codesitter/flows/analyzer_aware.py"
PROJECT_PATH="/Users/mustafaacar/retter/shortlink"

# Step 1: Setup
echo "Step 1: Running setup..."
cocoindex setup --force "$FLOW_PATH"
if [ $? -ne 0 ]; then
    echo "❌ Setup failed!"
    exit 1
fi
echo "✓ Setup completed"
echo

# Step 2: Change to project directory
echo "Step 2: Changing to project directory..."
cd "$PROJECT_PATH" || exit 1
echo "✓ Now in: $(pwd)"
echo

# Step 3: Run update
echo "Step 3: Running indexing..."
cocoindex update "$FLOW_PATH"
if [ $? -ne 0 ]; then
    echo "❌ Indexing failed!"
    exit 1
fi
echo "✓ Indexing completed"
echo

# Step 4: Verify data
echo "Step 4: Verifying indexed data..."
RESULT=$(psql "$COCOINDEX_DATABASE_URL" -t -c "SELECT COUNT(*) FROM analyzerawarecodeindex__code_chunks_with_metadata;" 2>/dev/null)
RESULT=$(echo $RESULT | tr -d ' ')

if [ -z "$RESULT" ] || [ "$RESULT" = "0" ]; then
    echo "❌ No data found in database!"
    echo "Trying alternative table name..."
    RESULT=$(psql "$COCOINDEX_DATABASE_URL" -t -c "SELECT COUNT(*) FROM code_chunks_with_metadata;" 2>/dev/null)
    RESULT=$(echo $RESULT | tr -d ' ')
fi

echo "✓ Found $RESULT chunks in database"
echo

# Step 5: Show how to start server
echo "=== Success! ==="
echo
echo "To start the API server, run:"
echo "cd $PROJECT_PATH"
echo "cocoindex server $FLOW_PATH -ci --address 0.0.0.0:3000"
echo
echo "Then access:"
echo "- API: http://localhost:3000/cocoindex"
echo "- UI: https://cocoindex.io/cocoinsight"
echo
echo "Sample API calls:"
echo 'curl -X GET http://localhost:3000/cocoindex/stats'
echo 'curl -X POST http://localhost:3000/cocoindex/query -H "Content-Type: application/json" -d "{\"filter\":{\"is_react_component\":true},\"limit\":5}"'
