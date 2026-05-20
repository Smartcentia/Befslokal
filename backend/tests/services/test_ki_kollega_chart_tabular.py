"""Tester for SQL→diagram-tabular og utvalg av siste chart fra script_results."""

from __future__ import annotations

import pytest

from app.services.intelligence.ki_kollega.sql_chart_tabular import (
    pick_last_chart_from_script_results,
    sql_rows_to_chart_tabular,
)


def test_sql_rows_to_chart_tabular_region_and_amount() -> None:
    cols = ["region", "total_kr"]
    rows = [
        {"region": "Vest", "total_kr": 1000},
        {"region": "Øst", "total_kr": 2000},
    ]
    tab = sql_rows_to_chart_tabular(cols, rows)
    assert tab is not None
    assert tab["valueKey"] == "total_kr"
    assert "region" in tab["dimensionKeys"]
    assert len(tab["rows"]) == 2


def test_sql_rows_to_chart_tabular_no_numeric_returns_none() -> None:
    cols = ["navn", "beskrivelse"]
    rows = [{"navn": "A", "beskrivelse": "x"}]
    assert sql_rows_to_chart_tabular(cols, rows) is None


def test_pick_last_chart_wins_two_tools() -> None:
    sr = {
        "fetch_ssb_abc": {
            "chart": {
                "rows": [{"tid": "2020", "verdi": 1.0}],
                "dimensionKeys": ["tid"],
                "valueKey": "verdi",
                "role": None,
            }
        },
        "run_sql_xyz": {
            "chart": {
                "rows": [{"region": "X", "belop": 99.0}],
                "dimensionKeys": ["region"],
                "valueKey": "belop",
                "role": None,
            }
        },
    }
    out = pick_last_chart_from_script_results(sr)
    assert out is not None
    assert out["valueKey"] == "belop"
    assert out["rows"][0].get("region") == "X"


def test_pick_last_chart_single_ssb() -> None:
    sr = {
        "t1": {
            "chart": {
                "rows": [{"Tid": "2021", "verdi": 5.0}],
                "dimensionKeys": ["Tid"],
                "valueKey": "verdi",
                "role": {"time": ["Tid"]},
            }
        }
    }
    out = pick_last_chart_from_script_results(sr)
    assert out is not None
    assert out["valueKey"] == "verdi"
