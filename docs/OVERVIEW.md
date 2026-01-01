MCP DB Analyzer - Docs Overview

Purpose
This project runs a local MCP server that inspects database schemas, builds
relationship graphs, and reports lightweight heuristic insights.

Who is it for
- Developers who need quick schema visibility across SQL backends.
- Teams that want a simple MCP endpoint for schema metadata.

What it does
- Connects via SQLAlchemy and introspects tables, views, columns, keys.
- Builds Mermaid ER or Graphviz DOT diagrams.
- Emits insights like orphan tables and missing FK indexes.

What it does not do
- It does not scan data contents (no data profiling).
- It does not run migrations or make schema changes.
- It does not replace full ER modeling tools.

Project Structure
- src/mcp_db_analyzer/db.py: schema collection via SQLAlchemy Inspector
- src/mcp_db_analyzer/graph.py: DOT and Mermaid diagram builders
- src/mcp_db_analyzer/insights.py: heuristic insights
- src/mcp_db_analyzer/tools: MCP tool registration
- src/mcp_db_analyzer/resources: resource endpoints for examples/help
- src/mcp_db_analyzer/prompts: prompt templates for clients
