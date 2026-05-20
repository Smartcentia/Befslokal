"""Tester for schema_graph (Inspector-basert relasjonskart)."""

from unittest.mock import MagicMock

from app.services.governance.schema_graph import build_schema_graph, to_mermaid_er


def _make_inspector(table_names, fk_by_table: dict):
    insp = MagicMock()
    insp.get_table_names.return_value = table_names

    def _fks(table):
        return fk_by_table.get(table, [])

    insp.get_foreign_keys.side_effect = _fks
    return insp


def test_build_schema_graph_collects_fks_and_tables():
    insp = _make_inspector(
        ["contracts", "properties", "units"],
        {
            "units": [
                {
                    "name": "fk_units_property",
                    "constrained_columns": ["property_id"],
                    "referred_table": "properties",
                    "referred_columns": ["property_id"],
                }
            ],
            "contracts": [
                {
                    "name": "fk_contracts_unit",
                    "constrained_columns": ["unit_id"],
                    "referred_table": "units",
                    "referred_columns": ["unit_id"],
                }
            ],
            "properties": [],
        },
    )
    g = build_schema_graph(insp)
    assert g["tables"] == ["contracts", "properties", "units"]
    assert len(g["foreign_keys"]) == 2
    fk_units = next(f for f in g["foreign_keys"] if f["from_table"] == "units")
    assert fk_units["to_table"] == "properties"
    assert fk_units["from_columns"] == ["property_id"]


def test_build_schema_graph_skips_alembic_version():
    insp = _make_inspector(
        ["alembic_version", "properties"],
        {"properties": []},
    )
    g = build_schema_graph(insp)
    assert g["tables"] == ["properties"]
    assert g["foreign_keys"] == []


def test_build_schema_graph_skips_fk_to_skipped_table():
    insp = _make_inspector(
        ["child"],
        {
            "child": [
                {
                    "name": "fk_to_alembic",
                    "constrained_columns": ["v"],
                    "referred_table": "alembic_version",
                    "referred_columns": ["version_num"],
                }
            ],
        },
    )
    g = build_schema_graph(insp)
    assert g["foreign_keys"] == []


def test_to_mermaid_er_contains_relationship_and_entities():
    g = {
        "tables": ["units", "properties"],
        "foreign_keys": [
            {
                "from_table": "units",
                "from_columns": ["property_id"],
                "to_table": "properties",
                "to_columns": ["property_id"],
                "name": "fk_u_p",
            }
        ],
    }
    m = to_mermaid_er(g)
    assert "erDiagram" in m
    assert "units" in m
    assert "properties" in m
    assert "}o--||" in m
    assert "property_id" in m
