#!/bin/bash
# Quick examples of enhanced queries you can run with codesitter + Dossier-like features

echo "=== Enhanced Codesitter API Examples ==="
echo "These queries work with the new detailed analysis flow"
echo ""

# 1. Find a specific function and see its signature
echo "1. Find the 'fetchUserData' function with full signature:"
curl -s -X POST http://0.0.0.0:3000/cocoindex/query \
  -H "Content-Type: application/json" \
  -d '{
    "flow_name": "DetailedCodeAnalysis",
    "target_name": "code_chunks_detailed",
    "filter": {
      "function_signatures": {"$contains": "\"name\": \"fetchUserData\""}
    },
    "limit": 1
  }' | jq '.[] | {file: .filename, functions: (.function_signatures | fromjson)}'

echo ""
echo "2. Find all async functions that return Promises:"
curl -s -X POST http://0.0.0.0:3000/cocoindex/query \
  -H "Content-Type: application/json" \
  -d '{
    "flow_name": "DetailedCodeAnalysis",
    "target_name": "code_chunks_detailed",
    "filter": {
      "function_signatures": {"$contains": "\"isAsync\": true"},
      "function_signatures": {"$contains": "\"returnType\": \"Promise"}
    },
    "limit": 5
  }' | jq '.[] | {file: .filename, functions: (.function_signatures | fromjson | map(select(.isAsync and (.returnType | contains("Promise")))) | map({name, returnType}))}'

echo ""
echo "3. Find exported functions (your public API):"
curl -s -X POST http://0.0.0.0:3000/cocoindex/query \
  -H "Content-Type: application/json" \
  -d '{
    "flow_name": "DetailedCodeAnalysis",
    "target_name": "code_chunks_detailed",
    "filter": {
      "function_signatures": {"$contains": "\"isExport\": true"}
    },
    "limit": 10
  }' | jq '.[] | {file: .filename, exported: (.function_signatures | fromjson | map(select(.isExport)) | map({name, parameters: (.parameters | length), returnType}))}'

echo ""
echo "4. Find functions with more than 3 parameters (complexity indicator):"
curl -s -X POST http://0.0.0.0:3000/cocoindex/query \
  -H "Content-Type: application/json" \
  -d '{
    "flow_name": "DetailedCodeAnalysis",
    "target_name": "code_chunks_detailed",
    "filter": {
      "function_signatures": {"$regex": "\"parameters\":\\s*\\[[^\\]]{50,}"}
    },
    "limit": 5
  }' | jq '.[] | {file: .filename, complex_functions: (.function_signatures | fromjson | map(select(.parameters | length > 3)) | map({name, param_count: (.parameters | length)}))}'

echo ""
echo "5. Semantic search with function context:"
echo "Searching for 'authentication' and showing what functions are in those chunks:"

# First get embedding
EMBEDDING=$(curl -s -X POST http://0.0.0.0:3000/cocoindex/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "user authentication login", "model": "all-MiniLM-L6-v2"}' | jq -r '.embedding')

# Then search
curl -s -X POST http://0.0.0.0:3000/cocoindex/vector_search \
  -H "Content-Type: application/json" \
  -d "{
    \"flow_name\": \"DetailedCodeAnalysis\",
    \"target_name\": \"code_chunks_detailed\",
    \"vector_search\": {
      \"field\": \"embedding\",
      \"vector\": $EMBEDDING,
      \"limit\": 3
    }
  }" | jq '.[] | {file: .filename, similarity: .similarity, functions: (.function_signatures | fromjson | map(.name))}'

echo ""
echo "=== Compare with old boolean approach ==="
echo "Old way - just boolean flags:"
curl -s -X POST http://0.0.0.0:3000/cocoindex/query \
  -H "Content-Type: application/json" \
  -d '{
    "flow_name": "AnalyzerAwareCodeIndex",
    "target_name": "code_chunks_with_metadata",
    "filter": {
      "has_async_functions": true
    },
    "limit": 3
  }' | jq '.[] | {file: .filename, has_async: .has_async_functions}'

echo ""
echo "New way - actual function details!"
echo "Now you can search by function names, parameters, return types, and more."
