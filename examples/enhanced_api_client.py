#!/usr/bin/env python3
"""
Enhanced API Client - Demonstrates querying detailed code analysis data
"""

import requests
import json
from typing import List, Dict, Any, Optional

class EnhancedCodeAnalysisAPI:
    """Client for querying enhanced code analysis via CocoIndex API."""

    def __init__(self, base_url: str = "http://localhost:3000/cocoindex"):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}

    def find_functions_by_name(self, function_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find functions by exact name match."""
        query = {
            "flow_name": "DetailedCodeAnalysis",
            "target_name": "code_chunks_detailed",
            "filter": {
                "function_signatures": {"$contains": f'"name": "{function_name}"'}
            },
            "limit": limit
        }

        response = requests.post(
            f"{self.base_url}/query",
            json=query,
            headers=self.headers
        )

        # Parse the function signatures from results
        results = response.json()
        for result in results:
            if "function_signatures" in result:
                result["parsed_functions"] = json.loads(result["function_signatures"])

        return results

    def find_functions_with_parameters(self, param_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find functions that have parameters of a specific type."""
        query = {
            "flow_name": "DetailedCodeAnalysis",
            "target_name": "code_chunks_detailed",
            "filter": {
                "function_signatures": {"$contains": f'"type": "{param_type}"'}
            },
            "limit": limit
        }

        response = requests.post(
            f"{self.base_url}/query",
            json=query,
            headers=self.headers
        )
        return response.json()

    def find_async_functions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Find all async functions in the codebase."""
        query = {
            "flow_name": "DetailedCodeAnalysis",
            "target_name": "code_chunks_detailed",
            "filter": {
                "function_signatures": {"$contains": '"isAsync": true'}
            },
            "limit": limit
        }

        response = requests.post(
            f"{self.base_url}/query",
            json=query,
            headers=self.headers
        )
        return response.json()

    def find_exported_apis(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Find all exported functions (public API)."""
        query = {
            "flow_name": "DetailedCodeAnalysis",
            "target_name": "code_chunks_detailed",
            "filter": {
                "function_signatures": {"$contains": '"isExport": true'}
            },
            "limit": limit
        }

        response = requests.post(
            f"{self.base_url}/query",
            json=query,
            headers=self.headers
        )
        return response.json()

    def find_functions_returning_type(self, return_type: str, limit: int = 15) -> List[Dict[str, Any]]:
        """Find functions that return a specific type."""
        query = {
            "flow_name": "DetailedCodeAnalysis",
            "target_name": "code_chunks_detailed",
            "filter": {
                "function_signatures": {"$contains": f'"returnType": "{return_type}"'}
            },
            "limit": limit
        }

        response = requests.post(
            f"{self.base_url}/query",
            json=query,
            headers=self.headers
        )
        return response.json()

    def find_interfaces(self, exported_only: bool = False, limit: int = 30) -> List[Dict[str, Any]]:
        """Find TypeScript interfaces."""
        filters = {
            "function_signatures": {"$contains": '"kind": "interface"'}
        }

        if exported_only:
            filters["function_signatures"]["$and"] = [
                {"$contains": '"isExport": true'}
            ]

        query = {
            "flow_name": "DetailedCodeAnalysis",
            "target_name": "code_chunks_detailed",
            "filter": filters,
            "limit": limit
        }

        response = requests.post(
            f"{self.base_url}/query",
            json=query,
            headers=self.headers
        )
        return response.json()

    def analyze_function_complexity(self, filename: str) -> Dict[str, Any]:
        """Analyze function complexity in a specific file."""
        # Get all chunks from the file
        query = {
            "flow_name": "DetailedCodeAnalysis",
            "target_name": "code_chunks_detailed",
            "filter": {
                "filename": filename
            }
        }

        response = requests.post(
            f"{self.base_url}/query",
            json=query,
            headers=self.headers
        )

        results = response.json()

        # Analyze the functions
        analysis = {
            "filename": filename,
            "total_functions": 0,
            "async_functions": 0,
            "exported_functions": 0,
            "average_parameters": 0,
            "functions_by_param_count": {},
            "return_types": {}
        }

        all_functions = []
        for chunk in results:
            if "function_signatures" in chunk:
                functions = json.loads(chunk["function_signatures"])
                all_functions.extend(functions)

        if all_functions:
            analysis["total_functions"] = len(all_functions)
            analysis["async_functions"] = sum(1 for f in all_functions if f.get("isAsync"))
            analysis["exported_functions"] = sum(1 for f in all_functions if f.get("isExport"))

            # Parameter analysis
            param_counts = [len(f.get("parameters", [])) for f in all_functions]
            if param_counts:
                analysis["average_parameters"] = sum(param_counts) / len(param_counts)

                for count in param_counts:
                    analysis["functions_by_param_count"][str(count)] = \
                        analysis["functions_by_param_count"].get(str(count), 0) + 1

            # Return type analysis
            for func in all_functions:
                ret_type = func.get("returnType", "void")
                analysis["return_types"][ret_type] = \
                    analysis["return_types"].get(ret_type, 0) + 1

        return analysis

    def semantic_search_with_context(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search and include function context."""
        # Get embedding
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

        # Search with function context
        search_query = {
            "flow_name": "DetailedCodeAnalysis",
            "target_name": "code_chunks_detailed",
            "vector_search": {
                "field": "embedding",
                "vector": query_embedding,
                "limit": limit
            },
            "fields": ["filename", "chunk_text", "function_signatures", "similarity"]
        }

        response = requests.post(
            f"{self.base_url}/vector_search",
            json=search_query,
            headers=self.headers
        )

        # Parse function signatures in results
        results = response.json()
        for result in results:
            if "function_signatures" in result:
                result["parsed_functions"] = json.loads(result["function_signatures"])

        return results

def main():
    """Example usage of the enhanced API client."""
    api = EnhancedCodeAnalysisAPI()

    print("=== Enhanced Code Analysis Examples ===\n")

    # 1. Find specific function
    print("1. Finding 'useState' functions:")
    try:
        functions = api.find_functions_by_name("useState", limit=5)
        for func in functions[:3]:
            if "parsed_functions" in func:
                for f in func["parsed_functions"]:
                    if f["name"] == "useState":
                        print(f"  - {func['filename']}: {f['name']}({len(f['parameters'])} params)")
    except Exception as e:
        print(f"  Error: {e}")

    # 2. Find async functions
    print("\n2. Async Functions:")
    try:
        async_funcs = api.find_async_functions(limit=10)
        seen = set()
        for result in async_funcs[:5]:
            funcs = json.loads(result.get("function_signatures", "[]"))
            for f in funcs:
                if f.get("isAsync") and f["name"] not in seen:
                    seen.add(f["name"])
                    print(f"  - {f['name']}: {f['returnType']}")
    except Exception as e:
        print(f"  Error: {e}")

    # 3. Find exported APIs
    print("\n3. Exported Functions (Public API):")
    try:
        exported = api.find_exported_apis(limit=10)
        for result in exported[:5]:
            funcs = json.loads(result.get("function_signatures", "[]"))
            for f in funcs:
                if f.get("isExport"):
                    params = ", ".join([p["name"] + ": " + p["type"] for p in f.get("parameters", [])])
                    print(f"  - {f['name']}({params}) -> {f['returnType']}")
    except Exception as e:
        print(f"  Error: {e}")

    # 4. Find Promise-returning functions
    print("\n4. Functions Returning Promises:")
    try:
        promises = api.find_functions_returning_type("Promise", limit=10)
        for result in promises[:5]:
            funcs = json.loads(result.get("function_signatures", "[]"))
            for f in funcs:
                if "Promise" in f.get("returnType", ""):
                    print(f"  - {f['name']}: {f['returnType']}")
    except Exception as e:
        print(f"  Error: {e}")

    # 5. Semantic search with function context
    print("\n5. Semantic Search for 'authentication' with Function Context:")
    try:
        results = api.semantic_search_with_context("user authentication", limit=3)
        for result in results:
            print(f"  - {result['filename']} (similarity: {result.get('similarity', 'N/A'):.3f})")
            if "parsed_functions" in result:
                for f in result["parsed_functions"][:2]:
                    print(f"    Function: {f['name']}({len(f.get('parameters', []))} params)")
    except Exception as e:
        print(f"  Error: {e}")

    # 6. Analyze a specific file
    print("\n6. File Complexity Analysis:")
    try:
        # You would replace this with an actual filename from your project
        analysis = api.analyze_function_complexity("src/components/UserAuth.tsx")
        print(f"  File: {analysis['filename']}")
        print(f"  Total functions: {analysis['total_functions']}")
        print(f"  Async functions: {analysis['async_functions']}")
        print(f"  Exported functions: {analysis['exported_functions']}")
        print(f"  Average parameters: {analysis['average_parameters']:.1f}")
    except Exception as e:
        print(f"  Error: {e}")

if __name__ == "__main__":
    main()
