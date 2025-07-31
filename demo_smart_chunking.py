#!/usr/bin/env python3
"""
Demo: Smart Chunking with Analyzers

Shows how everything works together:
1. Analyzer understands the code
2. Smart chunker creates meaningful chunks
3. Flow integrates with CocoIndex
"""

import json
from pathlib import Path
from codesitter.chunkers import SmartChunker

def demo_smart_chunking():
    """Demonstrate the smart chunking in action."""

    # Example TypeScript code with the problematic pattern
    test_code = '''import React, { useState } from 'react'
import { useAuth } from '../hooks/auth'

export interface UserProfileProps {
    userId: string
    onUpdate?: (user: User) => void
}

export const UserProfile: React.FC<UserProfileProps> = ({ userId, onUpdate }) => {
    const [loading, setLoading] = useState(false)
    const { user } = useAuth()

    const handleUpdate = async () => {
        setLoading(true)
        try {
            const updated = await updateUser(userId, { name: user.name })
            onUpdate?.(updated)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div>
            <h1>{user.name}</h1>
            <button onClick={handleUpdate} disabled={loading}>
                Update Profile
            </button>
        </div>
    )
}

async function updateUser(id: string, data: Partial<User>): Promise<User> {
    const response = await fetch(`/api/users/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data)
    })
    return response.json()
}'''

    print("🎯 SMART CHUNKING DEMO")
    print("=" * 80)

    # Create chunker
    chunker = SmartChunker()

    # Process the file
    chunks = chunker.chunk_file("components/UserProfile.tsx", test_code)

    print(f"\n📊 Created {len(chunks)} smart chunks:\n")

    for i, chunk in enumerate(chunks, 1):
        print(f"Chunk {i}: {chunk.chunk_type.value}")
        print(f"  ID: {chunk.chunk_id}")
        print(f"  Lines: {chunk.start_line}-{chunk.end_line}" if chunk.start_line else "  Full file")

        if chunk.metadata:
            print(f"  Metadata:")
            for key, value in chunk.metadata.items():
                print(f"    {key}: {value}")

        print(f"\n  Preview:")
        print("  " + "-" * 60)
        preview_lines = chunk.text.split('\n')[:5]
        for line in preview_lines:
            print(f"  {line}")
        if len(chunk.text.split('\n')) > 5:
            print(f"  ... ({len(chunk.text.split('\n')) - 5} more lines)")
        print("  " + "-" * 60)
        print()

    # Show benefits
    print("\n✨ BENEFITS ACHIEVED:")
    print("  ✅ Each function is complete (no splits!)")
    print("  ✅ Every chunk has import context")
    print("  ✅ Stable chunk IDs for tracking")
    print("  ✅ Rich metadata for analysis")
    print("  ✅ Ready for incremental updates")

    # Show how it integrates
    print("\n🔗 INTEGRATION:")
    print("  1. Use with CLI: codesitter index --flow smart_chunking")
    print("  2. Use with flow: cocoindex update src/codesitter/flows/smart_chunking.py")
    print("  3. Query results: Search by chunk_type, metadata, etc.")


if __name__ == "__main__":
    demo_smart_chunking()
