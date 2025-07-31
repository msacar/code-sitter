#!/bin/bash
# Final test of the fixed analyzer

echo "=== Testing Fixed Codesitter Analyzer ==="
echo

# Test from your project directory
cd /Users/mustafaacar/retter/shortlink

# Make sure we have the latest changes
export PYTHONPATH="/Users/mustafaacar/codesitter/src:$PYTHONPATH"

echo "1. Testing with your TypeScript file:"
echo "   File: modules/shortlink-api/src/services/instanceService.ts"
echo

codesitter analyze file modules/shortlink-api/src/services/instanceService.ts

echo
echo "================================"
echo "2. Testing with absolute path:"
echo

codesitter analyze file /Users/mustafaacar/retter/shortlink/modules/shortlink-api/src/services/instanceService.ts

echo
echo "================================"
echo "3. If the above still shows minimal output, let's check with the test file:"
echo

codesitter analyze file /Users/mustafaacar/codesitter/test_file.ts
