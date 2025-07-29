"""CocoIndex flow definitions for code indexing.

This module contains various flow configurations for indexing code
with different levels of complexity and features.

Available flows:
- basic: Minimal flow with basic file discovery and JSON output
- simple: Multi-language support with syntax-aware chunking (default)
- enhanced: JavaScript/TypeScript focused with call-site extraction
- flexible: Advanced flow with pluggable language analyzers

Usage:
    # From command line
    cocoindex update src/code_sitter/flows/simple.py

    # Or via code-sitter CLI
    code-sitter index --flow simple
"""
