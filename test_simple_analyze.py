#!/usr/bin/env python3
"""Simple test script to demonstrate the enhanced analyze functionality."""

import subprocess
import json

# First, create the simple test file from the user's example
test_content = '''const users = [
  { id: 1, name: "John" },
  { id: 2, name: "Jane" },
  { id: 3, name: "Bob" }
];

function sayHello(id: number) {
  const user = getUser(id);
  console.log(user?.name.toLowerCase());
  return user?.name.toString();
}

function getUser(id: number) {
  return users.find(u => u.id === id);
}
'''

# Write the test file
with open('test_calls.ts', 'w') as f:
    f.write(test_content)

# Run the analyze command
result = subprocess.run(
    ["python", "-m", "codesitter", "analyze", "file", "test_calls.ts", "--json"],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    data = json.loads(result.stdout)
    print(json.dumps(data, indent=2))
else:
    print(f"Error: {result.stderr}")
