from __future__ import annotations
import sqlite3
from typing import Dict, Any
import pytest
from mcp_db_analyzer.db import collect_schema


@pytest.fixture()
def sqlite_db_url(tmp_path) -> str:
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        INSERT INTO users(name) VALUES ('alice'), ('bob');
        INSERT INTO orders(user_id) VALUES (1), (1), (2);
        """
    )
    conn.commit()
    conn.close()
    return f"sqlite:///{db_path}"


def _table_map(result: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {table["table"]: table for table in result.get("tables", [])}


def test_collect_schema_basic(sqlite_db_url: str) -> None:
    result = collect_schema(sqlite_db_url, include_stats=True)
    assert result.get("error") is None
    table_map = _table_map(result)

    assert "users" in table_map
    assert "orders" in table_map
    assert table_map["users"]["row_count"] == 2
    assert table_map["orders"]["row_count"] == 3

    fks = result.get("foreign_keys", [])
    assert len(fks) == 1
    assert fks[0]["table"] == "orders"
    assert fks[0]["referred_table"] == "users"


def test_collect_schema_include_tables_filters_fk(sqlite_db_url: str) -> None:
    result = collect_schema(sqlite_db_url, include_tables=["orders"])
    table_map = _table_map(result)
    assert "orders" in table_map
    assert "users" not in table_map

    # FK should be filtered because referred table is not included.
    assert result.get("foreign_keys") == []


def test_collect_schema_exclude_tables(sqlite_db_url: str) -> None:
    result = collect_schema(sqlite_db_url, exclude_tables=["users"])
    table_map = _table_map(result)
    assert "users" not in table_map
    assert "orders" in table_map
