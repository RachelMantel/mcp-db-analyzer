from __future__ import annotations
import asyncio
import json
from typing import List
from mcp.server.fastmcp import FastMCP
from mcp_db_analyzer.prompts.schema_prompts import register_prompts
from mcp_db_analyzer.resources.schema_resources import register_resources


def _get_prompt_names(mcp: FastMCP) -> List[str]:
    prompts = asyncio.run(mcp.list_prompts())
    return [prompt.name for prompt in prompts]


def _get_resource_content(mcp: FastMCP, uri: str) -> str:
    contents = asyncio.run(mcp.read_resource(uri))
    if isinstance(contents, list):
        contents = contents[0]
    return contents.content


def test_prompts_registered_and_structure() -> None:
    mcp = FastMCP("test")
    register_prompts(mcp)

    prompt_names = _get_prompt_names(mcp)
    assert "schema_report" in prompt_names
    assert "schema_diagram" in prompt_names

    prompt_map = mcp._prompt_manager._prompts
    for name in ("schema_report", "schema_diagram"):
        prompt_fn = prompt_map[name].fn
        result = prompt_fn("sqlite:///test.db")
        assert isinstance(result, list)
        assert result, "Prompt must return at least one message"
        for message in result:
            assert isinstance(message, dict)
            assert "role" in message
            assert "content" in message
            assert isinstance(message["role"], str)
            assert isinstance(message["content"], str)


def test_resources_return_strings_and_valid_json() -> None:
    mcp = FastMCP("test")
    register_resources(mcp)

    usage = _get_resource_content(mcp, "resource://mcp-db-analyzer/usage")
    assert isinstance(usage, str)
    assert usage

    examples = _get_resource_content(mcp, "resource://mcp-db-analyzer/examples/inspect_schema")
    assert isinstance(examples, str)
    parsed = json.loads(examples)
    assert isinstance(parsed, dict)
