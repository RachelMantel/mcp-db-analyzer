from __future__ import annotations
from typing import Any, Dict, List, Set


def _table_index_lists(table: Dict[str, Any]) -> List[List[str]]:
    """
    Return a list of index column lists that "cover" lookups:
    - PK columns
    - Regular indexes
    - Unique constraints
    """
    indexes: List[List[str]] = []

    pk_cols = list(table.get("primary_key", []) or [])
    if pk_cols:
        indexes.append(pk_cols)

    for idx in table.get("indexes", []) or []:
        cols = list(idx.get("columns", []) or [])
        if cols:
            indexes.append(cols)

    for uc in table.get("unique_constraints", []) or []:
        cols = list(uc.get("columns", []) or [])
        if cols:
            indexes.append(cols)

    return indexes


def find_orphan_tables(tables: List[Dict[str, Any]], fks: List[Dict[str, Any]]) -> List[str]:
    """
    Tables that have no incoming or outgoing foreign key relationships.
    """
    if not tables:
        return []

    outgoing = {fk.get("table") for fk in fks}
    incoming = {fk.get("referred_table") for fk in fks}

    orphans: List[str] = []
    for table in tables:
        name = table.get("table")
        if not name:
            continue
        if name not in outgoing and name not in incoming:
            orphans.append(name)

    return orphans


def _is_index_prefix(index_cols: List[str], fk_cols: List[str]) -> bool:
    """
    True if index_cols begins with fk_cols (prefix match), case-insensitive.
    Important for composite indexes where order matters (Postgres, etc).
    """
    if len(index_cols) < len(fk_cols):
        return False

    index_norm = [c.lower() for c in index_cols]
    fk_norm = [c.lower() for c in fk_cols]
    return index_norm[: len(fk_norm)] == fk_norm


def find_missing_fk_indexes(
    tables: List[Dict[str, Any]], fks: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Detect FK columns missing proper indexing.
    Returns:
      {
        "missing": [...],     # no index covering fk columns
        "suboptimal": [...]   # index covers columns but order not ideal (not prefix)
      }
    """
    if not tables or not fks:
        return {"missing": [], "suboptimal": []}

    table_map = {t.get("table"): t for t in tables}

    missing: List[Dict[str, Any]] = []
    suboptimal: List[Dict[str, Any]] = []

    for fk in fks:
        table_name = fk.get("table")
        fk_cols = list(fk.get("constrained_columns", []) or [])
        if not table_name or not fk_cols:
            continue

        table = table_map.get(table_name, {}) or {}
        indexed_lists = _table_index_lists(table)

        # Best: prefix match
        if any(_is_index_prefix(cols, fk_cols) for cols in indexed_lists):
            continue

        # Next best: subset coverage, case-insensitive (order mismatch)
        fk_set = {c.lower() for c in fk_cols}
        has_subset = any(fk_set.issubset({c.lower() for c in cols}) for cols in indexed_lists)

        if has_subset:
            suboptimal.append(
                {"table": table_name, "columns": list(fk_cols), "reason": "index_order_suboptimal"}
            )
        else:
            missing.append({"table": table_name, "columns": list(fk_cols)})

    return {"missing": missing, "suboptimal": suboptimal}


def _normalize_columns(columns: List[Dict[str, Any]]) -> Set[str]:
    return {col.get("name") for col in columns if col.get("name")}


def find_many_to_many(tables: List[Dict[str, Any]], fks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Heuristic many-to-many detection:
      - table has >= 2 FKs
      - if all columns are FK columns => high confidence
      - else allow small set of extra columns => medium confidence
    """
    if not tables or not fks:
        return []

    table_to_fks: Dict[str, List[Dict[str, Any]]] = {}
    for fk in fks:
        table_to_fks.setdefault(fk.get("table"), []).append(fk)

    findings: List[Dict[str, Any]] = []

    for table in tables:
        name = table.get("table")
        if not name:
            continue

        fks_for_table = table_to_fks.get(name, [])
        if len(fks_for_table) < 2:
            continue

        fk_cols: Set[str] = set()
        for fk in fks_for_table:
            fk_cols.update(fk.get("constrained_columns", []) or [])

        if not fk_cols:
            continue

        all_cols = _normalize_columns(table.get("columns", []) or [])
        extra_cols = sorted(all_cols - fk_cols)

        targets = [
            t for t in (fk.get("referred_table") for fk in fks_for_table) if t
        ]

        if fk_cols == all_cols:
            confidence = "high"
        else:
            allowed_extras = {"id", "created_at", "updated_at", "status", "role"}
            extra_cols_norm = {c.lower() for c in extra_cols}
            if extra_cols_norm.issubset(allowed_extras):
                confidence = "medium"
            else:
                continue

        findings.append(
            {
                "table": name,
                "references": targets,
                "confidence": confidence,
                "extra_columns": extra_cols,
            }
        )

    return findings


def build_insights(tables: List[Dict[str, Any]], fks: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "orphan_tables": find_orphan_tables(tables, fks),
        "many_to_many": find_many_to_many(tables, fks),
        "missing_fk_indexes": find_missing_fk_indexes(tables, fks),
    }
