#!/usr/bin/env python3
"""Test the universal extractor with TypeScript code."""

import json
from tree_sitter_language_pack import get_language
from tree_sitter import Parser
from src.codesitter.analyzers.universal_extractor import TypeScriptExtractor

# Test code
test_code = '''
import { useState } from 'react';

interface User {
    id: number;
    name: string;
    email?: string;
}

export async function getUser(id: number): Promise<User | null> {
    const response = await fetch(`/api/users/${id}`);
    return response.json();
}

export const validateUser = (user: User): boolean => {
    return user.name.length > 0;
};

export class UserService {
    private users: User[] = [];

    async addUser(user: User): Promise<void> {
        this.users.push(user);
    }

    findUser(id: number): User | undefined {
        return this.users.find(u => u.id === id);
    }
}
'''

# Parse with tree-sitter
ts_lang = get_language("typescript")
parser = Parser(ts_lang)
tree = parser.parse(test_code.encode())

# Extract structure
extractor = TypeScriptExtractor(ts_lang)
elements = list(extractor.extract_all(tree))

# Pretty print results
print("=== Extracted Elements ===\n")
for element in elements:
    print(f"{element.element_type.upper()}: {element.name}")
    print(f"  Type: {element.node_type}")
    print(f"  Lines: {element.start_line}-{element.end_line}")

    if element.metadata:
        print("  Metadata:")
        for key, value in element.metadata.items():
            if key == 'parameters' and value:
                print(f"    {key}:")
                for param in value:
                    param_str = f"      - {param['name']}"
                    if param.get('type'):
                        param_str += f": {param['type']}"
                    if param.get('optional'):
                        param_str += " (optional)"
                    if param.get('default'):
                        param_str += f" = {param['default']}"
                    print(param_str)
            else:
                print(f"    {key}: {value}")

    if element.children:
        print(f"  Children: {len(element.children)}")
        for child in element.children:
            print(f"    - {child.element_type}: {child.name}")

    print()

# Also output JSON for analysis
output = []
for element in elements:
    elem_dict = {
        'type': element.element_type,
        'name': element.name,
        'node_type': element.node_type,
        'lines': f"{element.start_line}-{element.end_line}",
        'metadata': element.metadata,
        'children': [{'type': c.element_type, 'name': c.name} for c in element.children]
    }
    output.append(elem_dict)

print("\n=== JSON Output ===")
print(json.dumps(output, indent=2))
