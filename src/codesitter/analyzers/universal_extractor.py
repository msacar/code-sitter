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
            'lexical_declaration',
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
        'export': [
            'export_statement',
            'export_declaration',
        ]
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
        yield from self._extract_from_node(tree.root_node)

    def _extract_from_node(self, node, depth=0) -> Iterator[ExtractedElement]:
        """Recursively extract elements from a node."""
        # Check if this node matches any pattern
        element = None
        if node.is_named and node.type in self._node_type_to_element:
            element = self._create_element(node)
            if element:
                # Extract children before yielding parent
                for child in node.named_children:
                    child_elements = list(self._extract_from_node(child, depth + 1))
                    element.children.extend(child_elements)
                yield element
                return  # Don't recurse further into this node's children

        # Continue recursion for non-matching nodes
        for child in node.named_children:
            yield from self._extract_from_node(child, depth + 1)

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
                if name_node.type == 'identifier':
                    return name_node.text.decode('utf-8')
                # Recurse to find identifier
                ident = self._find_child_by_type(name_node, 'identifier')
                if ident:
                    return ident.text.decode('utf-8')

        # Try to find any identifier child
        for child in node.named_children:
            if child.type == 'identifier':
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

    def _enrich_element(self, element: ExtractedElement, node):
        """Add TypeScript-specific metadata."""
        if element.element_type == 'function':
            self._enrich_function(element, node)
        elif element.element_type == 'class':
            self._enrich_class(element, node)
        elif element.element_type == 'interface':
            self._enrich_interface(element, node)
        elif element.element_type == 'variable':
            self._enrich_variable(element, node)

    def _enrich_function(self, element: ExtractedElement, node):
        """Extract detailed function information."""
        metadata = element.metadata

        # Check if async
        metadata['async'] = element.text.strip().startswith('async ')

        # Extract parameters
        params = []
        params_node = self._get_field(node, 'parameters')
        if params_node:
            for param in params_node.named_children:
                if param.type in ['required_parameter', 'optional_parameter']:
                    param_info = {
                        'name': self._extract_name(param) or '<unnamed>',
                        'optional': param.type == 'optional_parameter',
                        'type': None,
                        'default': None
                    }

                    # Extract type
                    type_node = self._get_field(param, 'type')
                    if type_node:
                        param_info['type'] = type_node.text.decode('utf-8')

                    # Extract default value
                    value_node = self._get_field(param, 'value')
                    if value_node:
                        param_info['default'] = value_node.text.decode('utf-8')

                    params.append(param_info)

        metadata['parameters'] = params

        # Extract return type
        return_type_node = self._get_field(node, 'return_type')
        if return_type_node:
            # Skip the ':' token
            if return_type_node.named_child_count > 0:
                metadata['return_type'] = return_type_node.named_children[0].text.decode('utf-8')

        # Extract generics
        type_params = self._get_field(node, 'type_parameters')
        if type_params:
            metadata['generics'] = type_params.text.decode('utf-8')

        # Check if it's an arrow function
        if node.type == 'variable_declarator':
            value = self._get_field(node, 'value')
            if value and value.type == 'arrow_function':
                metadata['arrow_function'] = True

        # Check if exported
        parent = node.parent
        if parent and parent.type == 'export_statement':
            metadata['exported'] = True

    def _enrich_class(self, element: ExtractedElement, node):
        """Extract detailed class information."""
        metadata = element.metadata

        # Check if abstract
        if 'abstract' in element.text[:50]:
            metadata['abstract'] = True

        # Extract extends
        heritage = self._get_field(node, 'heritage')
        if heritage:
            extends = self._find_child_by_type(heritage, 'extends_clause')
            if extends:
                metadata['extends'] = extends.text.decode('utf-8').replace('extends', '').strip()

            implements = self._find_child_by_type(heritage, 'implements_clause')
            if implements:
                metadata['implements'] = implements.text.decode('utf-8').replace('implements', '').strip()

        # Extract decorators
        decorators = []
        for child in node.children:
            if child.type == 'decorator':
                decorators.append(child.text.decode('utf-8'))
        if decorators:
            metadata['decorators'] = decorators

        # Check if exported
        parent = node.parent
        if parent and parent.type == 'export_statement':
            metadata['exported'] = True

    def _enrich_interface(self, element: ExtractedElement, node):
        """Extract interface details."""
        metadata = element.metadata

        # Extract extends
        extends_node = self._get_field(node, 'extends')
        if extends_node:
            # Extract interface names from extends_type_clause
            extends_interfaces = []
            for child in extends_node.named_children:
                if child.type in ['type_identifier', 'generic_type']:
                    extends_interfaces.append(child.text.decode('utf-8'))
            metadata['extends'] = extends_interfaces

        # Extract generics
        type_params = self._get_field(node, 'type_parameters')
        if type_params:
            metadata['generics'] = type_params.text.decode('utf-8')

        # Check if exported
        parent = node.parent
        if parent and parent.type == 'export_statement':
            metadata['exported'] = True

    def _enrich_variable(self, element: ExtractedElement, node):
        """Extract variable details."""
        metadata = element.metadata

        # Check const/let/var
        parent = node.parent
        if parent and parent.type == 'lexical_declaration':
            if parent.text.decode('utf-8').strip().startswith('const'):
                metadata['kind'] = 'const'
            elif parent.text.decode('utf-8').strip().startswith('let'):
                metadata['kind'] = 'let'
        elif parent and parent.type == 'variable_declaration':
            metadata['kind'] = 'var'

        # Extract type
        type_node = self._get_field(node, 'type')
        if type_node:
            metadata['type'] = type_node.text.decode('utf-8')

        # Check if it's a function
        value = self._get_field(node, 'value')
        if value:
            if value.type in ['arrow_function', 'function_expression']:
                element.element_type = 'function'
                self._enrich_function(element, node)
