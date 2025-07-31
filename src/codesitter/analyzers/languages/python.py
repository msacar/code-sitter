"""Python language analyzer."""

from typing import Iterator, List, Dict, Any
import logging

from tree_sitter import Language, Parser, Query
from tree_sitter_language_pack import get_language

from ..base import LanguageAnalyzer, CodeChunk, CallRelationship, ImportRelationship
from ..parser_utils import create_parser, query_captures

logger = logging.getLogger(__name__)


class PythonAnalyzer(LanguageAnalyzer):
    """
    Analyzer for Python files.

    Extracts:
    - Function call relationships
    - Import statements
    - Class inheritance
    - Decorators
    """

    def __init__(self):
        # Initialize Tree-sitter for Python using language pack
        self._language = get_language("python")

        # Define queries
        self._call_query = """
        (call
          function: [
            (identifier) @callee
            (attribute
              attribute: (identifier) @callee
            )
          ]
          arguments: (argument_list) @args
        ) @call
        """

        self._import_query = """
        (import_statement
          name: (dotted_name) @module
        ) @import

        (import_from_statement
          module_name: (dotted_name) @module
          name: [
            (dotted_name) @item
            (aliased_import
              name: (dotted_name) @item
              alias: (identifier) @alias
            )
          ]
        ) @from_import

        (import_from_statement
          module_name: (dotted_name) @module
          (import_prefix) @star
        ) @star_import
        """

        self._function_query = """
        (function_definition
          name: (identifier) @function_name
        ) @function

        (class_definition
          name: (identifier) @class_name
          body: (block
            (function_definition
              name: (identifier) @method_name
            ) @method
          )
        ) @class
        """

        self._decorator_query = """
        (decorated_definition
          (decorator
            (identifier) @decorator_name
          )
        ) @decorated

        (decorated_definition
          (decorator
            (call
              function: (identifier) @decorator_func
            )
          )
        ) @decorated_call
        """

    @property
    def supported_extensions(self) -> List[str]:
        return [".py", ".pyw"]

    @property
    def language_name(self) -> str:
        return "python"

    def extract_call_relationships(
        self,
        chunk: CodeChunk
    ) -> Iterator[CallRelationship]:
        """Extract function calls from Python code."""
        parser = create_parser(self._language)

        try:
            tree = parser.parse(bytes(chunk.text, "utf8"))
            # Use language.query() instead of Query() constructor
            query = self._language.query(self._call_query)
            captures = query.captures(tree.root_node)

            # Find containing function/method for context
            func_query = self._language.query(self._function_query)
            func_captures = func_query.captures(tree.root_node)

            # Build a map of byte ranges to function names
            func_ranges = {}
            current_class = None

            for name, node in func_captures:
                if name == "class_name":
                    current_class = node.text.decode("utf8")
                elif name == "function_name":
                    func_name = node.text.decode("utf8")
                    func_ranges[(node.parent.start_byte, node.parent.end_byte)] = func_name
                elif name == "method_name" and current_class:
                    method_name = node.text.decode("utf8")
                    func_ranges[(node.parent.start_byte, node.parent.end_byte)] = f"{current_class}.{method_name}"

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
                        caller = "module_level"
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
                                # Split by comma (simplified - doesn't handle nested commas)
                                parts = args_content.split(",")
                                for part in parts:
                                    arg = part.strip()
                                    # Remove keyword argument names
                                    if "=" in arg:
                                        arg = arg.split("=")[0].strip()
                                    args.append(arg)

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
        """Extract import statements from Python code."""
        parser = create_parser(self._language)

        try:
            tree = parser.parse(bytes(chunk.text, "utf8"))
            # Use language.query() instead of Query() constructor
            query = self._language.query(self._import_query)
            captures = query.captures(tree.root_node)

            # Process imports
            current_import = None

            for name, node in captures:
                if name == "import":
                    # Simple import statement
                    module_node = None
                    for child_name, child_node in captures:
                        if child_name == "module" and child_node.start_byte >= node.start_byte and child_node.end_byte <= node.end_byte:
                            module_node = child_node
                            break

                    if module_node:
                        module_name = module_node.text.decode("utf8")
                        yield ImportRelationship(
                            filename=chunk.filename,
                            imported_from=module_name,
                            imported_items=[module_name],
                            import_type="module",
                            line=node.start_point[0] + chunk.start_line
                        )

                elif name == "from_import":
                    # from ... import ... statement
                    module_name = None
                    items = []

                    for child_name, child_node in captures:
                        if child_node.start_byte >= node.start_byte and child_node.end_byte <= node.end_byte:
                            if child_name == "module":
                                module_name = child_node.text.decode("utf8")
                            elif child_name == "item":
                                items.append(child_node.text.decode("utf8"))
                            elif child_name == "alias":
                                # Handle aliased imports
                                if items:
                                    items[-1] = f"{items[-1]} as {child_node.text.decode('utf8')}"

                    if module_name:
                        yield ImportRelationship(
                            filename=chunk.filename,
                            imported_from=module_name,
                            imported_items=items,
                            import_type="from_import",
                            line=node.start_point[0] + chunk.start_line
                        )

                elif name == "star_import":
                    # from ... import * statement
                    module_name = None
                    for child_name, child_node in captures:
                        if child_name == "module" and child_node.start_byte >= node.start_byte and child_node.end_byte <= node.end_byte:
                            module_name = child_node.text.decode("utf8")
                            break

                    if module_name:
                        yield ImportRelationship(
                            filename=chunk.filename,
                            imported_from=module_name,
                            imported_items=["*"],
                            import_type="star_import",
                            line=node.start_point[0] + chunk.start_line
                        )

        except Exception as e:
            logger.error(f"Error extracting imports from {chunk.filename}: {e}")

    def extract_custom_metadata(
        self,
        chunk: CodeChunk
    ) -> Dict[str, Any]:
        """Extract Python-specific metadata."""
        metadata = {}
        parser = create_parser(self._language)

        try:
            tree = parser.parse(bytes(chunk.text, "utf8"))

            # Check for decorators
            dec_query = Query(self._language, self._decorator_query)
            dec_captures = dec_query.captures(tree.root_node)

            decorators = set()
            for name, node in dec_captures:
                if name in ["decorator_name", "decorator_func"]:
                    decorators.add(node.text.decode("utf8"))

            if decorators:
                metadata["decorators"] = list(decorators)

            # Check for common patterns
            if "@property" in decorators:
                metadata["has_properties"] = True

            if any(d in decorators for d in ["@staticmethod", "@classmethod"]):
                metadata["has_special_methods"] = True

            # Check for async functions
            if "async def" in chunk.text:
                metadata["has_async_functions"] = True

            # Check for type hints
            if "->" in chunk.text or ": " in chunk.text:
                metadata["has_type_hints"] = True

            # Check for docstrings
            if '"""' in chunk.text or "'''" in chunk.text:
                metadata["has_docstrings"] = True

            # Check for test functions
            if any(pattern in chunk.text for pattern in ["def test_", "def Test", "pytest", "unittest"]):
                metadata["has_tests"] = True

            # Check for class definitions
            if "class " in chunk.text:
                metadata["has_classes"] = True

        except Exception as e:
            logger.error(f"Error extracting metadata from {chunk.filename}: {e}")

        return metadata

    def should_analyze_chunk(self, chunk: CodeChunk) -> bool:
        """Filter out chunks that don't need analysis."""
        # Skip chunks that are mostly comments or docstrings
        lines = chunk.text.strip().split('\n')
        code_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]

        # If less than 20% of lines are actual code, skip
        if len(lines) > 0 and len(code_lines) / len(lines) < 0.2:
            return False

        return True
