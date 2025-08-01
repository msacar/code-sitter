"""
Proposed Universal Structure Extraction Design

Based on tree-sitter's node types, here's a comprehensive extraction system:

## Universal Node Patterns (work across many languages):

### DECLARATION PATTERNS:
- function_declaration
- class_declaration
- method_definition
- variable_declaration / variable_declarator
- interface_declaration (TS, Java, etc.)
- enum_declaration
- module_declaration

### COMMON FIELDS (available via node.field_name_for_child):
- name: The identifier of the declaration
- parameters: Function/method parameters
- body: The implementation
- type: Type annotations
- value: Initial values

## Language-Specific Enrichments:

### TypeScript Specific Node Types:
- type_alias_declaration (type Foo = ...)
- interface_declaration
- enum_declaration
- namespace_declaration
- ambient_declaration (declare ...)
- decorator (@ annotations)
- type_parameter (generics <T>)
- type_annotation (: Type)
- as_expression (type assertions)
- satisfies_expression
- readonly_type
- optional_parameter
- rest_parameter

### TypeScript Type Nodes:
- union_type (A | B)
- intersection_type (A & B)
- generic_type (Array<T>)
- function_type (() => void)
- object_type ({ x: number })
- literal_type ("foo" | 123)
- template_literal_type
- conditional_type (T extends U ? X : Y)
- infer_type
- type_predicate (x is Type)

## Proposed Implementation:

class UniversalExtractor:
    '''Base extractor using universal patterns'''

    UNIVERSAL_PATTERNS = {
        'functions': ['function_declaration', 'method_definition', 'arrow_function'],
        'classes': ['class_declaration', 'class_expression'],
        'interfaces': ['interface_declaration'],
        'variables': ['variable_declaration', 'variable_declarator', 'lexical_declaration'],
        'imports': ['import_statement', 'import_declaration'],
        'exports': ['export_statement', 'export_declaration'],
    }

    def extract_element(self, node):
        '''Extract common fields that exist across languages'''
        element = {
            'type': node.type,
            'name': self.get_name(node),
            'range': {
                'start_line': node.start_point[0],
                'end_line': node.end_point[0],
                'start_byte': node.start_byte,
                'end_byte': node.end_byte
            },
            'text': node.text.decode('utf-8'),
            'fields': {}
        }

        # Extract all available fields
        for i, child in enumerate(node.named_children):
            field_name = node.field_name_for_named_child(i)
            if field_name:
                element['fields'][field_name] = {
                    'type': child.type,
                    'text': child.text.decode('utf-8')
                }

        return element

class TypeScriptEnricher(UniversalExtractor):
    '''Add TypeScript-specific extraction'''

    TS_SPECIFIC_PATTERNS = {
        'types': ['type_alias_declaration', 'type_parameter'],
        'enums': ['enum_declaration'],
        'namespaces': ['namespace_declaration', 'module_declaration'],
        'decorators': ['decorator'],
    }

    def enrich_function(self, element, node):
        '''Add TypeScript-specific function details'''
        # Extract parameter types
        params = []
        param_list = self.find_child_by_type(node, 'formal_parameters')
        if param_list:
            for param in param_list.named_children:
                param_info = {
                    'name': self.get_name(param),
                    'optional': self.find_child_by_type(param, 'optional_parameter') is not None,
                    'type': None,
                    'default': None
                }

                # Get type annotation
                type_ann = self.find_child_by_field(param, 'type')
                if type_ann:
                    param_info['type'] = type_ann.text.decode('utf-8')

                # Get default value
                default = self.find_child_by_field(param, 'value')
                if default:
                    param_info['default'] = default.text.decode('utf-8')

                params.append(param_info)

        element['parameters'] = params

        # Extract return type
        return_type = self.find_child_by_field(node, 'return_type')
        if return_type:
            element['return_type'] = return_type.text.decode('utf-8')

        # Check if async
        element['async'] = node.text.decode('utf-8').strip().startswith('async ')

        # Extract generics
        type_params = self.find_child_by_type(node, 'type_parameters')
        if type_params:
            element['generics'] = type_params.text.decode('utf-8')

        return element

## Benefits:

1. **Maximum Detail**: Extracts all available information from the AST
2. **Language Agnostic Core**: Universal patterns work for Python, JavaScript, Java, Go, etc.
3. **Progressive Enhancement**: Start with universal, add language-specific features
4. **Type-Aware**: Full type information for TypeScript/Java/etc.
5. **Extensible**: Easy to add new languages or patterns

## Example Output:

{
    "type": "function_declaration",
    "name": "getUser",
    "async": true,
    "generics": "<T extends User>",
    "parameters": [
        {
            "name": "id",
            "type": "number",
            "optional": false,
            "default": null
        },
        {
            "name": "options",
            "type": "FetchOptions",
            "optional": true,
            "default": "{}"
        }
    ],
    "return_type": "Promise<T | null>",
    "decorators": ["@cache", "@log"],
    "range": {
        "start_line": 10,
        "end_line": 15
    }
}
"""
