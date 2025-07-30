# CocoIndex Integration - Correct Implementation

## What Was Wrong

After carefully reviewing the CocoIndex documentation and examples, I found several issues with my initial implementation:

1. **`op.apply()` doesn't exist** - This method is not part of CocoIndex API
2. **Dict vs Dataclass confusion** - CocoIndex requires proper types, not plain dicts for KTable values
3. **Overly complex flows** - Tried to do too much in intermediate steps

## The Correct Pattern (from examples)

Looking at `examples/code_embedding/main.py`:

```python
@cocoindex.op.function()
def extract_extension(filename: str) -> str:
    return os.path.splitext(filename)[1]

@cocoindex.transform_flow()
def code_to_embedding(text: DataSlice[str]) -> DataSlice[Vector[float, Literal[384]]]:
    return text.transform(functions.SentenceTransformerEmbed(...))

# In the flow:
chunk["embedding"] = chunk["text"].call(code_to_embedding)
chunk["extension"] = file["filename"].transform(extract_extension)
```

Key patterns:
- Use `@op.function()` for simple transformations
- Use `@transform_flow()` for reusable transformation flows
- Use `.transform()` with functions, `.call()` with transform flows
- Keep intermediate steps minimal

## Working Implementation: analyzer_simple

The `analyzer_simple` flow now correctly:

1. Uses individual `@op.function()` decorated functions for each metadata check
2. Transforms data directly without complex intermediate structures
3. Follows the exact pattern from CocoIndex examples

### Setup and Usage

```bash
# Setup
export USE_POSTGRES=true
export COCOINDEX_DATABASE_URL="postgresql://user:pass@localhost:5432/db"

cocoindex setup /path/to/codesitter/src/codesitter/flows/analyzer_simple.py

# Index your project
cd /your/typescript/project
codesitter index -p . --flow analyzer_simple --postgres
```

### What Gets Analyzed

Creates table: `code_analysis` with columns:
- filename, location, code, embedding, language
- is_react_component, has_interfaces, has_type_aliases
- has_async_functions, is_test_file

### Query Examples

```sql
-- Find React components
SELECT filename, code
FROM code_analysis
WHERE is_react_component = true;

-- Find TypeScript interfaces
SELECT filename, code
FROM code_analysis
WHERE has_interfaces = true;

-- Semantic search
SELECT filename, code,
       1 - (embedding <=> query_embedding) as similarity
FROM code_analysis
ORDER BY embedding <=> query_embedding
LIMIT 10;
```

## Lessons Learned

1. **Follow examples exactly** - CocoIndex has specific patterns that must be followed
2. **Keep it simple** - Don't create complex intermediate data structures
3. **Use proper decorators** - `@op.function()` for transforms, `@transform_flow()` for reusable flows
4. **No op.apply()** - This method doesn't exist, use `.transform()` instead

## Flow Comparison

| Flow | Status | Issue | Use Instead |
|------|--------|-------|-------------|
| flexible | ✓ Works | Only uses analyzer for language detection | - |
| analyzer_aware | ✗ Broken | Dict/dataclass type errors | analyzer_simple |
| analyzer_advanced | ✗ Broken | Uses non-existent op.apply() | analyzer_simple |
| **analyzer_simple** | ✓ Works | Fixed all issues | **Use this!** |

The `analyzer_simple` flow is the correct implementation that properly uses your TypeScript analyzer to extract metadata while following CocoIndex's patterns.
