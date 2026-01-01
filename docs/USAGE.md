# Usage

## Quickstart
1) python -m venv .venv
2) .venv\Scripts\activate
3) pip install -r requirements.txt
4) python server.py

## Connection URLs
- sqlite:///test.db
- postgresql+psycopg://user:pass@localhost:5432/mydb
- mysql+pymysql://user:pass@localhost:3306/mydb
- mssql+pyodbc://@HOST/DB?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes

## MCP Inspector quick test
1) python server.py
2) npx @modelcontextprotocol/inspector
3) Add server:
   - name: mcp-db-analyzer
   - command: python
   - args: ["server.py"]
   - cwd: this repo path
4) Call inspect_schema with connection_url "sqlite:///test.db"

## Example inputs
inspect_schema:
```json
{
  "connection_url": "sqlite:///test.db",
  "include_stats": true,
  "include_insights": true
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

## Common issues
- Missing driver error: install the correct SQLAlchemy driver for your DB.
- Slow stats: row counts are gated for non-SQLite unless schema or include_tables is set.
