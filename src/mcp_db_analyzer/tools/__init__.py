from mcp.server.fastmcp import FastMCP
from src.mcp_db_analyzer.tools.info_tools import register_info_tools
from .schema_tools import register_schema_tools
from .graph_tools import register_graph_tools


def register_tools(mcp: FastMCP) -> None:
    """Register all tools for the MCP server."""
    register_info_tools(mcp)
    register_schema_tools(mcp)
    register_graph_tools(mcp)
