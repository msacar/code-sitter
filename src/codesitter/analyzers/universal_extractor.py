"""Universal structure extractor using tree-sitter."""

from abc import ABC
from typing import Dict, List, Any, Optional, Iterator
import logging

# Import ExtractedElement from base to avoid circular import
from .base import ExtractedElement

logger = logging.getLogger(__name__)


class UniversalExtractor(ABC):
    """Base class for extracting structure from any tree-sitter language."""

    # Universal patterns that work across many languages
    UNIVERSAL_PATTERNS = {
        'function': [
            'function_declaration',
            'function_definition',
            'method_definition',
            'method_declaration',
            'function_item',  # Rust
            'func_literal',   # Go
        ],
        'class': [
            'class_declaration',
            'class_definition',
            'class_specifier',  # C++
            'struct_item',      # Rust
        ],
        'interface': [
            'interface_declaration',
            'trait_item',  # Rust
            'protocol_declaration',  # Swift
        ],
        'variable': [
            'variable_declaration',
            'variable_declarator',
            # Don't include lexical_declaration - it's a container, not the actual variable
            'const_item',  # Rust
            'let_declaration',  # Rust
        ],
        'type': [
            'type_alias_declaration',
            'type_definition',
            'typedef_declaration',
            'type_item',  # Rust
        ],
        'enum': [
            'enum_declaration',
            'enum_item',  # Rust
            'enum_specifier',  # C
        ],
        'import': [
            'import_statement',
            'import_declaration',
            'use_declaration',  # Rust
            'import_spec',  # Go
        ],
        # Note: export_statement is a wrapper/container, not an element itself
        # The actual exported elements (class, function, etc.) are detected
        # and marked as exported via metadata
    }

    def __init__(self, language):
        self.language = language
        # Build reverse mapping for quick lookup
        self._node_type_to_element = {}
        for element_type, patterns in self.UNIVERSAL_PATTERNS.items():
            for pattern in patterns:
                self._node_type_to_element[pattern] = element_type

    def extract_all(self, tree) -> Iterator[ExtractedElement]:
        """Extract all structural elements from the tree."""
        yield from self._extract_from_node(tree.root_node, parent_qualified_name="")

    def _extract_from_node(self, node, parent_qualified_name="", depth=0) -> Iterator[ExtractedElement]:
        """Recursively extract elements from a node."""
        # Check if this node matches any pattern
        element = None
        if node.is_named and node.type in self._node_type_to_element:
            element = self._create_element(node)
            if element:
                # Build qualified name
                if parent_qualified_name:
                    element.qualified_name = f"{parent_qualified_name}.{element.name}"
                else:
                    element.qualified_name = element.name

                # Extract children before yielding parent
                for child in node.named_children:
                    child_elements = list(self._extract_from_node(child, element.qualified_name, depth + 1))
                    element.children.extend(child_elements)
                yield element
                return  # Don't recurse further into this node's children

        # Continue recursion for non-matching nodes
        for child in node.named_children:
            yield from self._extract_from_node(child, parent_qualified_name, depth + 1)

    def _create_element(self, node) -> Optional[ExtractedElement]:
        """Create an ExtractedElement from a node."""
        element_type = self._node_type_to_element.get(node.type)
        if not element_type:
            return None

        # Extract name
        name = self._extract_name(node)
        if not name and element_type != 'variable':  # Variables might be anonymous
            return None

        # Extract all fields
        fields = self._extract_fields(node)

        # Create base element
        element = ExtractedElement(
            element_type=element_type,
            name=name or '<anonymous>',
            node_type=node.type,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            start_byte=node.start_byte,
            end_byte=node.end_byte,
            text=node.text.decode('utf-8'),
            fields=fields,
            metadata={},
            children=[]
        )

        # Language-specific enrichment
        self._enrich_element(element, node)

        return element

    def _extract_name(self, node) -> Optional[str]:
        """Extract the name of an element."""
        # Try common field names
        for field_name in ['name', 'identifier', 'declarator']:
            name_node = self._get_field(node, field_name)
            if name_node:
                # Handle nested identifiers
                if name_node.type in ['identifier', 'type_identifier', 'property_identifier']:
                    return name_node.text.decode('utf-8')
                # Recurse to find identifier
                for id_type in ['identifier', 'type_identifier', 'property_identifier']:
                    ident = self._find_child_by_type(name_node, id_type)
                    if ident:
                        return ident.text.decode('utf-8')

        # Try to find any identifier child
        for child in node.named_children:
            if child.type in ['identifier', 'type_identifier', 'property_identifier']:
                return child.text.decode('utf-8')

        return None

    def _extract_fields(self, node) -> Dict[str, Any]:
        """Extract all fields from a node."""
        fields = {}
        for i, child in enumerate(node.named_children):
            field_name = node.field_name_for_named_child(i)
            if field_name:
                fields[field_name] = {
                    'type': child.type,
                    'text': child.text.decode('utf-8'),
                    'start_line': child.start_point[0] + 1,
                    'end_line': child.end_point[0] + 1
                }
        return fields

    def _get_field(self, node, field_name):
        """Get a named field from a node."""
        for i, child in enumerate(node.named_children):
            if node.field_name_for_named_child(i) == field_name:
                return child
        return None

    def _find_child_by_type(self, node, node_type):
        """Find the first child with the given type."""
        for child in node.named_children:
            if child.type == node_type:
                return child
        return None

    def _enrich_element(self, element: ExtractedElement, node):
        """Override in subclasses to add language-specific enrichment."""
        pass


class TypeScriptExtractor(UniversalExtractor):
    """TypeScript-specific extractor with enriched type information."""

    # Additional TypeScript-specific patterns
    TS_PATTERNS = {
        'type': [
            'type_alias_declaration',
            # interface_declaration should be 'interface', not 'type'
        ],
        'interface': [
            'interface_declaration',
        ],
        'enum': ['enum_declaration'],
        'namespace': ['namespace_declaration', 'module_declaration'],
    }

    def __init__(self, language):
        super().__init__(language)
        # Add TypeScript-specific patterns
        for element_type, patterns in self.TS_PATTERNS.items():
            for pattern in patterns:
                self._node_type_to_element[pattern] = element_type

    def _check_export_status(self, element: ExtractedElement, node):
        """Check if the element is exported (the only thing that requires AST analysis)."""
        parent = node.parent
        if parent:
            if parent.type == 'export_statement':
                element.metadata['exported'] = True
            elif parent.parent and parent.parent.type == 'export_statement':
                element.metadata['exported'] = True

    def _enrich_element(self, element: ExtractedElement, node):
        """Add TypeScript-specific metadata - simplified to only export status."""
        # Only check export status - everything else can be extracted from text by LLMs
        self._check_export_status(element, node)

        # Special case: convert arrow functions to function type
        if element.element_type == 'variable' and node.type == 'variable_declarator':
            value = self._get_field(node, 'value')
            if value and value.type in ['arrow_function', 'function_expression']:
                element.element_type = 'function'
