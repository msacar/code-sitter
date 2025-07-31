"""Enhanced TypeScript analyzer with Dossier-like capabilities."""

from typing import Iterator, List, Dict, Any, Optional
import logging
import re

from tree_sitter import Language, Parser, Query, Node
from tree_sitter_language_pack import get_language

from ..base import LanguageAnalyzer, CodeChunk, CallRelationship, ImportRelationship
from ..parser_utils import create_parser

logger = logging.getLogger(__name__)


class EnhancedTypeScriptAnalyzer(LanguageAnalyzer):
    """
    Enhanced TypeScript/JavaScript analyzer with detailed extraction.

    Extracts:
    - Detailed function signatures with parameters and types
    - Class definitions with methods
    - Interface and type definitions
    - JSDoc/TSDoc comments
    - Call relationships with context
    - Import/export statements
    """

    def __init__(self):
        # Initialize Tree-sitter languages
        self._ts_language = get_language("typescript")
        self._tsx_language = get_language("tsx")
        self._js_language = get_language("javascript")

        try:
            self._jsx_language = get_language("jsx")
        except Exception:
            logger.warning("JSX language not found, using JavaScript parser")
            self._jsx_language = self._js_language

        self._language_map = {
            ".ts": self._ts_language,
            ".tsx": self._tsx_language,
            ".js": self._js_language,
            ".jsx": self._jsx_language,
        }

        # Enhanced queries for detailed extraction
        self._function_detail_query = """
        (function_declaration
          name: (identifier) @function_name
          parameters: (formal_parameters) @params
          return_type: (_)? @return_type
          body: (statement_block) @body
        ) @function

        (method_definition
          name: (property_identifier) @method_name
          parameters: (formal_parameters) @params
          return_type: (_)? @return_type
          body: (statement_block) @body
        ) @method

        (variable_declarator
          name: (identifier) @var_name
          value: [
            (arrow_function
              parameters: (formal_parameters) @params
              return_type: (_)? @return_type
              body: (_) @body
            ) @arrow
            (function_expression
              name: (identifier)? @func_expr_name
              parameters: (formal_parameters) @params
              return_type: (_)? @return_type
              body: (statement_block) @body
            ) @func_expr
          ]
        ) @var_func
        """

        self._interface_query = """
        (interface_declaration
          name: (type_identifier) @interface_name
          body: (interface_body) @body
        ) @interface

        (type_alias_declaration
          name: (type_identifier) @type_name
          value: (_) @type_value
        ) @type_alias
        """

        self._class_query = """
        (class_declaration
          name: (type_identifier) @class_name
          body: (class_body) @body
        ) @class
        """

        self._jsdoc_query = """
        (comment) @comment
        """

    @property
    def supported_extensions(self) -> List[str]:
        return [".ts", ".tsx", ".js", ".jsx"]

    @property
    def language_name(self) -> str:
        return "typescript"

    def _get_parser_and_language(self, filename: str):
        """Get the appropriate parser and language for a file."""
        import os
        ext = os.path.splitext(filename)[1].lower()
        language = self._language_map.get(ext, self._ts_language)

        # Use utility function that handles different tree-sitter API versions
        parser = create_parser(language)

        return parser, language

    def _extract_parameters(self, params_node: Node, source_text: bytes) -> List[Dict[str, Any]]:
        """Extract parameter details from a parameters node."""
        parameters = []

        if not params_node:
            return parameters

        # Find all parameter nodes
        for child in params_node.children:
            if child.type in ["required_parameter", "optional_parameter"]:
                param_info = {
                    "name": "",
                    "type": "any",
                    "optional": child.type == "optional_parameter"
                }

                # Extract parameter name
                for subchild in child.children:
                    if subchild.type == "identifier":
                        param_info["name"] = subchild.text.decode("utf8")
                    elif subchild.type == "type_annotation":
                        # Extract type
                        type_text = source_text[subchild.start_byte:subchild.end_byte].decode("utf8")
                        param_info["type"] = type_text.strip(": ")

                if param_info["name"]:
                    parameters.append(param_info)

        return parameters

    def _extract_return_type(self, return_node: Node, source_text: bytes) -> str:
        """Extract return type from a return type node."""
        if not return_node:
            return "void"

        type_text = source_text[return_node.start_byte:return_node.end_byte].decode("utf8")
        return type_text.strip(": ")

    def _find_preceding_comment(self, node: Node, source_text: bytes) -> Optional[str]:
        """Find JSDoc comment preceding a node."""
        # This is simplified - a full implementation would parse JSDoc
        start_line = node.start_point[0]
        lines = source_text.decode("utf8").split("\n")

        # Look for comment in preceding lines
        for i in range(start_line - 1, max(0, start_line - 5), -1):
            line = lines[i].strip()
            if line.startswith("/**"):
                # Found start of JSDoc comment
                comment_lines = []
                j = i
                while j < len(lines) and not lines[j].strip().endswith("*/"):
                    comment_lines.append(lines[j])
                    j += 1
                if j < len(lines):
                    comment_lines.append(lines[j])
                return "\n".join(comment_lines)

        return None

    def extract_detailed_signatures(self, chunk: CodeChunk) -> List[Dict[str, Any]]:
        """Extract detailed function/method signatures."""
        parser, language = self._get_parser_and_language(chunk.filename)
        signatures = []

        try:
            source_bytes = bytes(chunk.text, "utf8")
            tree = parser.parse(source_bytes)
            query = Query(language, self._function_detail_query)
            captures = query.captures(tree.root_node)

            current_function = None

            for name, node in captures:
                if name in ["function", "method", "var_func"]:
                    if current_function:
                        signatures.append(current_function)

                    current_function = {
                        "kind": "function" if name == "function" else "method",
                        "name": "",
                        "parameters": [],
                        "returnType": "void",
                        "isAsync": False,
                        "isExport": False,
                        "docstring": "",
                        "line": node.start_point[0] + chunk.start_line,
                        "column": node.start_point[1]
                    }

                    # Check for async
                    node_text = source_bytes[node.start_byte:node.end_byte].decode("utf8")
                    if "async" in node_text[:50]:  # Check first 50 chars
                        current_function["isAsync"] = True

                    # Check for export
                    if node.parent and node.parent.type == "export_statement":
                        current_function["isExport"] = True

                    # Extract JSDoc
                    comment = self._find_preceding_comment(node, source_bytes)
                    if comment:
                        current_function["docstring"] = comment

                elif name in ["function_name", "method_name", "var_name"] and current_function:
                    current_function["name"] = node.text.decode("utf8")

                elif name == "params" and current_function:
                    current_function["parameters"] = self._extract_parameters(node, source_bytes)

                elif name == "return_type" and current_function:
                    current_function["returnType"] = self._extract_return_type(node, source_bytes)

            # Don't forget the last function
            if current_function:
                signatures.append(current_function)

        except Exception as e:
            logger.error(f"Error extracting signatures from {chunk.filename}: {e}")

        return signatures

    def extract_interfaces_and_types(self, chunk: CodeChunk) -> List[Dict[str, Any]]:
        """Extract interface and type definitions."""
        parser, language = self._get_parser_and_language(chunk.filename)
        definitions = []

        try:
            source_bytes = bytes(chunk.text, "utf8")
            tree = parser.parse(source_bytes)
            query = Query(language, self._interface_query)
            captures = query.captures(tree.root_node)

            for name, node in captures:
                if name == "interface":
                    interface_name = None
                    for child_name, child_node in captures:
                        if child_name == "interface_name" and child_node.parent == node:
                            interface_name = child_node.text.decode("utf8")
                            break

                    if interface_name:
                        definitions.append({
                            "kind": "interface",
                            "name": interface_name,
                            "line": node.start_point[0] + chunk.start_line,
                            "isExport": node.parent and node.parent.type == "export_statement"
                        })

                elif name == "type_alias":
                    type_name = None
                    for child_name, child_node in captures:
                        if child_name == "type_name" and child_node.parent == node:
                            type_name = child_node.text.decode("utf8")
                            break

                    if type_name:
                        definitions.append({
                            "kind": "type_alias",
                            "name": type_name,
                            "line": node.start_point[0] + chunk.start_line,
                            "isExport": node.parent and node.parent.type == "export_statement"
                        })

        except Exception as e:
            logger.error(f"Error extracting interfaces from {chunk.filename}: {e}")

        return definitions

    def extract_custom_metadata(self, chunk: CodeChunk) -> Dict[str, Any]:
        """Extract enhanced metadata including detailed signatures."""
        metadata = {}

        # Extract detailed function signatures
        signatures = self.extract_detailed_signatures(chunk)
        if signatures:
            metadata["functions"] = signatures
            metadata["has_functions"] = True
            metadata["function_count"] = len(signatures)

            # Check for specific patterns
            metadata["has_async_functions"] = any(s.get("isAsync") for s in signatures)
            metadata["has_exported_functions"] = any(s.get("isExport") for s in signatures)

        # Extract interfaces and types
        definitions = self.extract_interfaces_and_types(chunk)
        if definitions:
            metadata["definitions"] = definitions
            metadata["has_interfaces"] = any(d["kind"] == "interface" for d in definitions)
            metadata["has_type_aliases"] = any(d["kind"] == "type_alias" for d in definitions)

        # React component detection (enhanced)
        if "React" in chunk.text or "jsx" in chunk.filename.lower():
            for sig in signatures:
                # Check if function returns JSX
                if sig.get("returnType") and ("JSX.Element" in sig["returnType"] or
                                              "ReactElement" in sig["returnType"]):
                    metadata["is_react_component"] = True
                    break
                # Check function body for JSX return
                if "return" in chunk.text and "<" in chunk.text:
                    func_start = chunk.text.find(sig["name"])
                    if func_start > 0:
                        func_text = chunk.text[func_start:]
                        if re.search(r'return\s*\(?\s*<', func_text):
                            metadata["is_react_component"] = True
                            break

        # Test file detection
        if any(pattern in chunk.filename for pattern in ["test", "spec", "__tests__"]):
            metadata["is_test_file"] = True

        return metadata

    # Keep existing methods for compatibility
    def extract_call_relationships(self, chunk: CodeChunk) -> Iterator[CallRelationship]:
        """Extract function calls (existing implementation)."""
        # ... (keep existing implementation)
        return super().extract_call_relationships(chunk)

    def extract_import_relationships(self, chunk: CodeChunk) -> Iterator[ImportRelationship]:
        """Extract imports (existing implementation)."""
        # ... (keep existing implementation)
        return super().extract_import_relationships(chunk)
