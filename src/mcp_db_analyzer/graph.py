from __future__ import annotations
from typing import Any, Dict, List, Tuple
import re


def build_dot(tables: List[Dict[str, Any]], fks: List[Dict[str, Any]]) -> str:
    """
    Build a Graphviz DOT diagram for DB schema:
    - One node per table
    - One directed edge per FK (child -> parent)
    - Optional labels include fk columns mapping (constrained -> referred)
    """
    lines: List[str] = [
        "digraph db_schema {",
        "  rankdir=LR;",
        "  node [shape=box, style=rounded];",
    ]

    seen_nodes: set[str] = set()
    seen_edges: set[tuple[str, str, tuple[str, ...], tuple[str, ...]]] = set()

    # Nodes
    for table in tables:
        name = table.get("table")
        if not name or name in seen_nodes:
            continue
        seen_nodes.add(name)
        lines.append(f'  "{name}";')

    # Edges
    for fk in fks:
        src = fk.get("table")
        dst = fk.get("referred_table")
        src_cols = fk.get("constrained_columns", []) or []
        dst_cols = fk.get("referred_columns", []) or []

        if not src or not dst:
            continue

        # Dedupe by structure, not by label text
        edge_key = (src, dst, tuple(src_cols), tuple(dst_cols))
        if edge_key in seen_edges:
            continue
        seen_edges.add(edge_key)

        label = ""
        if src_cols and dst_cols:
            src_label = ", ".join(src_cols)
            dst_label = ", ".join(dst_cols)
            label_text = f"{src_label} -> {dst_label}"
            # DOT label escaping
            label_text = label_text.replace("\\", "\\\\").replace('"', '\\"')
            label = f' [label="{label_text}"]'

        lines.append(f'  "{src}" -> "{dst}"{label};')

    lines.append("}")
    return "\n".join(lines)



def render_mermaid_er(tables: List[Dict[str, Any]], fks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build a Mermaid ER diagram from schema data (tables + fks), with strong dedupe.

    Returns:
      {"mermaid": "..."} or {"error": "...", "mermaid": None}
    """
    try:
        # ---- collect & dedupe table names ----
        table_names: set[str] = set()
        for t in tables:
            name = (t.get("table") or "").strip()
            if name:
                table_names.add(name)

        # ---- relationships dedupe ----
        # key includes cols mapping to avoid dupes while still allowing multiple distinct FKs
        seen_edges: set[Tuple[str, str, Tuple[str, ...], Tuple[str, ...]]] = set()

        lines: List[str] = ["erDiagram"]

        # ---- entities ----
        for t in sorted(table_names):
            lines.append(f"  {_m_id(t)} {{")
            lines.append("  }")

        # ---- relations ----
        for fk in fks:
            src = (fk.get("table") or "").strip()
            dst = (fk.get("referred_table") or "").strip()
            if not src or not dst:
                continue

            src_cols = tuple((fk.get("constrained_columns") or []) or [])
            dst_cols = tuple((fk.get("referred_columns") or []) or [])

            edge_key = (src, dst, src_cols, dst_cols)
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)

            # optional label
            label = "FK"
            if src_cols and dst_cols:
                label = f"{', '.join(src_cols)} -> {', '.join(dst_cols)}"
                label = _m_label(label)

            # child }o--|| parent : ...
            lines.append(f"  {_m_id(src)} }}o--|| {_m_id(dst)} : {label}")

        return {"mermaid": "\n".join(lines)}
    except Exception as exc:
        return {"error": f"mermaid build failed: {exc}", "mermaid": None}


def _m_id(name: str) -> str:
    # Mermaid ER identifier must be simple; normalize schema.table -> schema_table
    s = name.replace(".", "_")
    s = re.sub(r"[^A-Za-z0-9_]", "_", s)
    if not s or not (s[0].isalpha() or s[0] == "_"):
        s = "_" + s
    return s


def _m_label(text: str) -> str:
    return re.sub(r"[\r\n:]", " ", text).strip()
