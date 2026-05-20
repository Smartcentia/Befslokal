from app.services.external.ssb_table_taxonomy import CATEGORY_ORDER, classify_ssb_table


def test_10674_is_melding():
    cats = classify_ssb_table(
        "10674: Meldingar til barnevernet, etter konklusjon",
        [],
        "10674",
    )
    assert "melding" in cats
    assert cats[0] == "melding"


def test_kostra_in_label():
    cats = classify_ssb_table("Netto driftsutgifter barnevern KOSTRA", [], "99999")
    assert "kostra" in cats
    assert cats[0] == "kostra"


def test_category_order_stable():
    cats = classify_ssb_table(
        "KOSTRA og melding til barnevernet",
        [],
        "",
    )
    idx = {c: i for i, c in enumerate(cats)}
    assert idx["kostra"] < idx["melding"]
    for c in cats:
        assert c in CATEGORY_ORDER


def test_fallback_annet():
    cats = classify_ssb_table("Xyz ukjent", [], "")
    assert cats == ["annet"]


def test_neet_table_is_utenforskap():
    cats = classify_ssb_table(
        "13556: Kommunefordelt prioritert arbeidsstyrkestatus (inkl. NEET) for personer 15-29 år",
        ["prioritert arbeidsstyrkestatus"],
        "13556",
    )
    assert "utenforskap" in cats
    assert cats[0] == "utenforskap"
