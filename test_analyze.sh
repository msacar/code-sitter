#!/bin/bash
cd /Users/mustafaacar/codesitter
python -m codesitter analyze file test_calls_enhanced.ts --json | python -c "
import sys
import json

data = json.load(sys.stdin)

# Pretty print the full output
print(json.dumps(data, indent=2))

# Check function call associations
print('\n=== Function Call Associations ===')
for elem in data.get('structure', []):
    if elem['type'] == 'function' and 'calls' in elem.get('metadata', {}):
        print(f\"\\nFunction: {elem['name']}\")
        print(f\"  Has {len(elem['metadata']['calls'])} calls:\")
        for call in elem['metadata']['calls']:
            args = ', '.join(call['arguments']) if call['arguments'] else ''
            print(f\"    - {call['callee']}({args}) at line {call['line']}\")
"
