#!/usr/bin/env python3
"""Debug script to test TypeScript analyzer directly."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codesitter.analyzers import (
    register_defaults,
    auto_discover_analyzers,
    get_analyzer,
    get_registry,
)
from codesitter.analyzers.base import CodeChunk

def test_typescript_analyzer():
    """Test TypeScript analyzer functionality."""
    print("=== TypeScript Analyzer Test ===\n")

    # Initialize analyzers
    print("1. Initializing analyzers...")
    register_defaults()
    auto_discover_analyzers()

    # Check registered analyzers
    registry = get_registry()
    supported = registry.list_supported_extensions()
    print(f"   Supported extensions: {list(supported.keys())}")

    # Test TypeScript file
    test_file = "test.ts"
    analyzer = get_analyzer(test_file)

    if not analyzer:
        print(f"\n✗ No analyzer found for {test_file}")
        return

    print(f"\n2. Analyzer for {test_file}: {analyzer.__class__.__name__}")
    print(f"   Language: {analyzer.language_name}")
    print(f"   Extensions: {analyzer.supported_extensions}")

    # Test code sample
    test_code = '''
import { Component } from 'react';
import * as utils from './utils';

interface Props {
    name: string;
    age: number;
}

export async function processData(data: any[]): Promise<void> {
    console.log("Processing...");
    utils.validate(data);
    await utils.save(data);
}

export class UserComponent extends Component<Props> {
    render() {
        return <div>Hello {this.props.name}</div>;
    }
}
'''

    print("\n3. Testing analysis on sample code...")

    # Create chunk
    chunk = CodeChunk(
        text=test_code,
        filename=test_file,
        start_line=0,
        end_line=20,
        node_type="",
        symbols=[]
    )

    # Test metadata extraction
    print("\n4. Extracting custom metadata...")
    try:
        metadata = analyzer.extract_custom_metadata(chunk)
        for key, value in metadata.items():
            print(f"   {key}: {value}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test call extraction
    print("\n5. Extracting call relationships...")
    try:
        calls = list(analyzer.extract_call_relationships(chunk))
        print(f"   Found {len(calls)} calls:")
        for call in calls:
            print(f"   - {call.caller} → {call.callee}({', '.join(call.arguments)})")
    except Exception as e:
        print(f"   Error: {e}")

    # Test import extraction
    print("\n6. Extracting import relationships...")
    try:
        imports = list(analyzer.extract_import_relationships(chunk))
        print(f"   Found {len(imports)} imports:")
        for imp in imports:
            print(f"   - from '{imp.imported_from}' import {', '.join(imp.imported_items)} [{imp.import_type}]")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_typescript_analyzer()
