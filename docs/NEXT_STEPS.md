## Summary

Out of the box, CocoIndex’s built‑in TypeScript parser will split your `.ts` and `.tsx` files into syntactic “chunks” (e.g. functions, classes, blocks) and index their raw text for search or embedding, but it does **not** automatically record structured call‑site relationships (i.e., which function calls which with what arguments). You can still full‑text–search for occurrences like `y(` in the indexed chunks, but to see precise “function x calls y with argument z” data, you’ll need to plug in a custom Tree‑sitter query via a Python operator in your flow.

---

## 1. What CocoIndex’s Built‑In Parser Does

* **Syntactic chunking only**
  CocoIndex leverages Tree‑sitter under the hood to break files into semantic chunks—functions, classes, imports, etc.—and indexes each chunk’s text, filename, and positional metadata for rapid retrieval ([CocoIndex][1]).
* **No AST metadata in chunks**
  The default chunk objects do *not* include detailed AST nodes or call‐graph edges; they only carry the raw source text and context for vector or text search ([CocoIndex][2]).

---

## 2. Why You Can’t Directly “See” Call Sites

* **Lack of structured capture**
  CocoIndex’s Python SDK doesn’t expose individual AST captures like `call_expression` by default—it treats each chunk as opaque text for embedding or full‑text lookup.
* **Text search workaround**
  You could search chunks for the literal `y(` pattern to find likely call sites, but this is essentially regex/text matching, not a guaranteed AST‑aware extraction.

---

## 3. Extracting Call Relationships Yourself

1. **Use Python Tree‑Sitter Bindings**
   Install and import the `py-tree-sitter` package to get AST access in Python ([GitHub][3]):

   ```bash
   pip install tree-sitter
   ```

