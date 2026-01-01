from __future__ import annotations

import json
from typing import Dict

from mcp.server.fastmcp import FastMCP


def register_resources(mcp: FastMCP) -> None:
    @mcp.resource(
        "resource://mcp-db-analyzer/usage",
        name="usage",
        title="Usage Guide",
        description="Quick usage guide for the MCP DB analyzer.",
        mime_type="text/plain",
    )
    def usage_guide() -> str:
        return (
            "MCP DB Analyzer\n"
            "- inspect_schema: tables/columns/PK/FK/indexes/uniques + filters/stats\n"
            "- schema_graph_dot: DOT graph for tables + foreign keys\n"
            "- schema_graph_mermaid: Mermaid ER diagram for tables + foreign keys\n"
            "- schema_insights: heuristic insights about schema quality\n"
            "- list_schemas: list available schemas\n"
        )

    @mcp.resource(
        "resource://mcp-db-analyzer/examples/{tool}",
        name="tool_examples",
        title="Tool Example Inputs",
        description="Example JSON inputs for common tools.",
        mime_type="application/json",
    )
    def tool_examples(tool: str) -> str:
        examples: Dict[str, Dict[str, object]] = {
            "inspect_schema": {
                "connection_url": "sqlite:///test.db",
                "include_stats": True,
                "include_insights": True,
            },
            "schema_graph_mermaid": {
                "connection_url": "sqlite:///test.db",
            },
            "schema_graph_dot": {
                "connection_url": "sqlite:///test.db",
            },
            "schema_insights": {
                "connection_url": "sqlite:///test.db",
            },
            "list_schemas": {
                "connection_url": "sqlite:///test.db",
            },
        }

        payload = examples.get(
            tool,
            {"error": "Unknown tool. Try inspect_schema, schema_graph_mermaid, or schema_graph_dot."},
        )
        return json.dumps(payload, indent=2)
