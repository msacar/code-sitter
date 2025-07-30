## Analyzer Aware Flow - Troubleshooting

The issue you're experiencing has two parts:

### 1. Empty Statistics After Indexing

The problem is that the `codesitter` CLI runs the indexing from the wrong directory. It executes:
```bash
cocoindex update --setup /path/to/flow.py
```

But this runs from `/Users/mustafaacar/codesitter`, not from your project directory `/Users/mustafaacar/retter/shortlink`.

### 2. UI Warning About Setup

Even though setup is complete, the UI might be checking for version mismatches or cached state.

## Solution

### Option 1: Run Commands Directly (Recommended)

```bash
# 1. Force setup to ensure everything is synced
cocoindex setup --force /Users/mustafaacar/codesitter/src/codesitter/flows/analyzer_aware.py

# 2. Change to your project directory
cd /Users/mustafaacar/retter/shortlink

# 3. Run update from the correct directory
cocoindex update /Users/mustafaacar/codesitter/src/codesitter/flows/analyzer_aware.py

# 4. Start the server
cocoindex server /Users/mustafaacar/codesitter/src/codesitter/flows/analyzer_aware.py -ci --address 0.0.0.0:3000
```

### Option 2: Use the Fix Script

```bash
# Run the automated fix script
./fix_analyzer_aware.sh
```

### Option 3: Debug First

```bash
# Run debug script to see what's happening
./debug_analyzer_aware.py
```

## Verify Success

After running the update, check if data was indexed:

```sql
psql $COCOINDEX_DATABASE_URL -c "
SELECT
    COUNT(DISTINCT filename) as files,
    COUNT(*) as chunks,
    COUNT(CASE WHEN is_react_component THEN 1 END) as react_components
FROM analyzerawarecodeindex__code_chunks_with_metadata;"
```

You should see non-zero values.

## Why This Happens

1. CocoIndex needs to run from the project directory to find files
2. The `codesitter` CLI currently doesn't change to the project directory before running `cocoindex update`
3. The `--setup` flag might cause the command to focus on setup verification rather than actual indexing

## API Endpoints After Fix

Once properly indexed, these API calls will work:

```bash
# Search for React components
curl -X POST http://localhost:3000/cocoindex/query \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {
      "is_react_component": true
    },
    "limit": 10
  }'

# Get statistics
curl -X GET http://localhost:3000/cocoindex/stats
```
