# Documentation Updates Summary

## Changes Made

### 1. Removed Unnecessary CLI Options
- Removed `--imports-only` flag from `codesitter analyze file` command
- Removed `--calls-only` flag from `codesitter analyze file` command
- These flags were deemed unnecessary during development stage

### 2. Updated Documentation Files

#### ANALYZER_CLI.md
- Removed references to `--imports-only` and `--calls-only` flags
- Updated example for generating import graphs to use JSON output with jq instead of the removed flag

#### ANALYZER_STANDALONE.md
- Removed the "Extract specific information" section that mentioned the removed flags
- Updated the "Multiple Output Formats" section to remove mention of "Filtered views"
- Updated the "Check Dependencies" example to use JSON output with jq

#### Other Documentation Files
- ANALYZER_DETAILED_USAGE.md - No changes needed (specific to analyzer_detailed flow)
- ENHANCED_ANALYSIS_GUIDE.md - No changes needed (about Dossier-like features)
- PARSER_FIX.md - No changes needed (about tree-sitter API fix)

## Current State

The `codesitter analyze` command now has a simpler interface:
- `codesitter analyze list` - List available analyzers
- `codesitter analyze file <path>` - Analyze a single file
- `codesitter analyze file <path> --json` - JSON output for scripting
- `codesitter analyze directory <path>` - Analyze directory
- `codesitter analyze directory <path> --ext <extension>` - Filter by extension

The output always includes all available information (imports, calls, and metadata) rather than filtering by type.

## Rationale

During the development stage, having separate flags for filtering output types adds unnecessary complexity. Users can achieve the same filtering using standard tools like `jq` when using JSON output, which is more flexible and composable.
