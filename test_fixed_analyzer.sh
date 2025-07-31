#!/bin/bash
# Test the fixed analyzer

cd /Users/mustafaacar/retter/shortlink

echo "=== Testing Fixed TypeScript Analyzer ==="
echo

# First, ensure we're using the updated code
export PYTHONPATH="/Users/mustafaacar/codesitter/src:$PYTHONPATH"

# Test 1: Simple test file
echo "1. Testing with codesitter test file:"
codesitter analyze file /Users/mustafaacar/codesitter/test_file.ts

echo
echo "2. Testing with your project file:"
codesitter analyze file modules/shortlink-api/src/services/instanceService.ts

echo
echo "3. Testing with debug script again:"
python /Users/mustafaacar/codesitter/debug_specific_file.py modules/shortlink-api/src/services/instanceService.ts
