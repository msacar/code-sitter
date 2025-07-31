#!/usr/bin/env python3
"""
Compare traditional chunking vs smart chunking.

This shows the dramatic difference in chunk quality.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codesitter.chunkers import SmartChunker


def traditional_chunking(content: str, chunk_size: int = 500) -> list:
    """Simulate traditional size-based chunking."""
    chunks = []
    lines = content.split('\n')
    current_chunk = []
    current_size = 0

    for line in lines:
        line_size = len(line) + 1  # +1 for newline
        if current_size + line_size > chunk_size and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = [line]
            current_size = line_size
        else:
            current_chunk.append(line)
            current_size += line_size

    if current_chunk:
        chunks.append('\n'.join(current_chunk))

    return chunks


def compare_chunking():
    """Compare traditional vs smart chunking."""

    # Real-world example with imports, types, and functions
    test_code = '''import React, { useState, useEffect } from 'react'
import { useQuery } from '@apollo/client'
import { GET_USER_PROFILE } from '../queries/user'
import { UserProfile, UserSettings } from '../types'
import { validateEmail, formatPhoneNumber } from '../utils/validators'
import { LoadingSpinner } from '../components/common'

interface ProfilePageProps {
    userId: string
    onUpdate?: (user: UserProfile) => void
}

export const ProfilePage: React.FC<ProfilePageProps> = ({ userId, onUpdate }) => {
    const [isEditing, setIsEditing] = useState(false)
    const [formData, setFormData] = useState<UserSettings>({
        email: '',
        phone: '',
        notifications: true
    })

    const { data, loading, error } = useQuery(GET_USER_PROFILE, {
        variables: { id: userId }
    })

    useEffect(() => {
        if (data?.user) {
            setFormData({
                email: data.user.email,
                phone: data.user.phone,
                notifications: data.user.settings.notifications
            })
        }
    }, [data])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!validateEmail(formData.email)) {
            alert('Invalid email address')
            return
        }

        // Update user profile
        try {
            const response = await updateUserProfile(userId, formData)
            if (onUpdate) {
                onUpdate(response.user)
            }
            setIsEditing(false)
        } catch (error) {
            console.error('Failed to update profile:', error)
        }
    }

    if (loading) return <LoadingSpinner />
    if (error) return <div>Error: {error.message}</div>

    return (
        <div className="profile-page">
            <h1>User Profile</h1>
            {/* Profile content */}
        </div>
    )
}

async function updateUserProfile(userId: string, data: UserSettings): Promise<any> {
    const response = await fetch(`/api/users/${userId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    return response.json()
}'''

    print("🔍 CHUNKING COMPARISON")
    print("=" * 100)

    # Traditional chunking
    print("\n📦 TRADITIONAL CHUNKING (size-based, 500 chars)")
    print("-" * 100)
    traditional_chunks = traditional_chunking(test_code, 500)

    for i, chunk in enumerate(traditional_chunks):
        print(f"\nChunk {i + 1} ({len(chunk)} chars):")
        print("```")
        print(chunk[:200] + "..." if len(chunk) > 200 else chunk)
        print("```")

        # Analyze problems
        problems = []
        if "=>" in chunk and "const" not in chunk:
            problems.append("❌ Arrow function body without declaration")
        if "}" in chunk and "{" not in chunk:
            problems.append("❌ Closing brace without opening")
        if "{" in chunk and "}" not in chunk:
            problems.append("❌ Opening brace without closing")
        if "import" not in chunk and ("UserProfile" in chunk or "UserSettings" in chunk):
            problems.append("❌ Uses types without import context")

        if problems:
            print("Problems:")
            for p in problems:
                print(f"  {p}")

    # Smart chunking
    print("\n\n🧠 SMART CHUNKING (structure-aware)")
    print("-" * 100)

    chunker = SmartChunker()
    smart_chunks = chunker.chunk_file("ProfilePage.tsx", test_code)

    for i, chunk in enumerate(smart_chunks):
        print(f"\nChunk {i + 1}: {chunk.chunk_type.value}")
        print(f"ID: {chunk.chunk_id}")
        if chunk.metadata:
            print(f"Metadata: {chunk.metadata}")
        print("```")
        preview = chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text
        print(preview)
        print("```")

        # Analyze benefits
        benefits = []
        if chunk.chunk_type.value == "function":
            benefits.append("✅ Complete function with context")
        if chunk.chunk_type.value == "imports":
            benefits.append("✅ All imports grouped together")
        if "import" in chunk.text and chunk.chunk_type.value != "imports":
            benefits.append("✅ Includes necessary imports for context")

        if benefits:
            print("Benefits:")
            for b in benefits:
                print(f"  {b}")

    # Summary
    print("\n\n📊 SUMMARY")
    print("=" * 100)
    print(f"Traditional chunks: {len(traditional_chunks)} (arbitrary splits)")
    print(f"Smart chunks: {len(smart_chunks)} (meaningful units)")
    print("\nTraditional problems:")
    print("- Functions split across chunks")
    print("- Lost import context")
    print("- Broken syntax in chunks")
    print("- Poor incremental update granularity")
    print("\nSmart chunking benefits:")
    print("- Each chunk is self-contained")
    print("- Preserves all context")
    print("- Better for analysis and search")
    print("- Optimal incremental updates")


if __name__ == "__main__":
    compare_chunking()
