"""
# Quick Decision Guide: extract_structure() vs Enriched Metadata

## When to Choose extract_structure() ✅

Choose this if you value:
- **Clean Architecture** - Single Responsibility Principle
- **Type Safety** - Strongly typed ExtractedElement objects
- **Performance** - Only compute what you need
- **Future Extensibility** - Easy to add more extraction methods
- **Clear API** - Obvious what each method does

You should pick this if:
- You're building a long-term, maintainable system
- You have multiple consumers with different needs
- Performance matters (large codebases)
- You want clear separation between flags and structure

## When to Choose Enriched Metadata ✅

Choose this if you value:
- **Simplicity** - No new methods to implement
- **Quick Implementation** - Modify existing code
- **Single Parse** - Everything extracted at once
- **Flexibility** - Easy to add new fields

You should pick this if:
- You need a quick solution
- You always need all the data anyway
- You have few analyzers to update
- Backward compatibility isn't critical

## The Verdict 🎯

### For CodeSitter, I recommend: **extract_structure()**

Why?
1. **You're building a multi-language system** - Clean abstractions matter
2. **Performance is important** - Indexing large codebases
3. **Different use cases** - Some users want structure, others just want calls
4. **Growth potential** - Easy to add extract_types(), extract_dependencies(), etc.
5. **Testing** - Each extraction type can be tested independently

## Implementation Roadmap

### Phase 1: Add the method (1 hour)
```python
# In base.py
def extract_structure(self, chunk: CodeChunk) -> Iterator[ExtractedElement]:
    """Extract structural elements. Override in language analyzers."""
    return []  # Default implementation
```

### Phase 2: Implement for TypeScript (2 hours)
- Integrate UniversalExtractor
- Add TypeScriptExtractor enrichments
- Update tests

### Phase 3: Update CLI (1 hour)
- Add structure section to output
- Handle JSON formatting
- Keep backward compatibility

### Phase 4: Add more languages (ongoing)
- Python: Use ast module patterns
- Java: Use java-specific node types
- Each can be added independently

## Counter-argument Consideration 🤔

**"But enriched metadata is simpler!"**

True, but consider:
- What happens when you need extract_dependencies()?
- What about extract_comments()?
- What about extract_tests()?

With extract_structure(), each is a new method.
With enriched metadata, it becomes a massive, unwieldy dictionary.

## Final Thoughts

The slightly extra complexity of extract_structure() pays dividends in:
- Maintainability
- Performance
- Clarity
- Extensibility

It's the "right" engineering choice for a system meant to grow.
"""
