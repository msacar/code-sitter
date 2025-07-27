"""TypeScript/JavaScript language analyzer."""

from typing import Iterator, List, Dict, Any
import logging

from tree_sitter import Language, Parser, Query
import tree_sitter_typescript as ts_typescript
import tree_sitter_javascript as ts_javascript

from ..base import LanguageAnalyzer, CodeChunk, CallRelationship, ImportRelationship

logger = logging.getLogger(__name__)


class TypeScriptAnalyzer(LanguageAnalyzer):
    """
    Analyzer for TypeScript and JavaScript files.

    Extracts:
    - Function call relationships
    - Import/export statements
    - React component usage
    - Type definitions
    """

    def __init__(self):
        # Initialize Tree-sitter languages
        self._ts_language = Language(ts_typescript.language_typescript(), "typescript")
        self._tsx_language = Language(ts_typescript.language_tsx(), "tsx")
        self._js_language = Language(ts_javascript.language_javascript(), "javascript")
        self._jsx_language = Language(ts_javascript.language_jsx(), "jsx")

        self._language_map = {
            ".ts": self._ts_language,
            ".tsx": self._tsx_language,
            ".js": self._js_language,
            ".jsx": self._jsx_language,
        }

        # Define queries
        self._call_query = """
        (call_expression
          function: [
            (identifier) @callee
            (member_expression
              property: (property_identifier) @callee
            )
          ]
          arguments: (arguments) @args
        ) @call
        """

        self._import_query = """
        (import_statement
          source: (string) @source
        ) @import

        (import_clause
          (identifier) @default_import
        )

        (import_clause
          (named_imports
            (import_specifier
              name: (identifier) @named_import
            )
          )
        )

        (import_clause
          (namespace_import
            (identifier) @namespace_import
          )
        )
        """

        self._function_query = """
        (function_declaration
          name: (identifier) @function_name
        ) @function

        (method_definition
          name: (property_identifier) @method_name
        ) @method

        (variable_declarator
          name: (identifier) @var_name
          value: [
            (arrow_function) @arrow
            (function_expression) @func_expr
          ]
        ) @var_func
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

        parser = Parser()
        parser.set_language(language)

        return parser, language

    def extract_call_relationships(
        self,
        chunk: CodeChunk
    ) -> Iterator[CallRelationship]:
        """Extract function calls from TypeScript/JavaScript code."""
        parser, language = self._get_parser_and_language(chunk.filename)

        try:
            tree = parser.parse(bytes(chunk.text, "utf8"))
            query = Query(language, self._call_query)
            captures = query.captures(tree.root_node)

            # Find containing function for context
            func_query = Query(language, self._function_query)
            func_captures = func_query.captures(tree.root_node)

            # Build a map of byte ranges to function names
            func_ranges = {}
            for name, node in func_captures:
                if name in ["function_name", "method_name", "var_name"]:
                    func_name = node.text.decode("utf8")
                    parent = node.parent
                    while parent and parent.type not in ["function_declaration", "method_definition", "variable_declarator"]:
                        parent = parent.parent
                    if parent:
                        func_ranges[(parent.start_byte, parent.end_byte)] = func_name

            # Process call expressions
            for name, node in captures:
                if name == "call":
                    # Find callee
                    callee = None
                    args_text = ""

                    for child_name, child_node in captures:
                        if child_name == "callee" and child_node.start_byte >= node.start_byte and child_node.end_byte <= node.end_byte:
                            callee = child_node.text.decode("utf8")
                        elif child_name == "args" and child_node.start_byte >= node.start_byte and child_node.end_byte <= node.end_byte:
                            args_text = child_node.text.decode("utf8")

                    if callee:
                        # Find containing function
                        caller = "anonymous"
                        for (start, end), func_name in func_ranges.items():
                            if start <= node.start_byte <= end:
                                caller = func_name
                                break

                        # Parse arguments (simple extraction)
                        args = []
                        if args_text and len(args_text) > 2:
                            # Remove parentheses and split
                            args_content = args_text[1:-1].strip()
                            if args_content:
                                # Simple split (could be improved with proper parsing)
                                args = [arg.strip() for arg in args_content.split(",")]

                        yield CallRelationship(
                            filename=chunk.filename,
                            caller=caller,
                            callee=callee,
                            arguments=args,
                            line=node.start_point[0] + chunk.start_line,
                            column=node.start_point[1] + 1,
                            context=chunk.text[max(0, node.start_byte-50):min(len(chunk.text), node.end_byte+50)]
                        )

        except Exception as e:
            logger.error(f"Error extracting calls from {chunk.filename}: {e}")

    def extract_import_relationships(
        self,
        chunk: CodeChunk
    ) -> Iterator[ImportRelationship]:
        """Extract import statements from TypeScript/JavaScript code."""
        parser, language = self._get_parser_and_language(chunk.filename)

        try:
            tree = parser.parse(bytes(chunk.text, "utf8"))
            query = Query(language, self._import_query)
            captures = query.captures(tree.root_node)

            # Group captures by import statement
            imports = {}

            for name, node in captures:
                if name == "import":
                    imports[node.start_byte] = {
                        "node": node,
                        "source": None,
                        "default": None,
                        "named": [],
                        "namespace": None
                    }
                elif name == "source":
                    # Find the containing import
                    for start, imp in imports.items():
                        if imp["node"].start_byte <= node.start_byte <= imp["node"].end_byte:
                            imp["source"] = node.text.decode("utf8").strip("'\"")
                            break
                elif name == "default_import":
                    for start, imp in imports.items():
                        if imp["node"].start_byte <= node.start_byte <= imp["node"].end_byte:
                            imp["default"] = node.text.decode("utf8")
                            break
                elif name == "named_import":
                    for start, imp in imports.items():
                        if imp["node"].start_byte <= node.start_byte <= imp["node"].end_byte:
                            imp["named"].append(node.text.decode("utf8"))
                            break
                elif name == "namespace_import":
                    for start, imp in imports.items():
                        if imp["node"].start_byte <= node.start_byte <= imp["node"].end_byte:
                            imp["namespace"] = node.text.decode("utf8")
                            break

            # Generate ImportRelationship objects
            for imp_data in imports.values():
                if not imp_data["source"]:
                    continue

                items = []
                import_type = "unknown"

                if imp_data["default"]:
                    items.append(imp_data["default"])
                    import_type = "default"

                if imp_data["named"]:
                    items.extend(imp_data["named"])
                    import_type = "named" if not imp_data["default"] else "mixed"

                if imp_data["namespace"]:
                    items.append(f"* as {imp_data['namespace']}")
                    import_type = "namespace"

                yield ImportRelationship(
                    filename=chunk.filename,
                    imported_from=imp_data["source"],
                    imported_items=items,
                    import_type=import_type,
                    line=imp_data["node"].start_point[0] + chunk.start_line
                )

        except Exception as e:
            logger.error(f"Error extracting imports from {chunk.filename}: {e}")

    def extract_custom_metadata(
        self,
        chunk: CodeChunk
    ) -> Dict[str, Any]:
        """Extract TypeScript-specific metadata."""
        metadata = {}

        # Check if it's a React component
        if "React" in chunk.text or "jsx" in chunk.filename.lower():
            if any(pattern in chunk.text for pattern in ["function", "const", "class"]):
                if "return" in chunk.text and "<" in chunk.text:
                    metadata["is_react_component"] = True

        # Check for TypeScript types
        if chunk.filename.endswith((".ts", ".tsx")):
            if "interface " in chunk.text:
                metadata["has_interfaces"] = True
            if "type " in chunk.text:
                metadata["has_type_aliases"] = True
            if "enum " in chunk.text:
                metadata["has_enums"] = True

        # Check for async functions
        if "async " in chunk.text:
            metadata["has_async_functions"] = True

        # Check for test files
        if any(pattern in chunk.filename for pattern in ["test", "spec", "__tests__"]):
            metadata["is_test_file"] = True

        return metadata
