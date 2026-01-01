from __future__ import annotations

from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from sqlalchemy.engine import Engine

from mcp_db_analyzer.db import collect_schema, get_schema_inspector, open_engine
from mcp_db_analyzer.graph import build_dot, render_mermaid_er
from mcp_db_analyzer.insights import build_insights


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def server_info() -> Dict[str, Any]:
        """Return basic server info to verify MCP is running."""
        return {
            "name": "mcp-db-analyzer",
            "status": "ok",
            "tools": [
                "inspect_schema",
                "schema_graph_dot",
                "schema_graph_mermaid",
                "schema_insights",
                "list_schemas",
            ],
            "notes": "DB Analyzer MCP is running.",
        }

    @mcp.tool()
    def inspect_schema(
        connection_url: str,
        schema: Optional[str] = None,
        include_tables: Optional[List[str]] = None,
        exclude_tables: Optional[List[str]] = None,
        include_stats: bool = False,
        include_insights: bool = False,
    ) -> Dict[str, Any]:
        """
        Inspect DB schema via SQLAlchemy Inspector.

        Args:
            connection_url: SQLAlchemy connection URL.
            schema: Optional schema name (e.g., "public" for PostgreSQL).
            include_tables: Optional list of tables to include.
            exclude_tables: Optional list of tables to exclude.
            include_stats: Include row counts per table (guarded).
            include_insights: Include heuristic insights in the same response.
        """
        result = collect_schema(
            connection_url=connection_url,
            schema=schema,
            include_tables=include_tables,
            exclude_tables=exclude_tables,
            include_stats=include_stats,
        )

        if include_insights and not result.get("error"):
            result["insights"] = build_insights(
                result.get("tables", []),
                result.get("foreign_keys", []),
            )

        return result

    @mcp.tool()
    def schema_graph_dot(connection_url: str, schema: Optional[str] = None) -> Dict[str, Any]:
        """
        Return a DOT graph for the schema (tables + foreign keys).
        """
        result = inspect_schema(connection_url=connection_url, schema=schema)
        if result.get("error"):
            return result

        dot = build_dot(result.get("tables", []), result.get("foreign_keys", []))
        return {
            "schema": schema,
            "dot": dot,
            "tables_count": len(result.get("tables", [])),
            "foreign_keys_count": len(result.get("foreign_keys", [])),
            "dialect": result.get("dialect"),
        }

    @mcp.tool()
    def schema_graph_mermaid(connection_url: str, schema: Optional[str] = None) -> Dict[str, Any]:
        result = inspect_schema(connection_url=connection_url, schema=schema)
        if result.get("error"):
            return result

        tables = result.get("tables", [])
        fks = result.get("foreign_keys", [])

        mer = render_mermaid_er(tables=tables, fks=fks)
        if mer.get("error"):
            return {"schema": schema, "error": mer["error"], "dialect": result.get("dialect")}

        return {
            "schema": schema,
            "mermaid": mer["mermaid"],
            "tables_count": len(tables),
            "foreign_keys_count": len(fks),
            "dialect": result.get("dialect"),
        }



    @mcp.tool()
    def schema_insights(
        connection_url: str,
        schema: Optional[str] = None,
        include_tables: Optional[List[str]] = None,
        exclude_tables: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Return heuristic insights about the schema.
        """
        result = inspect_schema(
            connection_url=connection_url,
            schema=schema,
            include_tables=include_tables,
            exclude_tables=exclude_tables,
            include_insights=False,
        )
        if result.get("error"):
            return result

        return {
            "schema": schema,
            "dialect": result.get("dialect"),
            "insights": build_insights(
                result.get("tables", []),
                result.get("foreign_keys", []),
            ),
        }

    @mcp.tool()
    def list_schemas(connection_url: str) -> Dict[str, Any]:
        """
        List available schemas for the given DB.
        """
        engine: Optional[Engine] = None
        try:
            engine = open_engine(connection_url)
            inspector = get_schema_inspector(engine)
            schemas = inspector.get_schema_names()
            return {"schemas": schemas, "dialect": engine.dialect.name}
        except Exception as exc:
            return {"schemas": [], "error": str(exc)}
        finally:
            if engine is not None:
                engine.dispose()
