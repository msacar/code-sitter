"""
Query Interface for Code Index

This module provides search functionality for the indexed TypeScript codebase,
including symbol search, semantic search, and call-site analysis.
"""

import json
import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
import psycopg2
from pgvector.psycopg2 import register_vector
import logging

logger = logging.getLogger(__name__)


class CodeSearchEngine:
    """Main search engine for querying indexed code."""

    def __init__(
        self,
        db_url: Optional[str] = None,
        json_index_path: str = "./code_index.json",
        symbol_index_path: str = "./symbol_index.json"
    ):
        """
        Initialize the search engine.

        Args:
            db_url: PostgreSQL connection URL (if using Postgres)
            json_index_path: Path to JSON index file (fallback)
            symbol_index_path: Path to symbol index file
        """
        self.db_url = db_url or os.getenv("DATABASE_URL")
        self.json_index_path = json_index_path
        self.symbol_index_path = symbol_index_path

        # Initialize embedding model for semantic search
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

        # Load indices
        self._load_indices()

    def _load_indices(self):
        """Load symbol index and connect to database if available."""
        # Load symbol index
        if Path(self.symbol_index_path).exists():
            with open(self.symbol_index_path, 'r') as f:
                self.symbol_index = json.load(f)
        else:
            self.symbol_index = {}
            logger.warning(f"Symbol index not found at {self.symbol_index_path}")

        # Connect to database if available
        self.conn = None
        if self.db_url:
            try:
                self.conn = psycopg2.connect(self.db_url)
                register_vector(self.conn)
                logger.info("Connected to PostgreSQL database")
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                self.conn = None

        # Load JSON index as fallback
        self.json_index = []
        if not self.conn and Path(self.json_index_path).exists():
            with open(self.json_index_path, 'r') as f:
                self.json_index = json.load(f)
            logger.info(f"Loaded {len(self.json_index)} chunks from JSON index")

    def search_symbol(self, symbol_name: str) -> List[Dict[str, Any]]:
        """
        Search for a symbol by exact or partial name match.

        Args:
            symbol_name: Name of the symbol to search for

        Returns:
            List of locations where the symbol is defined
        """
        results = []

        # Exact match
        if symbol_name in self.symbol_index:
            results.extend(self.symbol_index[symbol_name])

        # Partial match
        for symbol, locations in self.symbol_index.items():
            if symbol_name.lower() in symbol.lower() and symbol != symbol_name:
                for loc in locations:
                    loc['matched_symbol'] = symbol
                    results.append(loc)

        return results

    def semantic_search(
        self,
        query: str,
        k: int = 10,
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using vector embeddings.

        Args:
            query: Natural language query
            k: Number of results to return
            threshold: Minimum similarity threshold

        Returns:
            List of relevant code chunks
        """
        # Generate query embedding
        query_embedding = self.embedder.encode(query)

        if self.conn:
            return self._semantic_search_postgres(query_embedding, k, threshold)
        else:
            return self._semantic_search_json(query_embedding, k, threshold)

    def _semantic_search_postgres(
        self,
        query_embedding: np.ndarray,
        k: int,
        threshold: float
    ) -> List[Dict[str, Any]]:
        """Perform semantic search using PostgreSQL with pgvector."""
        cursor = self.conn.cursor()

        # Convert to list for pgvector
        query_vec = query_embedding.tolist()

        # Query using cosine similarity
        cursor.execute("""
            SELECT
                filename,
                chunk_index,
                chunk_text,
                start_line,
                end_line,
                node_type,
                symbols,
                1 - (embedding <=> %s::vector) as similarity
            FROM typescript_code_index
            WHERE 1 - (embedding <=> %s::vector) > %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (query_vec, query_vec, threshold, query_vec, k))

        results = []
        for row in cursor.fetchall():
            results.append({
                'filename': row[0],
                'chunk_index': row[1],
                'text': row[2],
                'start_line': row[3],
                'end_line': row[4],
                'node_type': row[5],
                'symbols': row[6],
                'similarity': row[7]
            })

        cursor.close()
        return results

    def _semantic_search_json(
        self,
        query_embedding: np.ndarray,
        k: int,
        threshold: float
    ) -> List[Dict[str, Any]]:
        """Perform semantic search using JSON index."""
        results = []

        for item in self.json_index:
            if 'embedding' not in item or not item['embedding']:
                continue

            # Calculate cosine similarity
            chunk_embedding = np.array(item['embedding'])
            similarity = np.dot(query_embedding, chunk_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
            )

            if similarity > threshold:
                chunk_data = item.get('chunk_data', {})
                results.append({
                    'filename': chunk_data.get('filename'),
                    'text': chunk_data.get('text'),
                    'start_line': chunk_data.get('start_line'),
                    'end_line': chunk_data.get('end_line'),
                    'node_type': chunk_data.get('node_type'),
                    'symbols': chunk_data.get('symbols', []),
                    'similarity': float(similarity)
                })

        # Sort by similarity and return top k
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:k]

    def find_function_calls(
        self,
        function_name: str
    ) -> List[Dict[str, Any]]:
        """
        Find all locations where a function is called.

        Args:
            function_name: Name of the function to find calls for

        Returns:
            List of call sites with context
        """
        # Use semantic search to find potential call sites
        query = f"calling {function_name} function with parameters"
        candidates = self.semantic_search(query, k=50, threshold=0.3)

        # Filter for actual function calls
        call_sites = []
        for candidate in candidates:
            text = candidate.get('text', '')
            # Simple heuristic - look for function name followed by parentheses
            if f"{function_name}(" in text:
                # Extract the line containing the call
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    if f"{function_name}(" in line:
                        call_sites.append({
                            'filename': candidate['filename'],
                            'line': candidate['start_line'] + i,
                            'call_context': line.strip(),
                            'full_context': text,
                            'node_type': candidate.get('node_type')
                        })

        return call_sites

    def get_function_definition(self, function_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the full definition of a function.

        Args:
            function_name: Name of the function

        Returns:
            Function definition with full context
        """
        # First check symbol index
        symbols = self.search_symbol(function_name)

        if symbols:
            # For each symbol location, fetch the full chunk
            for symbol in symbols:
                # Could enhance this to fetch the actual chunk from DB/JSON
                return symbol

        # Fallback to semantic search
        results = self.semantic_search(f"function {function_name} definition", k=5)
        for result in results:
            if function_name in result.get('symbols', []):
                return result

        return None

    def analyze_dependencies(self, filename: str) -> Dict[str, List[str]]:
        """
        Analyze import/export dependencies for a file.

        Args:
            filename: Path to the file

        Returns:
            Dictionary with 'imports' and 'exports' lists
        """
        # Search for chunks from this file
        file_chunks = []

        if self.conn:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT chunk_text, node_type, symbols
                FROM typescript_code_index
                WHERE filename = %s
                ORDER BY chunk_index
            """, (filename,))

            for row in cursor.fetchall():
                file_chunks.append({
                    'text': row[0],
                    'node_type': row[1],
                    'symbols': row[2]
                })
            cursor.close()
        else:
            # Use JSON index
            for item in self.json_index:
                chunk_data = item.get('chunk_data', {})
                if chunk_data.get('filename') == filename:
                    file_chunks.append(chunk_data)

        # Extract imports and exports
        imports = []
        exports = []

        for chunk in file_chunks:
            text = chunk.get('text', '')

            # Simple regex-based extraction (could be enhanced with AST)
            if 'import' in text:
                lines = text.split('\n')
                for line in lines:
                    if line.strip().startswith('import'):
                        imports.append(line.strip())

            if 'export' in text:
                lines = text.split('\n')
                for line in lines:
                    if line.strip().startswith('export'):
                        exports.append(line.strip())

        return {
            'imports': imports,
            'exports': exports
        }

    def close(self):
        """Close database connection if open."""
        if self.conn:
            self.conn.close()


def format_search_results(results: List[Dict[str, Any]], max_results: int = 5) -> str:
    """Format search results for display."""
    output = []

    for i, result in enumerate(results[:max_results]):
        output.append(f"\n--- Result {i+1} ---")
        output.append(f"File: {result.get('filename', 'Unknown')}")
        output.append(f"Lines: {result.get('start_line', '?')}-{result.get('end_line', '?')}")

        if 'similarity' in result:
            output.append(f"Similarity: {result['similarity']:.3f}")

        if 'symbols' in result and result['symbols']:
            output.append(f"Symbols: {', '.join(result['symbols'])}")

        output.append(f"Type: {result.get('node_type', 'Unknown')}")
        output.append("\nCode:")
        output.append(result.get('text', '')[:200] + "...")
        output.append("-" * 50)

    return '\n'.join(output)
