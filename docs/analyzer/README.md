# Analyzer Documentation

This directory contains documentation for codesitter's code analysis features.

## Core Documentation

- **[ANALYZER_CLI.md](ANALYZER_CLI.md)** - How to use the `codesitter analyze` command
- **[ANALYZER_STANDALONE.md](ANALYZER_STANDALONE.md)** - Using analyzers without indexing
- **[DOCUMENTATION_UPDATES.md](DOCUMENTATION_UPDATES.md)** - Recent changes to the analyzer CLI

## Advanced Features

- **[ANALYZER_DETAILED_USAGE.md](ANALYZER_DETAILED_USAGE.md)** - Using the detailed analyzer flow
- **[ENHANCED_ANALYSIS_GUIDE.md](ENHANCED_ANALYSIS_GUIDE.md)** - Dossier-like features for rich code analysis
- **[PARSER_FIX.md](PARSER_FIX.md)** - Troubleshooting tree-sitter parser issues

## Future Development

- **[FUTURE_UNIVERSAL_EXTRACTION.md](FUTURE_UNIVERSAL_EXTRACTION.md)** - Proposed universal structure extraction

## Quick Start

```bash
# List available analyzers
codesitter analyze list

# Analyze a single file
codesitter analyze file src/main.ts

# Get JSON output for automation
codesitter analyze file src/main.ts --json

# Analyze entire directory
codesitter analyze directory ./src --ext .ts
```

## Current Capabilities

- Extract function calls and relationships
- Identify imports and dependencies
- Detect language-specific patterns (React components, async functions, etc.)
- Support for 20+ programming languages
- JSON output for scripting and automation

## Upcoming Features

- Universal structure extraction (functions, classes, interfaces)
- Rich type information and signatures
- Cross-file type resolution
- Enhanced query capabilities
