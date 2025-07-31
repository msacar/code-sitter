#!/usr/bin/env python3
"""
Quick start guide for using smart chunking in your project.
"""

print("""
🚀 SMART CHUNKING QUICK START
============================

Smart chunking solves the context problem in code analysis by creating
intelligent, self-contained chunks instead of arbitrary text splits.

STEP 1: Test with example code
------------------------------
python test_smart_chunking.py

STEP 2: Compare with traditional chunking
-----------------------------------------
python compare_chunking.py

STEP 3: Index your project with smart chunking
----------------------------------------------
# Option A: Direct flow execution
cd /your/project
python -c "from codesitter.flows.smart_chunking import flow; flow.update()"

# Option B: Using cocoindex CLI
cocoindex update /path/to/codesitter/src/codesitter/flows/smart_chunking.py

# Option C: With PostgreSQL
export USE_POSTGRES=true
export COCOINDEX_DATABASE_URL="postgresql://user:pass@localhost:5432/db"
cocoindex setup /path/to/codesitter/src/codesitter/flows/smart_chunking.py
cocoindex update /path/to/codesitter/src/codesitter/flows/smart_chunking.py

STEP 4: Query your smart chunks
-------------------------------
# If using PostgreSQL:
psql $COCOINDEX_DATABASE_URL -c "
    SELECT chunk_id, chunk_type, metadata
    FROM smart_chunks
    WHERE chunk_type = 'function'
    LIMIT 10;
"

# If using JSON:
python -c "
import json
with open('smart_chunks_index.json') as f:
    chunks = json.load(f)
    functions = [c for c in chunks if c['chunk_type'] == 'function']
    for func in functions[:5]:
        print(f\"{func['chunk_id']}: {func['metadata']}\")
"

STEP 5: Use in your own code
-----------------------------
from codesitter.chunkers import SmartChunker

# Initialize
chunker = SmartChunker()

# Chunk a file
with open('myfile.ts') as f:
    content = f.read()

chunks = chunker.chunk_file('myfile.ts', content)

# Process chunks
for chunk in chunks:
    print(f"Type: {chunk.chunk_type}")
    print(f"ID: {chunk.chunk_id}")
    print(f"Has imports: {len(chunk.file_imports)}")
    print(f"Metadata: {chunk.metadata}")
    print("---")

BENEFITS
--------
✅ Complete functions, never split
✅ Import context preserved
✅ Better incremental indexing
✅ Richer metadata for analysis
✅ Stable chunk IDs

NEXT STEPS
----------
1. Read docs/SMART_CHUNKING.md for details
2. Extend to more languages (see analyzers/)
3. Build advanced queries using metadata
4. Contribute improvements!

Happy chunking! 🎉
""")
