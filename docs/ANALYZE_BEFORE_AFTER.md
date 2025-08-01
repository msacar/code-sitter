# Before and After: analyze Command Output

## Before (Without extract_structure)

```
Analysis: test_structure.ts
Language: typescript | Analyzer: TypeScriptAnalyzer
================================================================================

📦 Imports (2):
  react → useState, useEffect (line 2)
  ./types → User (line 3)

📞 Function Calls (5):
  getUser → fetch(`/api/users/${id}`) at line 19
  getUser → response.json() at line 20
  addUser → this.users.push(user) at line 33
  addUser → this.db.save(user) at line 34
  findUser → this.users.find(callback) at line 38

📊 Metadata:
  has_interfaces: ✓
  has_type_aliases: ✓
  has_enums: ✓
  has_async_functions: ✓
  is_test_file: ✗
```

## After (With extract_structure)

```
Analysis: test_structure.ts
Language: typescript | Analyzer: TypeScriptAnalyzer
================================================================================

📦 Imports (2):
  react → useState, useEffect (line 2)
  ./types → User (line 3)

🏗️  Structure (7 elements):
  📘 Interface: User (lines 5-9)
     exported
  📐 Type: UserRole (line 11)
     exported
  🎯 Enum: Status (lines 13-16)
  🔧 Function: getUser (lines 18-21)
     async | exported
     Parameters: (id: number)
     Returns: Promise<User | null>
  🔧 Function: validateUser (lines 23-25)
     arrow function | exported
     Parameters: (user: User)
     Returns: boolean
  🏛️ Class: UserService (lines 27-40)
     Children: 3 elements
       - function: constructor
       - function: addUser
       - function: findUser
  🔧 Function: map (lines 43-45)
     Parameters: (items: T[], fn: (item: T) => U)
     Returns: U[]

📞 Function Calls (5):
  getUser → fetch(`/api/users/${id}`) at line 19
  getUser → response.json() at line 20
  addUser → this.users.push(user) at line 33
  addUser → this.db.save(user) at line 34
  findUser → this.users.find(callback) at line 38

📊 Metadata:
  has_interfaces: ✓
  has_type_aliases: ✓
  has_enums: ✓
  has_async_functions: ✓
  is_test_file: ✗
```

## Key Improvements

1. **Complete Code Structure**: Now we see ALL functions, classes, interfaces, types, and enums - not just boolean flags

2. **Rich Details**:
   - Function parameters with types
   - Return types
   - Async/export status
   - Class methods

3. **Hierarchical View**: Classes show their child methods

4. **Type Information**: Full TypeScript type annotations are preserved

5. **Visual Organization**: Icons help quickly identify different element types

## JSON Output Comparison

### Before
```json
{
  "metadata": {
    "has_interfaces": true,
    "has_type_aliases": true,
    "has_async_functions": true
  }
}
```

### After
```json
{
  "structure": [
    {
      "type": "interface",
      "name": "User",
      "lines": "5-9",
      "metadata": {
        "exported": true
      }
    },
    {
      "type": "function",
      "name": "getUser",
      "lines": "18-21",
      "metadata": {
        "async": true,
        "exported": true,
        "parameters": [
          {
            "name": "id",
            "type": "number",
            "optional": false
          }
        ],
        "return_type": "Promise<User | null>"
      }
    }
    // ... more elements
  ],
  "metadata": {
    "has_interfaces": true,
    "has_type_aliases": true,
    "has_async_functions": true
  }
}
```

Now we have actual data about the code structure, not just boolean flags!
