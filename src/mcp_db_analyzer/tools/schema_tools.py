from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from src.mcp_db_analyzer.db import collect_schema
from src.mcp_db_analyzer.insights import build_insights


def register_schema_tools(mcp: FastMCP) -> None:
    """Register schema inspection tools."""
    
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
    def schema_insights(
        connection_url: str,
        schema: Optional[str] = None,
        include_tables: Optional[List[str]] = None,
        exclude_tables: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Return heuristic insights about the schema."""
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

