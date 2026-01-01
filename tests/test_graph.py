from __future__ import annotations
from mcp_db_analyzer.graph import build_dot


def test_build_dot_contains_nodes_and_edges() -> None:
    tables = [{"table": "users"}, {"table": "orders"}]
    fks = [
        {
            "table": "orders",
            "referred_table": "users",
            "constrained_columns": ["user_id"],
            "referred_columns": ["id"],
        }
    ]
    dot = build_dot(tables, fks)

    assert '"users"' in dot
    assert '"orders"' in dot
    assert '"orders" -> "users"' in dot
    assert 'label="user_id -> id"' in dot
