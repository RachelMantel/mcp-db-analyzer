Tools Reference

server_info
- Purpose: returns basic server status and tool list.
- Input: none

list_schemas
- Purpose: list available schemas for a connection.
- Input:
  - connection_url: SQLAlchemy connection URL

inspect_schema
- Purpose: inspect tables, columns, PK/FK, indexes, uniques, views.
- Input:
  - connection_url: SQLAlchemy connection URL
  - schema: optional schema name (e.g., public)
  - include_tables: optional list of tables to include
  - exclude_tables: optional list of tables to exclude
  - include_stats: optional row counts (guarded)
  - include_insights: optional heuristic insights

schema_graph_mermaid
- Purpose: generate Mermaid ER diagram text from schema.
- Input:
  - connection_url: SQLAlchemy connection URL
  - schema: optional schema name

schema_graph_dot
- Purpose: generate Graphviz DOT diagram text from schema.
- Input:
  - connection_url: SQLAlchemy connection URL
  - schema: optional schema name

schema_insights
- Purpose: return heuristic insights about schema quality.
- Input:
  - connection_url: SQLAlchemy connection URL
  - schema: optional schema name
  - include_tables: optional list of tables to include
  - exclude_tables: optional list of tables to exclude
