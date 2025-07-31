#!/bin/bash
# Quick test to see why analyzer shows minimal output

echo "=== Testing Codesitter Analyzer ==="
echo

# Test 1: Analyze the test file that we know has content
echo "1. Testing with known good file:"
cd /Users/mustafaacar/codesitter
codesitter analyze file test_file.ts

echo
echo "2. Testing from your project directory:"
cd /Users/mustafaacar/retter/shortlink

# Check if file exists
if [ -f "modules/shortlink-api/src/services/instanceService.ts" ]; then
    echo "   File exists: modules/shortlink-api/src/services/instanceService.ts"

    # Show first few lines to verify it has content
    echo "   First 10 lines:"
    head -10 modules/shortlink-api/src/services/instanceService.ts | sed 's/^/     /'

    echo
    echo "3. Running analyzer:"
    codesitter analyze file modules/shortlink-api/src/services/instanceService.ts
else
    echo "   ERROR: File not found!"
fi

echo
echo "4. Try with absolute path:"
codesitter analyze file /Users/mustafaacar/retter/shortlink/modules/shortlink-api/src/services/instanceService.ts
