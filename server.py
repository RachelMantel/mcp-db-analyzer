from __future__ import annotations
from pathlib import Path
import sys
SRC_ROOT = Path(__file__).resolve().parent / "src"
# Allow running `python server.py` from repo root without PYTHONPATH.
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mcp.server.fastmcp import FastMCP
from mcp_db_analyzer.prompts.schema_prompts import register_prompts
from mcp_db_analyzer.resources.schema_resources import register_resources
from mcp_db_analyzer.tools import register_tools

mcp = FastMCP("mcp-db-analyzer")
register_prompts(mcp)
register_resources(mcp)
register_tools(mcp)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
