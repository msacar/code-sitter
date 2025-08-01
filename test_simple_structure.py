#!/usr/bin/env python3
"""Simple test of structure extraction."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from codesitter.analyzers import register_defaults, auto_discover_analyzers, get_analyzer
from codesitter.analyzers.base import CodeChunk

# Initialize analyzers
register_defaults()
auto_discover_analyzers()

# Test code
test_code = '''
interface User {
    id: number;
    name: string;
}

export async function getUser(id: number): Promise<User | null> {
    return null;
}

export class UserService {
    async addUser(user: User): Promise<void> {
        console.log(user);
    }
}
'''

# Get analyzer
analyzer = get_analyzer("test.ts")
if not analyzer:
    print("No analyzer found!")
    sys.exit(1)

print(f"Analyzer: {analyzer.__class__.__name__}")

# Create chunk
chunk = CodeChunk(
    text=test_code,
    filename="test.ts",
    start_line=1,
    end_line=len(test_code.split('\n')),
    node_type="file",
    symbols=[]
)

# Extract structure
print("\nExtracting structure...")
try:
    elements = list(analyzer.extract_structure(chunk))
    print(f"\nFound {len(elements)} elements:")
    for elem in elements:
        print(f"\n{elem.element_type.upper()}: {elem.name}")
        print(f"  Lines: {elem.start_line}-{elem.end_line}")
        if elem.metadata:
            print("  Metadata:")
            for k, v in elem.metadata.items():
                if k != 'filename':
                    print(f"    {k}: {v}")
        if elem.children:
            print(f"  Children: {len(elem.children)}")
            for child in elem.children:
                print(f"    - {child.element_type}: {child.name}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
