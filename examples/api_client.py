#!/usr/bin/env python3
"""
Example: Query code analysis data via CocoIndex API
"""

import requests
import json
from typing import List, Dict, Any

class CodeAnalysisAPI:
    """Client for querying code analysis via CocoIndex API."""

    def __init__(self, base_url: str = "http://localhost:3000/cocoindex"):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}

    def search_react_components(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Find React components in the codebase."""
        query = {
            "flow_name": "AnalyzerAwareCodeIndex",  # or "CodeAnalyzerFlow" for analyzer_simple
            "target_name": "code_chunks_with_metadata",  # or "code_analysis" for analyzer_simple
            "filter": {
                "is_react_component": True
            },
            "limit": limit
        }

        response = requests.post(
            f"{self.base_url}/query",
            json=query,
            headers=self.headers
        )
        return response.json()

    def search_typescript_interfaces(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Find TypeScript interfaces."""
        query = {
            "flow_name": "AnalyzerAwareCodeIndex",
            "target_name": "code_chunks_with_metadata",
            "filter": {
                "has_interfaces": True,
                "language": "typescript"
            },
            "limit": limit
        }

        response = requests.post(
            f"{self.base_url}/query",
            json=query,
            headers=self.headers
        )
        return response.json()

    def semantic_search(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search for similar code."""
        # First, get embedding for the query
        embedding_query = {
            "text": query_text,
            "model": "all-MiniLM-L6-v2"
        }

        embedding_response = requests.post(
            f"{self.base_url}/embed",
            json=embedding_query,
            headers=self.headers
        )
        query_embedding = embedding_response.json()["embedding"]

        # Then search with the embedding
        search_query = {
            "flow_name": "AnalyzerAwareCodeIndex",
            "target_name": "code_chunks_with_metadata",
            "vector_search": {
                "field": "embedding",
                "vector": query_embedding,
                "limit": limit
            }
        }

        response = requests.post(
            f"{self.base_url}/vector_search",
            json=search_query,
            headers=self.headers
        )
        return response.json()

    def get_async_test_files(self) -> List[str]:
        """Find test files with async functions."""
        query = {
            "flow_name": "AnalyzerAwareCodeIndex",
            "target_name": "code_chunks_with_metadata",
            "filter": {
                "is_test_file": True,
                "has_async_functions": True
            },
            "fields": ["filename"],
            "distinct": True
        }

        response = requests.post(
            f"{self.base_url}/query",
            json=query,
            headers=self.headers
        )
        return [item["filename"] for item in response.json()]

    def get_file_analysis(self, filename: str) -> List[Dict[str, Any]]:
        """Get all analysis data for a specific file."""
        query = {
            "flow_name": "AnalyzerAwareCodeIndex",
            "target_name": "code_chunks_with_metadata",
            "filter": {
                "filename": filename
            }
        }

        response = requests.post(
            f"{self.base_url}/query",
            json=query,
            headers=self.headers
        )
        return response.json()

def main():
    """Example usage of the API client."""
    # Initialize client
    api = CodeAnalysisAPI()

    print("=== Code Analysis API Examples ===\n")

    # 1. Find React components
    print("1. React Components:")
    try:
        components = api.search_react_components(limit=5)
        for comp in components[:5]:
            print(f"  - {comp['filename']}")
    except Exception as e:
        print(f"  Error: {e}")

    # 2. Find TypeScript interfaces
    print("\n2. TypeScript Interfaces:")
    try:
        interfaces = api.search_typescript_interfaces(limit=5)
        for item in interfaces[:5]:
            print(f"  - {item['filename']}")
    except Exception as e:
        print(f"  Error: {e}")

    # 3. Semantic search
    print("\n3. Semantic Search for 'authentication':")
    try:
        results = api.semantic_search("user authentication", limit=3)
        for result in results:
            print(f"  - {result['filename']} (score: {result.get('similarity', 'N/A')})")
    except Exception as e:
        print(f"  Error: {e}")

    # 4. Find async test files
    print("\n4. Test Files with Async Functions:")
    try:
        test_files = api.get_async_test_files()
        for file in test_files[:5]:
            print(f"  - {file}")
    except Exception as e:
        print(f"  Error: {e}")

if __name__ == "__main__":
    main()
