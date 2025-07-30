# CocoIndex Flows Status

## Working Flows ✅

### Basic Flows (No Analyzer)
- `basic` - Minimal example
- `simple` - Multi-language support
- `minimal` - Simplified version
- `flexible` - Uses analyzer for language detection only
- `flexible_no_vector` - No embeddings variant

### Analyzer Flows (Uses TypeScript Analyzer)
- **`analyzer_simple`** - ✅ **WORKING** - Extracts TypeScript metadata correctly

## Broken Flows ❌

- `analyzer_aware` - Type error (dict vs dataclass)
- `analyzer_advanced` - Uses non-existent op.apply()

## Recommended Usage

For TypeScript projects with metadata extraction:
```bash
codesitter index -p /your/project --flow analyzer_simple --postgres
```

For basic indexing without metadata:
```bash
codesitter index -p /your/project --flow flexible --postgres
```
