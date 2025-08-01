Summary of Our Brainstorming
The Core Insight
Tree-sitter already parses and identifies all structural elements (functions, classes, methods, etc.), but the current analyzer only uses this data internally to determine "caller" context. We're missing out on exposing this rich structural information!
Proposed Solution: Universal Structure Extraction

Universal Patterns that work across languages:

function_declaration, method_definition → Functions
class_declaration, struct_item → Classes/Structs
interface_declaration, trait_item → Interfaces
These patterns are surprisingly consistent across tree-sitter grammars


Language-Specific Enrichment:

TypeScript: Extract parameter types, return types, generics, async status
Python: Extract type hints, decorators, docstrings
Java: Extract annotations, access modifiers, throws clauses
Each language adds its specific flavor on top of the universal structure


Rich Output for each element:
json{
  "type": "function",
  "name": "getUser",
  "async": true,
  "parameters": [{"name": "id", "type": "number"}],
  "return_type": "Promise<User>",
  "exported": true
}


Benefits of This Approach

Multi-language by Default: Add a new language, get basic structure extraction for free
Query-able Structure: Find all async functions, exported classes, methods with specific parameters
Foundation for Advanced Features: Type checking, dependency graphs, refactoring tools
Leverages Tree-sitter's Strengths: We're using what tree-sitter does best - parsing structure

Next Steps to Consider

Should we add extract_structure() to the base LanguageAnalyzer interface?
Or enrich the existing extract_custom_metadata() to return actual elements instead of just booleans?
How to handle the output in the CLI - separate section for structure?
Storage implications - how does this affect indexing and search?

The universal extractor approach gives us maximum information with minimal language-specific code, making it perfect for a multi-language code intelligence system!