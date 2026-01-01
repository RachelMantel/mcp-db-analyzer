from __future__ import annotations
from mcp_db_analyzer.insights import build_insights


def test_build_insights_detects_orphan_and_missing_index() -> None:
    tables = [
        {
            "table": "parent",
            "columns": [{"name": "id"}],
            "primary_key": ["id"],
            "indexes": [],
            "unique_constraints": [],
        },
        {
            "table": "child",
            "columns": [{"name": "parent_id"}, {"name": "value"}],
            "primary_key": [],
            "indexes": [],
            "unique_constraints": [],
        },
        {
            "table": "lonely",
            "columns": [{"name": "id"}],
            "primary_key": ["id"],
            "indexes": [],
            "unique_constraints": [],
        },
    ]
    fks = [
        {
            "table": "child",
            "constrained_columns": ["parent_id"],
            "referred_table": "parent",
            "referred_columns": ["id"],
        }
    ]

    insights = build_insights(tables, fks)
    assert insights["orphan_tables"] == ["lonely"]
    assert insights["missing_fk_indexes"] == {
        "missing": [{"table": "child", "columns": ["parent_id"]}],
        "suboptimal": [],
    }


def test_build_insights_detects_many_to_many() -> None:
    tables = [
        {
            "table": "join_table",
            "columns": [{"name": "left_id"}, {"name": "right_id"}],
            "primary_key": ["left_id", "right_id"],
            "indexes": [],
            "unique_constraints": [],
        }
    ]
    fks = [
        {
            "table": "join_table",
            "constrained_columns": ["left_id"],
            "referred_table": "left",
            "referred_columns": ["id"],
        },
        {
            "table": "join_table",
            "constrained_columns": ["right_id"],
            "referred_table": "right",
            "referred_columns": ["id"],
        },
    ]

    insights = build_insights(tables, fks)
    assert insights["many_to_many"] == [
        {
            "table": "join_table",
            "references": ["left", "right"],
            "confidence": "high",
            "extra_columns": [],
        }
    ]


def test_build_insights_detects_likely_many_to_many() -> None:
    tables = [
        {
            "table": "join_table",
            "columns": [
                {"name": "left_id"},
                {"name": "right_id"},
                {"name": "created_at"},
                {"name": "status"},
            ],
            "primary_key": ["left_id", "right_id"],
            "indexes": [],
            "unique_constraints": [],
        }
    ]
    fks = [
        {
            "table": "join_table",
            "constrained_columns": ["left_id"],
            "referred_table": "left",
            "referred_columns": ["id"],
        },
        {
            "table": "join_table",
            "constrained_columns": ["right_id"],
            "referred_table": "right",
            "referred_columns": ["id"],
        },
    ]

    insights = build_insights(tables, fks)
    assert insights["many_to_many"] == [
        {
            "table": "join_table",
            "references": ["left", "right"],
            "confidence": "medium",
            "extra_columns": ["created_at", "status"],
        }
    ]
