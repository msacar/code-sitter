#!/usr/bin/env python3
"""Explore all node types available in tree-sitter-typescript."""

from tree_sitter_language_pack import get_language
from tree_sitter import Parser
import json

# Test code with various TypeScript constructs
test_code = '''
// Imports
import { Component } from 'react';
import * as fs from 'fs';
import type { User } from './types';

// Interface
interface User {
    id: number;
    name: string;
    email?: string;
}

// Type alias
type UserRole = 'admin' | 'user' | 'guest';

// Enum
enum Status {
    Active = 1,
    Inactive = 0
}

// Class
class UserService {
    private users: User[] = [];

    constructor(private db: Database) {}

    async getUser(id: number): Promise<User | null> {
        return this.users.find(u => u.id === id) || null;
    }

    static createUser(name: string): User {
        return { id: Date.now(), name };
    }
}

// Function declaration
function processUser(user: User): void {
    console.log(user.name);
}

// Arrow function
const validateUser = (user: User): boolean => {
    return user.name.length > 0;
};

// Generator function
function* generateIds(): Generator<number> {
    let id = 1;
    while (true) {
        yield id++;
    }
}

// Generic function
function identity<T>(arg: T): T {
    return arg;
}

// Decorator
@injectable()
class Repository {
    @log()
    save(entity: any): void {
        // implementation
    }
}

// Namespace
namespace Utils {
    export function format(str: string): string {
        return str.trim();
    }
}

// Module declaration
declare module "custom-module" {
    export function customFn(): void;
}

// Type assertion
const name = (user as User).name;

// Const assertion
const config = {
    api: "https://api.example.com"
} as const;
'''

# Parse the code
ts_lang = get_language("typescript")
parser = Parser(ts_lang)
tree = parser.parse(test_code.encode())

def collect_node_types(node, node_types=None, depth=0):
    """Recursively collect all unique node types in the tree."""
    if node_types is None:
        node_types = {}

    # Track this node type and example
    if node.type not in node_types:
        node_types[node.type] = {
            "count": 0,
            "is_named": node.is_named,
            "example": node.text.decode()[:100] + "..." if len(node.text) > 100 else node.text.decode(),
            "has_children": node.child_count > 0
        }
    node_types[node.type]["count"] += 1

    # Recurse to children
    for child in node.children:
        collect_node_types(child, node_types, depth + 1)

    return node_types

# Collect all node types
node_types = collect_node_types(tree.root_node)

# Sort by frequency
sorted_types = sorted(node_types.items(), key=lambda x: x[1]["count"], reverse=True)

print("=== All Node Types in TypeScript ===\n")
print(f"Total unique node types: {len(node_types)}\n")

# Group by category
declarations = []
expressions = []
statements = []
types = []
other = []

for node_type, info in sorted_types:
    if info["is_named"]:  # Only show named nodes
        entry = f"{node_type} (count: {info['count']})"

        if "declaration" in node_type:
            declarations.append(entry)
        elif "expression" in node_type:
            expressions.append(entry)
        elif "statement" in node_type:
            statements.append(entry)
        elif "type" in node_type:
            types.append(entry)
        else:
            other.append(entry)

print("DECLARATIONS:")
for d in declarations:
    print(f"  - {d}")

print("\nSTATEMENTS:")
for s in statements:
    print(f"  - {s}")

print("\nEXPRESSIONS:")
for e in expressions[:10]:  # Limit expressions output
    print(f"  - {e}")
if len(expressions) > 10:
    print(f"  ... and {len(expressions) - 10} more")

print("\nTYPE NODES:")
for t in types:
    print(f"  - {t}")

print("\nOTHER IMPORTANT NODES:")
for o in other[:20]:  # Limit output
    print(f"  - {o}")

# Now let's examine what fields are available on key nodes
print("\n\n=== Node Fields for Key Types ===")

def explore_node_fields(node, target_type):
    """Find a node of the target type and explore its fields."""
    if node.type == target_type:
        return node
    for child in node.children:
        result = explore_node_fields(child, target_type)
        if result:
            return result
    return None

# Explore function declaration
func_node = explore_node_fields(tree.root_node, "function_declaration")
if func_node:
    print("\nfunction_declaration fields:")
    print(f"  - type: {func_node.type}")
    print(f"  - named_child_count: {func_node.named_child_count}")
    print("  - children types:", [child.type for child in func_node.named_children])

    # Try to get field names
    for i, child in enumerate(func_node.named_children):
        field_name = func_node.field_name_for_named_child(i)
        if field_name:
            print(f"  - field '{field_name}': {child.type} = {child.text.decode()[:50]}")
