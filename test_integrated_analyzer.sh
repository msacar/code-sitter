#!/bin/bash
# Test the integrated analyzer CLI

echo "Testing Integrated Analyzer CLI..."
echo "================================="

# Test listing analyzers
echo -e "\n1. Testing 'analyze list' command:"
codesitter analyze list | head -10

# Create a test file
cat > /tmp/test_analyzer.ts << 'EOF'
import React from 'react'
import { useState } from 'react'

export function TestComponent() {
    const [count, setCount] = useState(0)

    const handleClick = () => {
        setCount(count + 1)
        console.log('Clicked!')
    }

    return <button onClick={handleClick}>{count}</button>
}
EOF

# Test analyzing the file
echo -e "\n2. Testing 'analyze file' command:"
codesitter analyze file /tmp/test_analyzer.ts

# Test JSON output
echo -e "\n3. Testing JSON output:"
codesitter analyze file /tmp/test_analyzer.ts --json | head -20

# Test calls only
echo -e "\n4. Testing '--calls-only' flag:"
codesitter analyze file /tmp/test_analyzer.ts --calls-only

# Test imports only
echo -e "\n5. Testing '--imports-only' flag:"
codesitter analyze file /tmp/test_analyzer.ts --imports-only

# Clean up
rm /tmp/test_analyzer.ts

echo -e "\n✅ Integrated Analyzer CLI is working!"
echo "Use 'codesitter analyze --help' for more options"