2. **Write a `call_expression` Query**
   For example, to capture callees and their first argument identifiers:

   ````scheme
   (call_expression
     function: (identifier)   @callee      ; the called function’s name
     arguments: (arguments
       (identifier)           @arg          ; first argument
     )
   )
   ``` :contentReference[oaicite:3]{index=3}

   ````

3. **Embed the Query as a Custom Operator**
   In your CocoIndex flow, register a Python transform that:

   * Parses each chunk’s `text` into a Tree‑sitter tree
   * Runs your `call_expression` query
   * Emits records `{ caller, callee, arg, file, position }` into your chosen sink

4. **Index and Retrieve**
   Send those records to PostgreSQL (or another store) so you can run structured SQL queries like:

   ```sql
   SELECT * FROM call_edges
    WHERE caller = 'y';
   ```

   giving you the exact calls made *by* `y`, along with their arguments.

---

## 4. Conclusion

CocoIndex’s built‑in TS parser excels at real‑time, syntax‑aware chunking and vector/text indexing, but it does not itself track call‑graph details. To “see” when function `y` calls other functions (and with what parameters), you’ll need to augment your Python flow with a small Tree‑sitter–based extract operator that specifically captures those `call_expression` nodes.

[1]: https://cocoindex.io/blogs/index-code-base-for-rag/?utm_source=chatgpt.com "Build Real-Time Codebase Indexing for AI Code Generation"
[2]: https://cocoindex.io/docs/?utm_source=chatgpt.com "Overview | CocoIndex"
[3]: https://github.com/tree-sitter/py-tree-sitter?utm_source=chatgpt.com "Python bindings to the Tree-sitter parsing library - GitHub"


## WHAT we need to do To capture call-site relationships Summary

To capture call-site relationships in your TypeScript code, you can write a custom Python operator in your CocoIndex flow using the `py-tree-sitter` bindings for Tree‑sitter ([Wikipedia][1]). This operator will parse each code chunk into a concrete syntax tree, run a query targeting `call_expression` nodes, and emit structured records of the function calls and their arguments ([volito.digital][2]). By registering this operator via `cocoindex.op.function()` (or the `FunctionSpec`/executor pattern), you seamlessly integrate AST‑based extraction into CocoIndex’s incremental pipeline ([CocoIndex][3]). The resulting call data can then be sunk into your chosen target (e.g. PostgreSQL or a vector store) for precise lookup of which functions invoke a given function and with what parameters ([cocoindexio.substack.com][4]).

---

## 1. Install Required Packages

1. First, install the core Tree‑sitter Python bindings:

   ```bash
   pip install tree-sitter
   ```

   ([GitHub][5])
2. Install the TypeScript and TSX grammars for Tree‑sitter:

   ```bash
   pip install tree-sitter-typescript
   ```

   ([PyPI][6])
3. Ensure your environment uses Python 3.11–3.13, as required by the CocoIndex SDK:

   ```bash
   pip install cocoindex
   ```

---

## 2. Load the TypeScript Grammar and Parser

1. In your Python script, import the Tree‑sitter API and the language pack:

   ```python
   from tree_sitter import Language, Parser
   from tree_sitter_language_pack import get_language
   ```

   ([GitHub][5], [PyPI][6])
2. Load the grammar and initialize the parser:

   ```python
   TS_LANGUAGE = get_language("typescript")
   parser = Parser()
   parser.set_language(TS_LANGUAGE)
   ```

---

## 3. Write a Call‑Expression Query

1. Define a Tree‑sitter query that matches function definitions containing call expressions, capturing the callee name and its first argument:

   ```scheme
   (
     (function_declaration
       name: (identifier)         @caller
       body: (statement_block
         (call_expression
           function: (identifier) @callee
           arguments: (arguments (identifier) @arg)
         ) @site
       )
     )
   )
   ```

   ([Stack Overflow][7], [Cycode][8])

---

## 4. Parse and Capture in a Custom Operator

1. Use the CocoIndex SDK to register a custom function:

   ```python
   import cocoindex.op as op

   @op.function()
   def extract_calls(text: str, filename: str):
       # Will be implemented below
       ...
   ```

   ([CocoIndex][3])
2. Inside `extract_calls`, parse the chunk and run the query:

   ```python
   from tree_sitter import Query

   parser = Parser()
   parser.set_language(TS_LANGUAGE)
   tree = parser.parse(bytes(text, "utf8"))

   query = Query(TS_LANGUAGE, YOUR_QUERY_STRING)
   captures = query.captures(tree.root_node)
   ```

   ([GitHub][5], [GitHub][9])
3. Iterate over `captures` and yield structured records:

   ```python
   caller, callee, arg = None, None, None
   for name, node in captures:
       if name == "caller":
           caller = node.text.decode("utf8")
       elif name == "callee":
           callee = node.text.decode("utf8")
       elif name == "arg":
           arg = node.text.decode("utf8")
       elif name == "site":
           yield {
               "filename": filename,
               "caller": caller,
               "callee": callee,
               "arg": arg,
               "line": node.start_point[0] + 1,
               "column": node.start_point[1] + 1,
           }
   ```

   ([volito.digital][2])

---

## 5. Register the Operator and Run Your Flow

1. In your `FlowBuilder`, chain the transform on your `chunks.text` field and add a sink:

   ```python
   flow = FlowBuilder("CodeCalls")
   files = flow.add_source(sources.LocalFile(path=".", included_patterns=["*.ts", "*.tsx"]))
   files["calls"] = files["text"].transform(extract_calls)
   flow.add_sink(flow.sinks.Postgres(table_name="call_sites"))
   ```

   ([GitHub][10])
2. Execute the flow to index calls incrementally:

   ```bash
   cocoindex update code_calls_flow.py
   cocoindex server code_calls_flow.py
   ```

   ([CocoIndex][11])

With these steps, each time you query function `y` in your database, you’ll retrieve exactly the call sites made by `y`—including the specific arguments passed—powered by Tree‑sitter’s precise CST queries integrated into CocoIndex’s pipeline.

[1]: https://en.wikipedia.org/wiki/Tree-sitter_%28parser_generator%29?utm_source=chatgpt.com "Tree-sitter (parser generator)"
[2]: https://volito.digital/using-the-tree-sitter-library-in-python-to-build-a-custom-tool-for-parsing-source-code-and-extracting-call-graphs/?utm_source=chatgpt.com "Using The Tree-Sitter Library In Python To Build A Custom Tool For ..."
[3]: https://cocoindex.io/docs/core/custom_function?utm_source=chatgpt.com "Custom Functions | CocoIndex"
[4]: https://cocoindexio.substack.com/p/index-codebase-with-tree-sitter-and?utm_source=chatgpt.com "Index codebase with Tree-sitter and Cocoindex for RAG and ..."
[5]: https://github.com/tree-sitter/py-tree-sitter?utm_source=chatgpt.com "Python bindings to the Tree-sitter parsing library - GitHub"
[6]: https://pypi.org/project/tree-sitter-typescript/?utm_source=chatgpt.com "tree-sitter-typescript - PyPI"
[7]: https://stackoverflow.com/questions/70267465/how-do-i-extract-the-first-argument-from-a-function-in-tree-sitter?utm_source=chatgpt.com "How do I extract the first argument from a function in tree-sitter"
[8]: https://cycode.com/blog/tips-for-using-tree-sitter-queries/?utm_source=chatgpt.com "Tips for using tree sitter queries - Cycode"
[9]: https://github.com/tree-sitter/py-tree-sitter/blob/master/examples/usage.py?utm_source=chatgpt.com "py-tree-sitter/examples/usage.py at master - GitHub"
[10]: https://github.com/cocoindex-io/cocoindex?utm_source=chatgpt.com "cocoindex-io/cocoindex: Data transformation framework for AI. Ultra ..."
[11]: https://cocoindex.io/docs/core/flow_methods?utm_source=chatgpt.com "Run a CocoIndex Flow"
