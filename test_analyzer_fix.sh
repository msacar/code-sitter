#!/bin/bash
# Test the analyzer fix

echo "Testing Analyzer CLI Fix..."
echo "=========================="

# Create a test TypeScript file
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

echo -e "\n1. Testing 'analyze list' command:"
codesitter analyze list

echo -e "\n2. Testing 'analyze file' command:"
codesitter analyze file /tmp/test_analyzer.ts

echo -e "\n3. Testing JSON output:"
codesitter analyze file /tmp/test_analyzer.ts --json | python -m json.tool | head -20

# Clean up
rm /tmp/test_analyzer.ts

echo -e "\n✅ Test complete!"
