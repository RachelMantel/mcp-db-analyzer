from __future__ import annotations
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP

# ייבוא הלוגיקה ישירות מה-Database ומה-Graph builder
# זה מבטיח שאנחנו לא תלויים ברישום של כלים אחרים
from mcp_db_analyzer.db import collect_schema
from mcp_db_analyzer.graph import build_dot, build_mermaid_er

def register_graph_tools(mcp: FastMCP) -> None:
    """Register graph visualization tools."""

    @mcp.tool()
    def schema_graph_dot(
        connection_url: str,
        schema: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Return a DOT graph for the schema (tables + foreign keys).
        Use this to get a technical, graphviz-compatible representation of the DB.
        """
        result = collect_schema(connection_url=connection_url, schema=schema)
        
        if result.get("error"):
            return result

        tables = result.get("tables", [])
        fks = result.get("foreign_keys", [])

        dot_content = build_dot(tables, fks)
        
        return {
            "schema": schema,
            "dot": dot_content,
            "metadata": {
                "tables_count": len(tables),
                "foreign_keys_count": len(fks),
                "dialect": result.get("dialect"),
            }
        }

    @mcp.tool()
    def schema_graph_mermaid(
        connection_url: str,
        schema: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a Mermaid ER diagram for the schema.
        Ideal for visual documentation and understanding relationships.
        """
        result = collect_schema(connection_url=connection_url, schema=schema)
        
        if result.get("error"):
            return result

        tables = result.get("tables", [])
        fks = result.get("foreign_keys", [])

        mermaid_result = build_mermaid_er(tables=tables, fks=fks)
        
        if "error" in mermaid_result:
            return {
                "schema": schema,
                "error": mermaid_result["error"],
                "dialect": result.get("dialect")
            }

        return {
            "schema": schema,
            "mermaid": mermaid_result["mermaid"],
            "metadata": {
                "tables_count": len(tables),
                "foreign_keys_count": len(fks),
                "dialect": result.get("dialect"),
            }
        }
