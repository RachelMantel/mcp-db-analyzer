from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError


def open_engine(connection_url: str) -> Engine:
    return create_engine(connection_url)


def get_schema_inspector(engine: Engine):
    return inspect(engine)


def split_schema_and_table(name: str) -> Tuple[Optional[str], str]:
    if "." in name:
        schema, table = name.split(".", 1)
        return schema, table
    return None, name


def format_table_name(schema: Optional[str], table: str) -> str:
    return f"{schema}.{table}" if schema else table


def _normalize_table_name(schema: Optional[str], table: str) -> str:
    return f"{schema}.{table}".lower() if schema else table.lower()


def _normalize_filter_names(names: Optional[List[str]]) -> Tuple[set[str], set[str]]:
    bare: set[str] = set()
    qualified: set[str] = set()
    if not names:
        return bare, qualified
    for name in names:
        if not name:
            continue
        schema, table = split_schema_and_table(name)
        if not table:
            continue
        bare.add(table.lower())
        if schema:
            qualified.add(f"{schema}.{table}".lower())
    return bare, qualified


def _filter_tables(
    tables: List[str],
    schema: Optional[str],
    include_tables: Optional[List[str]],
    exclude_tables: Optional[List[str]],
) -> List[str]:
    if not include_tables and not exclude_tables:
        return tables

    include_bare, include_qualified = _normalize_filter_names(include_tables)
    exclude_bare, exclude_qualified = _normalize_filter_names(exclude_tables)

    filtered: List[str] = []
    for table in tables:
        normalized_full = _normalize_table_name(schema, table)
        normalized_bare = table.lower()
        if include_tables and normalized_full not in include_qualified and normalized_bare not in include_bare:
            continue
        if normalized_full in exclude_qualified or normalized_bare in exclude_bare:
            continue
        filtered.append(table)

    return filtered


def _count_rows(engine: Engine, schema: Optional[str], table: str) -> Optional[int]:
    """
    Exact row counts can be expensive on large tables (Postgres/MySQL).
    This is optional and guarded by _should_count_rows.
    """
    preparer = engine.dialect.identifier_preparer
    quoted_table = preparer.quote(table)
    qualified = f"{preparer.quote(schema)}.{quoted_table}" if schema else quoted_table

    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) AS count FROM {qualified}"))
            return int(result.scalar() or 0)
    except SQLAlchemyError:
        return None


def _should_count_rows(
    include_stats: bool,
    engine: Engine,
    schema: Optional[str],
    include_tables: Optional[List[str]],
) -> bool:
    if not include_stats:
        return False
    if engine.dialect.name == "sqlite":
        return True
    # For non-SQLite, require scope restriction to avoid full DB scans.
    return bool(schema or include_tables)


def collect_schema(
    connection_url: str,
    schema: Optional[str] = None,
    include_tables: Optional[List[str]] = None,
    exclude_tables: Optional[List[str]] = None,
    include_stats: bool = False,
) -> Dict[str, Any]:
    engine: Optional[Engine] = None
    try:
        engine = open_engine(connection_url)
        inspector = get_schema_inspector(engine)

        tables: List[str] = inspector.get_table_names(schema=schema)
        views: List[str] = inspector.get_view_names(schema=schema)

        tables = _filter_tables(tables, schema, include_tables, exclude_tables)
        views = _filter_tables(views, schema, include_tables, exclude_tables)

        allowed_tables_qualified = {_normalize_table_name(schema, table) for table in tables}
        allowed_tables_bare = {table.lower() for table in tables}

        count_rows = _should_count_rows(include_stats, engine, schema, include_tables)
        warnings: List[str] = []
        if include_stats and not count_rows:
            warnings.append(
                "Row counts skipped unless schema or include_tables is provided for non-SQLite."
            )

        table_details: List[Dict[str, Any]] = []
        fk_details: List[Dict[str, Any]] = []

        for table in tables:
            columns = inspector.get_columns(table, schema=schema)
            pk = inspector.get_pk_constraint(table, schema=schema)
            fks = inspector.get_foreign_keys(table, schema=schema)
            indexes = inspector.get_indexes(table, schema=schema)
            uniques = inspector.get_unique_constraints(table, schema=schema)

            table_details.append(
                {
                    "table": format_table_name(schema, table),
                    "columns": [
                        {
                            "name": col.get("name"),
                            "type": str(col.get("type")),
                            "nullable": bool(col.get("nullable")),
                            "default": col.get("default"),
                        }
                        for col in (columns or [])
                    ],
                    "primary_key": (pk or {}).get("constrained_columns", []) or [],
                    "indexes": [
                        {
                            "name": idx.get("name"),
                            "columns": idx.get("column_names", []) or [],
                            "unique": bool(idx.get("unique")),
                        }
                        for idx in (indexes or [])
                    ],
                    "unique_constraints": [
                        {
                            "name": uc.get("name"),
                            "columns": uc.get("column_names", []) or [],
                        }
                        for uc in (uniques or [])
                    ],
                    "row_count": _count_rows(engine, schema, table) if count_rows else None,
                }
            )

            for fk in (fks or []):
                referred_schema = fk.get("referred_schema")
                referred_table = fk.get("referred_table") or ""
                split_schema, split_table = split_schema_and_table(referred_table)
                if split_table:
                    referred_table = split_table
                    if split_schema:
                        referred_schema = split_schema
                    elif schema and not referred_schema:
                        referred_schema = schema
                elif schema and not referred_schema:
                    referred_schema = schema

                if referred_table:
                    normalized_referred = _normalize_table_name(referred_schema, referred_table)
                    if (
                        normalized_referred not in allowed_tables_qualified
                        and referred_table.lower() not in allowed_tables_bare
                    ):
                        continue

                fk_details.append(
                    {
                        "table": format_table_name(schema, table),
                        "constrained_columns": fk.get("constrained_columns", []) or [],
                        "referred_table": format_table_name(referred_schema, referred_table),
                        "referred_columns": fk.get("referred_columns", []) or [],
                    }
                )

        return {
            "schema": schema,
            "tables": table_details,
            "foreign_keys": fk_details,
            "views": views,
            "dialect": engine.dialect.name,
            "warnings": warnings,
        }

    except SQLAlchemyError as exc:
        return {
            "schema": schema,
            "error": str(exc),
            "tables": [],
            "foreign_keys": [],
            "views": [],
        }
    finally:
        if engine is not None:
            engine.dispose()
