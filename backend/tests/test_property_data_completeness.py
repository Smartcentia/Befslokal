"""Enhetstester for property_data_completeness (uten DB for norm_id)."""
import pytest

from app.services.financials.property_data_completeness import norm_id


@pytest.mark.parametrize(
    "raw,expected",
    [
        (None, None),
        ("", None),
        ("  ", None),
        ("1234", "1234"),
        ("1234.0", "1234"),
        ("12-34.0", "12-34"),
    ],
)
def test_norm_id(raw, expected):
    assert norm_id(raw) == expected
