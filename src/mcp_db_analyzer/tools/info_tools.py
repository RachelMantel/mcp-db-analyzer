from typing import Any, Dict
from mcp.server.fastmcp import FastMCP
from sqlalchemy.engine import Engine
from src.mcp_db_analyzer.db import open_engine, get_schema_inspector


def register_info_tools(mcp: FastMCP) -> None:
    """Register server info tools."""
    
    @mcp.tool()
    def server_info() -> Dict[str, Any]:
        """Return basic server info to verify MCP is running."""
        return {
            "name": "mcp-db-analyzer",
            "status": "ok",
            "tools": [
                "server_info",
                "list_schemas",
                "inspect_schema",
                "schema_graph_dot",
                "schema_graph_mermaid",
                "schema_insights",
            ],
            "notes": "DB Analyzer MCP is running.",
        }

    @mcp.tool()
    def list_schemas(connection_url: str) -> Dict[str, Any]:
        """List available schemas for the given DB."""
        
        engine: Engine | None = None
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
