"""
Utility functions for tree-sitter parser creation.
Handles API differences between tree-sitter versions.
"""

from tree_sitter import Parser, Language, Query, QueryCursor
import logging

logger = logging.getLogger(__name__)


def create_parser(language: Language) -> Parser:
    """
    Create a tree-sitter parser with the given language.
    Handles API differences between tree-sitter versions.
    """
    # Try the newer API first (Parser constructor with language)
    try:
        return Parser(language)
    except Exception as e:
        logger.debug(f"Failed to create parser with language in constructor: {e}")

    # Try creating parser and setting language
    parser = Parser()

    # Try the newer API (parser.language property)
    if hasattr(parser, 'language') and not callable(getattr(parser, 'language')):
        try:
            parser.language = language
            return parser
        except Exception as e:
            logger.debug(f"Failed to set parser.language property: {e}")

    # Try the older API (set_language method)
    if hasattr(parser, 'set_language'):
        try:
            parser.set_language(language)
            return parser
        except Exception as e:
            logger.debug(f"Failed to use set_language method: {e}")

    raise RuntimeError(
        f"Could not create parser with language. "
        f"Parser type: {type(parser)}, Language type: {type(language)}, "
        f"Parser attributes: {[attr for attr in dir(parser) if not attr.startswith('_')]}"
    )


def query_captures(query: Query, node, start_byte=None, end_byte=None):
    """
    Get captures from a query using the correct API.

    In the current tree-sitter API (0.25.0+), Query objects don't have a captures() method.
    Instead, we need to use QueryCursor to execute queries.
    """
    # Create a QueryCursor with the query
    cursor = QueryCursor(query)

    # Set byte range if provided
    if start_byte is not None and end_byte is not None:
        cursor.set_byte_range(start_byte, end_byte)

    # Get captures using the cursor
    captures_dict = cursor.captures(node)

    # Convert the dictionary format to a list of (node, name) tuples
    # to match the old API format that the analyzers expect
    captures_list = []
    for capture_name, nodes in captures_dict.items():
        for node in nodes:
            captures_list.append((node, capture_name))

    return captures_list


def query_matches(query: Query, node, start_byte=None, end_byte=None):
    """
    Get matches from a query using the correct API.

    Returns matches in the format: [(pattern_index, {capture_name: [nodes]}), ...]
    """
    # Create a QueryCursor with the query
    cursor = QueryCursor(query)

    # Set byte range if provided
    if start_byte is not None and end_byte is not None:
        cursor.set_byte_range(start_byte, end_byte)

    # Get matches using the cursor
    return cursor.matches(node)
