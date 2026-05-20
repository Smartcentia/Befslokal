"""Kuratert SSB-tabelliste (barnevern/familievern)."""

from app.services.external.ssb_curated_tables import (
    filter_curated_items,
    filter_items_by_category,
    page_curated_tables,
)


def test_filter_curated_by_label():
    items = [
        {"id": "1", "label": "Foo barnevern statistikk", "sourceQuery": "barnevern", "variableNames": []},
        {"id": "2", "label": "Helt annet tema", "sourceQuery": "x", "variableNames": []},
    ]
    got = filter_curated_items(items, "barnevern")
    assert len(got) == 1
    assert got[0]["id"] == "1"


def test_filter_curated_by_table_id():
    items = [{"id": "14565", "label": "X", "sourceQuery": "barnevern", "variableNames": []}]
    got = filter_curated_items(items, "14565")
    assert len(got) == 1


def test_filter_by_category():
    items = [
        {"id": "1", "label": "KOSTRA barnevern", "categories": ["kostra", "tiltak"], "variableNames": []},
        {"id": "2", "label": "Kun melding", "categories": ["melding"], "variableNames": []},
    ]
    assert len(filter_items_by_category(items, "kostra")) == 1
    assert len(filter_items_by_category(items, "melding")) == 1
    assert len(filter_items_by_category(items, None)) == 2


def test_page_curated_sorts_and_slices():
    items = [
        {"id": "b", "label": "B", "sourceQuery": "familievern", "variableNames": []},
        {"id": "a", "label": "A", "sourceQuery": "barnevern", "variableNames": []},
    ]
    out = page_curated_tables(items, page=1, page_size=1, lang="no")
    assert out["page"]["totalElements"] == 2
    assert out["page"]["totalPages"] == 2
    assert out["tables"][0]["id"] == "a"
    assert out["tables"][0]["paths"][0][0]["label"] == "Barnevern og familievern"
