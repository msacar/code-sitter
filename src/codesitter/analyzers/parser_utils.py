"""
Utility functions for tree-sitter parser creation.
Handles API differences between tree-sitter versions.
"""

from tree_sitter import Parser, Language, Query
import logging

logger = logging.getLogger(__name__)


def create_parser(language: Language) -> Parser:
    """
    Create a tree-sitter parser with the given language.
    Handles API differences between tree-sitter versions.
    """
    parser = Parser()

    # Try the newer API first (parser.language property)
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

    # Try passing language to constructor
    try:
        return Parser(language)
    except Exception as e:
        logger.debug(f"Failed to pass language to Parser constructor: {e}")

    # Last resort - check if we need to call Language() on the language object
    try:
        if hasattr(language, '__call__'):
            lang_instance = language()
            parser = Parser()
            if hasattr(parser, 'set_language'):
                parser.set_language(lang_instance)
            else:
                parser.language = lang_instance
            return parser
    except Exception as e:
        logger.debug(f"Failed to instantiate language: {e}")

    raise RuntimeError(
        f"Could not create parser with language. "
        f"Parser type: {type(parser)}, Language type: {type(language)}, "
        f"Parser attributes: {[attr for attr in dir(parser) if not attr.startswith('_')]}"
    )


def query_captures(query: Query, node, start_byte=None, end_byte=None):
    """
    Get captures from a query, handling API differences between tree-sitter versions.

    In newer versions of tree-sitter, captures() requires byte range parameters.
    """
    # Try the newer API first (with byte range)
    if hasattr(query, 'captures') and start_byte is not None and end_byte is not None:
        try:
            return query.captures(node, start_byte=start_byte, end_byte=end_byte)
        except TypeError:
            pass

    # Try with positional byte range tuple
    if hasattr(query, 'captures') and start_byte is not None and end_byte is not None:
        try:
            return query.captures(node, (start_byte, end_byte))
        except TypeError:
            pass

    # Try the older API (without byte range)
    if hasattr(query, 'captures'):
        try:
            return query.captures(node)
        except TypeError as e:
            # If it fails due to missing arguments, try with node's byte range
            if 'start_byte' in str(e) or 'positional argument' in str(e):
                try:
                    return query.captures(node, start_byte=node.start_byte, end_byte=node.end_byte)
                except:
                    try:
                        return query.captures(node, (node.start_byte, node.end_byte))
                    except:
                        pass

    # Try matches() as alternative
    if hasattr(query, 'matches'):
        try:
            matches = query.matches(node)
            # Convert matches to captures format
            captures = []
            for match in matches:
                for capture in match[1]:
                    captures.append(capture)
            return captures
        except:
            pass

    raise RuntimeError(
        f"Could not execute query. Query type: {type(query)}, "
        f"Query methods: {[m for m in dir(query) if not m.startswith('_') and callable(getattr(query, m))]}"
    )
