MCP DB Analyzer

Local MCP server that inspects database schemas, builds relationship graphs, and produces lightweight insights. Built as a clean, local MCP implementation suitable for use by coding agents (Codex, Cursor, Claude Code, Gemini).

Why this exists
The goal of this project is to demonstrate a fully working local MCP server that:
- Runs as a process on a laptop (no hosting required)
- Exposes useful tools for coding agents
- Is easy to inspect, extend, and test

Features
- Schema inspection via SQLAlchemy Inspector (tables, columns, PK/FK, indexes, views)
- Mermaid ER and Graphviz DOT diagram generation
- Heuristic insights (orphan tables, missing FK indexes, many-to-many detection)
- MCP resources and prompts for quick usage

Project Structure
- src/mcp_db_analyzer: package root
- src/mcp_db_analyzer/db.py: schema collection + connection handling
- src/mcp_db_analyzer/graph.py: DOT/Mermaid builders
- src/mcp_db_analyzer/insights.py: heuristic analysis
- src/mcp_db_analyzer/tools: MCP tool registration
- src/mcp_db_analyzer/resources: resource endpoints
- src/mcp_db_analyzer/prompts: prompt templates
- docs: extended documentation

Quickstart
1) python -m venv .venv
2) .venv\Scripts\activate
3) pip install -r requirements.txt
4) python server.py

MCP Inspector Quick Test
1) python server.py
2) npx @modelcontextprotocol/inspector
3) Add server:
   - name: mcp-db-analyzer
   - command: python
   - args: ["server.py"]
   - cwd: this repo path
4) Call inspect_schema with connection_url "sqlite:///test.db"

Tools
- server_info: basic server status and tool list
- list_schemas: list available schemas for a DB
- inspect_schema: tables/columns/PK/FK/indexes/unique constraints + filters/stats
- schema_graph_dot: Graphviz DOT output for tables + foreign keys
- schema_graph_mermaid: Mermaid ER output for tables + foreign keys
- schema_insights: heuristic insights about schema quality

Tool Outputs (high level)
- server_info: name, status, tools, notes
- list_schemas: schemas, dialect (or error)
- inspect_schema: schema, tables, foreign_keys, views, dialect, warnings (or error)
- schema_graph_dot: schema, dot, tables_count, foreign_keys_count, dialect (or error)
- schema_graph_mermaid: schema, mermaid, tables_count, foreign_keys_count, dialect (or error)
- schema_insights: schema, dialect, insights (or error)

Drivers
- Install the driver for your database:
  - PostgreSQL: psycopg (or psycopg2-binary)
  - MySQL: pymysql (or mysqlclient)
  - SQL Server: pyodbc (requires ODBC driver)

Connection URL Examples
- sqlite:///test.db
- postgresql+psycopg://user:pass@localhost:5432/mydb
- mysql+pymysql://user:pass@localhost:3306/mydb
- mssql+pyodbc://@HOST/DB?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes

Example Tool Inputs
inspect_schema:
```json
{
  "connection_url": "sqlite:///test.db",
  "include_stats": true,
  "include_insights": true
}
```

inspect_schema with filters:
```json
{
  "connection_url": "postgresql+psycopg://user:pass@localhost:5432/mydb",
  "schema": "public",
  "include_tables": ["users", "orders"],
  "exclude_tables": ["audit_log"]
}
```

schema_graph_mermaid:
```json
{
  "connection_url": "sqlite:///test.db"
}
```

schema_graph_dot:
```json
{
  "connection_url": "sqlite:///test.db"
}
```

Schema Diagram Example (Mermaid ER)
```mermaid
erDiagram
  users {
    INTEGER id
    TEXT name
  }
  orders {
    INTEGER id
    INTEGER user_id
  }
  users ||--o{ orders : id -> user_id
```

Troubleshooting
- Import error for mcp_db_analyzer: run from repo root or ensure `src` is on `PYTHONPATH`.
- Missing driver error: install the correct SQLAlchemy driver for your DB.
- Row counts skipped: for non-SQLite, set `schema` or `include_tables` when `include_stats` is true.

Security Note
- Prefer TLS/SSL connections and avoid plaintext DB connections.
- Do not hard-code credentials; use env vars or a secret manager.
- Schema metadata may be sensitive; treat outputs accordingly.

Docs
- docs/OVERVIEW.md
- docs/USAGE.md
- docs/TOOLS.md
- docs/SECURITY.md

Notes
- Uses SQLAlchemy Inspector for cross-DB metadata.
- Row counts can be expensive; for non-SQLite, stats are gated by schema or include_tables.
- See codex.config.example.toml for a Codex MCP config sample.
