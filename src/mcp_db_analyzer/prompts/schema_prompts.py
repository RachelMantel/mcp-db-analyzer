from __future__ import annotations
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    @mcp.prompt(
        name="schema_report",
        title="DB Schema Report",
        description="Request a concise schema report using inspect_schema.",
    )
    def schema_report_prompt(connection_url: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        schema_text = schema or "default"
        return [
            {
                "role": "user",
                "content": (
                    "Inspect this database schema and summarize:\n"
                    "- List all tables and their purpose\n"
                    "- Explain key relationships\n"
                    "- Identify the most important tables\n"
                    "- Point out schema/data risks\n"
                    "- Provide a visual schema diagram\n\n"
                    f"Connection URL: {connection_url}\n"
                    f"Schema: {schema_text}\n"
                    "Use the inspect_schema tool and present results clearly and concisely."
                ),
            }
        ]

    @mcp.prompt(
        name="schema_diagram",
        title="Schema Diagram",
        description="Generate a Mermaid ER diagram for a schema.",
    )
    def schema_diagram_prompt(connection_url: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        schema_text = schema or "default"
        return [
            {
                "role": "user",
                "content": (
                    "Generate a Mermaid ER diagram for this database schema.\n\n"
                    f"Connection URL: {connection_url}\n"
                    f"Schema: {schema_text}\n"
                    "Use inspect_schema and format the diagram as a mermaid erDiagram block."
                ),
            }
        ]
