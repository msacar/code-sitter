"""
Proposed analyze.py output with structure extraction:

$ codesitter analyze file src/services/userService.ts

═══════════════════════════════════════════════════════════════════════════════
Analysis: src/services/userService.ts
Language: typescript | Analyzer: TypeScriptAnalyzer
═══════════════════════════════════════════════════════════════════════════════

📦 Imports (3):
  react → useState, useEffect (line 1)
  ./types → User, UserRole (line 2)
  ./api → fetchUser (line 3)

🏗️ Structure (5 elements):

  📘 Interface: User (lines 5-9)
    Fields: id: number, name: string, email?: string
    Exported: ✓

  📘 Type: UserRole (line 11)
    Definition: 'admin' | 'user' | 'guest'
    Exported: ✓

  🔧 Function: getUser (lines 13-17)
    async ✓ | exported ✓
    Parameters: (id: number, options?: FetchOptions)
    Returns: Promise<User | null>

  🔧 Function: validateUser (lines 19-21)
    arrow function ✓ | exported ✓
    Parameters: (user: User)
    Returns: boolean

  🏛️ Class: UserService (lines 23-45)
    exported ✓
    Methods: 3
      - constructor(db: Database)
      - async addUser(user: User): Promise<void>
      - findUser(id: number): User | undefined

📞 Function Calls (8):
  constructor → super() at line 25
  addUser → this.db.save(user) at line 30
  findUser → this.users.find(callback) at line 35
  ... and 5 more

📊 Metadata:
  has_interfaces: ✓
  has_type_aliases: ✓
  has_async_functions: ✓
  is_test_file: ✗

═══════════════════════════════════════════════════════════════════════════════

With --json flag:
{
  "file": "src/services/userService.ts",
  "structure": [
    {
      "type": "interface",
      "name": "User",
      "lines": "5-9",
      "exported": true,
      "fields": [
        {"name": "id", "type": "number", "optional": false},
        {"name": "name", "type": "string", "optional": false},
        {"name": "email", "type": "string", "optional": true}
      ]
    },
    {
      "type": "function",
      "name": "getUser",
      "lines": "13-17",
      "async": true,
      "exported": true,
      "parameters": [
        {"name": "id", "type": "number", "optional": false},
        {"name": "options", "type": "FetchOptions", "optional": true}
      ],
      "return_type": "Promise<User | null>"
    }
  ],
  "imports": [...],
  "calls": [...],
  "metadata": {...}
}
"""
