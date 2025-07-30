## Quick Fix - One Command

You already have the `.env` file with correct settings. Just run this complete command:

```bash
cd /Users/mustafaacar/codesitter && \
source .env && \
cd /Users/mustafaacar/retter/shortlink && \
cocoindex setup --force /Users/mustafaacar/codesitter/src/codesitter/flows/analyzer_aware.py && \
cocoindex update /Users/mustafaacar/codesitter/src/codesitter/flows/analyzer_aware.py && \
psql $COCOINDEX_DATABASE_URL -t -c "SELECT 'Indexed chunks:', COUNT(*) FROM analyzerawarecodeindex__code_chunks_with_metadata;"
```

## Or Use the Complete Fix Script

```bash
cd /Users/mustafaacar/codesitter
./complete_fix_analyzer_aware.sh
```

This script:
1. Loads your .env file
2. Tests database connection
3. Runs setup and indexing from the correct directory
4. Verifies the data was indexed
5. Shows you how to start the server

## Start the Server After Indexing

```bash
cd /Users/mustafaacar/retter/shortlink
source /Users/mustafaacar/codesitter/.env
cocoindex server /Users/mustafaacar/codesitter/src/codesitter/flows/analyzer_aware.py -ci --address 0.0.0.0:3000
```

## Test API Endpoints

```bash
# Get stats
curl -X GET http://localhost:3000/cocoindex/stats

# Find React components
curl -X POST http://localhost:3000/cocoindex/query \
  -H "Content-Type: application/json" \
  -d '{"filter":{"is_react_component":true},"limit":5}'
```
