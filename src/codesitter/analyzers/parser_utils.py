"""
Utility functions for tree-sitter parser creation.
Handles API differences between tree-sitter versions.
"""

from tree_sitter import Parser, Language
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
