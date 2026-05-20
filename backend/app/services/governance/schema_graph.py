"""Bygg database-relasjonsgraf fra SQLAlchemy Inspector (PostgreSQL FK-constraints)."""

from __future__ import annotations

import re
from typing import Any, Dict, List

# Tabeller som ikke skal inkluderes i kartet (støy / migreringsmetadata).
SKIP_TABLES = frozenset({"alembic_version", "spatial_ref_sys"})

# Mermaid entity: tillat bokstaver, tall, underscore; ellers bruk anførselstegn.
_MERMAID_SAFE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _mermaid_entity(table: str) -> str:
    if _MERMAID_SAFE.match(table):
        return table
    escaped = table.replace('"', '\\"')
    return f'"{escaped}"'


def build_schema_graph(inspector: Any) -> Dict[str, Any]:
    """
    Returnerer tabeller og fremmednøkler fra faktisk DB-skjema.

    Args:
        inspector: sqlalchemy.engine.reflection.Inspector

    Returns:
        dict med nøklene ``tables`` (sortert liste) og ``foreign_keys`` (liste av dicts).
    """
    raw_names = [t for t in inspector.get_table_names() if t not in SKIP_TABLES]
    tables_set: set[str] = set(raw_names)
    foreign_keys: List[Dict[str, Any]] = []

    for from_table in sorted(raw_names):
        for fk in inspector.get_foreign_keys(from_table):
            to_table = fk["referred_table"]
            if to_table in SKIP_TABLES:
                continue
            tables_set.add(to_table)
            foreign_keys.append(
                {
                    "from_table": from_table,
                    "from_columns": list(fk["constrained_columns"]),
                    "to_table": to_table,
                    "to_columns": list(fk["referred_columns"]),
                    "name": fk.get("name"),
                }
            )

    return {
        "tables": sorted(tables_set),
        "foreign_keys": foreign_keys,
    }


def to_mermaid_er(graph: Dict[str, Any]) -> str:
    """
    Generer én Mermaid ``erDiagram``-blokk: tom enhetsblokk per tabell + FK-relasjoner.

    Barn (fra_table) M:N..1 mot forelder (to_table): ``}o--||``.
    """
    tables: List[str] = graph["tables"]
    foreign_keys: List[Dict[str, Any]] = graph["foreign_keys"]

    lines: List[str] = ["erDiagram"]

    for t in tables:
        ent = _mermaid_entity(t)
        lines.append(f"    {ent} {{" + " }")

    for fk in foreign_keys:
        left = _mermaid_entity(fk["from_table"])
        right = _mermaid_entity(fk["to_table"])
        fc = ",".join(fk["from_columns"])
        tc = ",".join(fk["to_columns"])
        label = f"{fc} → {tc}"
        if len(label) > 120:
            label = label[:117] + "..."
        label = label.replace('"', "'")
        lines.append(f'    {left} }}o--|| {right} : "{label}"')

    return "\n".join(lines)
