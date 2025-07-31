#!/usr/bin/env python3
"""
Quick test to verify smart chunking is working correctly.
Run this from the codesitter directory.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from codesitter.chunkers import SmartChunker
    print("✅ Smart chunker imports successfully!")

    # Test with a simple example
    chunker = SmartChunker()

    test_code = """
import React from 'react'

export function Hello() {
    return <div>Hello World</div>
}

export function Goodbye() {
    return <div>Goodbye!</div>
}
"""

    chunks = chunker.chunk_file("test.tsx", test_code)
    print(f"✅ Created {len(chunks)} chunks")

    for chunk in chunks:
        print(f"  - {chunk.chunk_type.value}: {chunk.chunk_id}")

    print("\n✨ Smart chunking is working! Try it with:")
    print("   codesitter index --flow smart_chunking")

except Exception as e:
    print(f"❌ Error: {e}")
    print("\nMake sure you're in the codesitter directory and have run:")
    print("   uv pip install -e .")
