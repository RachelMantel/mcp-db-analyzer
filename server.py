from __future__ import annotations
from mcp.server.fastmcp import FastMCP
from src.mcp_db_analyzer.prompts.schema_prompts import register_prompts
from src.mcp_db_analyzer.resources.schema_resources import register_resources
from src.mcp_db_analyzer.tools import register_tools

mcp = FastMCP("mcp-db-analyzer")
register_prompts(mcp)
register_resources(mcp)
register_tools(mcp)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
