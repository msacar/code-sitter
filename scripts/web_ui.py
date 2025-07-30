"""
Simple Web UI for Codesitter

Run with: python scripts/web_ui.py
Then open http://localhost:5000
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from flask import Flask, render_template_string, request, jsonify
from codesitter.query import CodeSearchEngine

app = Flask(__name__)
engine = CodeSearchEngine()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Codesitter Search</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .search-box {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        input[type="text"] {
            width: 70%;
            padding: 10px;
            font-size: 16px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        select, button {
            padding: 10px 20px;
            font-size: 16px;
            margin-left: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background: white;
            cursor: pointer;
        }
        button {
            background: #007bff;
            color: white;
            border: none;
        }
        button:hover {
            background: #0056b3;
        }
        .results {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .result-item {
            border-bottom: 1px solid #eee;
            padding: 15px 0;
        }
        .result-item:last-child {
            border-bottom: none;
        }
        .filename {
            font-weight: bold;
            color: #007bff;
            margin-bottom: 5px;
        }
        .code-preview {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 14px;
            white-space: pre-wrap;
            overflow-x: auto;
        }
        .metadata {
            color: #666;
            font-size: 14px;
            margin-top: 5px;
        }
        .loading {
            text-align: center;
            color: #666;
            padding: 20px;
        }
        .error {
            color: #dc3545;
            padding: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <h1>🔍 Codesitter Search</h1>

    <div class="search-box">
        <input type="text" id="query" placeholder="Search your codebase..." autofocus>
        <select id="search-type">
            <option value="semantic">Semantic Search</option>
            <option value="symbol">Symbol Search</option>
            <option value="calls">Function Calls</option>
            <option value="definition">Definitions</option>
        </select>
        <button onclick="search()">Search</button>
    </div>

    <div id="results" class="results" style="display: none;">
        <div id="results-content"></div>
    </div>

    <script>
        function escapeHtml(unsafe) {
            return unsafe
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        async function search() {
            const query = document.getElementById('query').value;
            const searchType = document.getElementById('search-type').value;

            if (!query) return;

            const resultsDiv = document.getElementById('results');
            const resultsContent = document.getElementById('results-content');

            resultsDiv.style.display = 'block';
            resultsContent.innerHTML = '<div class="loading">Searching...</div>';

            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        query: query,
                        type: searchType
                    })
                });

                const data = await response.json();

                if (data.error) {
                    resultsContent.innerHTML = '<div class="error">' + escapeHtml(data.error) + '</div>';
                    return;
                }

                if (data.results.length === 0) {
                    resultsContent.innerHTML = '<div class="loading">No results found</div>';
                    return;
                }

                let html = '<h3>Found ' + data.results.length + ' results:</h3>';

                data.results.forEach(result => {
                    html += '<div class="result-item">';
                    html += '<div class="filename">' + escapeHtml(result.filename) + '</div>';

                    if (result.chunk_text) {
                        html += '<div class="code-preview">' + escapeHtml(result.chunk_text) + '</div>';
                    }

                    if (result.text) {
                        html += '<div class="code-preview">' + escapeHtml(result.text) + '</div>';
                    }

                    if (result.score) {
                        html += '<div class="metadata">Score: ' + result.score.toFixed(3) + '</div>';
                    }

                    if (result.location) {
                        html += '<div class="metadata">Location: lines ' + result.location + '</div>';
                    }

                    if (result.start_line && result.end_line) {
                        html += '<div class="metadata">Lines: ' + result.start_line + '-' + result.end_line + '</div>';
                    }

                    html += '</div>';
                });

                resultsContent.innerHTML = html;

            } catch (error) {
                resultsContent.innerHTML = '<div class="error">Error: ' + escapeHtml(error.message) + '</div>';
            }
        }

        // Search on Enter key
        document.getElementById('query').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                search();
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/search', methods=['POST'])
def api_search():
    try:
        data = request.json
        query = data.get('query', '')
        search_type = data.get('type', 'semantic')

        results = []

        if search_type == 'semantic':
            results = engine.semantic_search(query, k=10)
        elif search_type == 'symbol':
            results = engine.search_symbol(query)
        elif search_type == 'calls':
            results = engine.find_function_calls(query)
        elif search_type == 'definition':
            results = engine.find_definition(query)

        return jsonify({'results': results})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Codesitter Web UI...")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, port=5000)
