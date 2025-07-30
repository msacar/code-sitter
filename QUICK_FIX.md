# Quick Fix Commands

Run these commands in order to properly index with analyzer_aware:

```bash
# 1. Force setup (run once)
cocoindex setup --force /Users/mustafaacar/codesitter/src/codesitter/flows/analyzer_aware.py

# 2. Go to your project directory (IMPORTANT!)
cd /Users/mustafaacar/retter/shortlink

# 3. Run update from the project directory
cocoindex update /Users/mustafaacar/codesitter/src/codesitter/flows/analyzer_aware.py

# 4. Verify data was indexed
psql $COCOINDEX_DATABASE_URL -c "SELECT COUNT(*) as chunks FROM analyzerawarecodeindex__code_chunks_with_metadata;"

# 5. Start the server (from project directory)
cocoindex server /Users/mustafaacar/codesitter/src/codesitter/flows/analyzer_aware.py -ci --address 0.0.0.0:3000
```

The key issue is that `codesitter index` command runs from the wrong directory. You need to run `cocoindex update` directly from your project directory.
