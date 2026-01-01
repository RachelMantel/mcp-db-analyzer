MCP DB Analyzer

Local MCP server for database inspection, relationship analysis, and schema insights.

Structure
- src/mcp_db_inspector: package root
- src/mcp_db_inspector/db: connection + metadata extraction
- src/mcp_db_inspector/graph: graph/DOT output building
- src/mcp_db_inspector/insights: heuristics and findings

Tools
- server_info: server status and supported tools
- inspect_schema: tables/columns/PK/FK/indexes/unique constraints + filters/stats
- schema_graph_dot: DOT graph for tables + foreign keys
- schema_graph_mermaid: Mermaid ER diagram for tables + foreign keys
- schema_insights: heuristic insights about schema quality
- list_schemas: available schemas in the DB

Setup
- python -m venv .venv
- .venv\Scripts\activate
- pip install -r requirements.txt

Run
- python server.py

Example connection URLs
- sqlite:///test.db
- postgresql+psycopg://user:pass@localhost:5432/mydb
- mssql+pyodbc://@HOST/DB?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes

Example calls (tool inputs)
inspect_schema:
{
  "connection_url": "sqlite:///test.db",
  "include_stats": true,
  "include_insights": true
}

schema_graph_mermaid:
{
  "connection_url": "sqlite:///test.db"
}

Codex MCP config example
- See codex.config.example.toml

MCP Inspector quick test (mcp-db-analyzer)
1) python server.py
2) npx @modelcontextprotocol/inspector
3) Add server:
   - name: mcp-db-analyzer
   - command: python
   - args: ["server.py"]
   - cwd: this repo path
4) Call inspect_schema with connection_url "sqlite:///test.db".

Notes
- Uses SQLAlchemy Inspector for cross-DB metadata.
- Add the driver for your DB (see requirements.txt).