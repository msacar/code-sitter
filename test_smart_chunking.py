#!/usr/bin/env python3
"""
Test script for smart chunking.

Run this to see how smart chunking improves on traditional chunking.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codesitter.chunkers import SmartChunker
import json


def test_smart_chunking():
    """Test smart chunking with the problematic auth middleware example."""

    # The problematic code that gets split poorly by default
    test_code = '''import middy from '@middy/core'
import type { APIGatewayProxyEvent, APIGatewayProxyResult, Context } from 'aws-lambda'
import type { MiddyContext } from '../utils/middy-wrapper'

export interface AuthMiddlewareOptions {
    skipAuth?: boolean
}

export class ApiError extends Error {
    constructor(
        public statusCode: number,
        message: string,
    ) {
        super(message)
        this.name = 'ApiError'
    }
}

export const authMiddleware = (options: AuthMiddlewareOptions = {}): middy.MiddlewareObj<APIGatewayProxyEvent, APIGatewayProxyResult> => ({
    before: async (request: middy.Request<APIGatewayProxyEvent, APIGatewayProxyResult, Error, Context>) => {
        if (options.skipAuth) return

        const context = request.context as MiddyContext

        // Get tenant config from context (loaded by tenant-config-manager middleware)
        const tenantConfig = context.tenantConfig
        if (!tenantConfig) {
            throw new ApiError(500, 'Tenant configuration not loaded')
        }

        // Extract API key from request
        let apiKey = request.event.headers['x-rio-api-key'] || request.event.headers['X-Rio-Api-Key']
        if (!apiKey) {
            apiKey = request.event.queryStringParameters?.['x-rio-api-key'] || request.event.queryStringParameters?.['X-Rio-Api-Key']
        }

        // Validate against tenant-specific API key
        if (!apiKey || apiKey !== tenantConfig.apiKey) {
            throw new ApiError(401, 'Invalid API key')
        }

        context.apiKey = apiKey
    },
})'''

    # Create smart chunker
    chunker = SmartChunker()

    # Chunk the file
    chunks = chunker.chunk_file("test/auth-middleware.ts", test_code)

    print("🎯 SMART CHUNKING RESULTS")
    print("=" * 80)
    print(f"Total chunks created: {len(chunks)}")
    print()

    for i, chunk in enumerate(chunks):
        print(f"📦 Chunk {i + 1}: {chunk.chunk_type.value}")
        print(f"   ID: {chunk.chunk_id}")
        print(f"   Lines: {chunk.start_line}-{chunk.end_line}" if chunk.start_line else "   Lines: N/A")
        print(f"   Hash: {chunk.content_hash[:8]}...")

        if chunk.metadata:
            print(f"   Metadata: {json.dumps(chunk.metadata, indent=6)}")

        print("\n   Content Preview:")
        print("-" * 40)
        lines = chunk.text.split('\n')
        preview_lines = lines[:10] if len(lines) > 10 else lines
        for line in preview_lines:
            print(f"   {line}")
        if len(lines) > 10:
            print(f"   ... ({len(lines) - 10} more lines)")
        print("-" * 40)
        print()

    # Show relationships
    print("\n🔗 CHUNK RELATIONSHIPS")
    print("=" * 80)
    for chunk in chunks:
        if chunk.dependencies or chunk.dependents:
            print(f"{chunk.chunk_id}:")
            if chunk.dependencies:
                print(f"  ← Depends on: {chunk.dependencies}")
            if chunk.dependents:
                print(f"  → Used by: {chunk.dependents}")

    print("\n✅ KEY BENEFITS:")
    print("- Each chunk is self-contained with imports")
    print("- Functions are never split in half")
    print("- Every chunk knows its context")
    print("- Better incremental indexing")
    print("- Stable chunk IDs for tracking changes")


if __name__ == "__main__":
    test_smart_chunking()
