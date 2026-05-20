"""
beregn_budsjett_2027.py — Transparent, logikkbasert budsjettestimat for 2027.

Bruk:
    python beregn_budsjett_2027.py input.csv
    python beregn_budsjett_2027.py input.csv --vekst 0.05 --fallback 1500000 --output budsjett_2027.csv

Logikk per rad (prioritert rekkefølge):
    1. AVVIKLES / STENGES i eiendomsnavn → 0
    2. 2025-tall mangler eller <= 0    → fallback (regional median eller flat verdi)
    3. Standard vekstmodell            → 2025 * (1 + vekst_rate)
    4. Cap                             → maks 50 % økning fra 2025

Fallback-valg er automatisk:
    - Regional median brukes hvis regionen har >= 8 observasjoner OG cv (std/median) <= 0.5
    - Ellers brukes flat fallback-verdi (default: 1 500 000)
"""

import argparse
import sys
import pandas as pd


AVVIKLES_NOKKELORD = ("AVVIKLES", "STENGES", "NEDLEGGES")


def les_og_rens(fil: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(fil, sep=";", skiprows=1, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(fil, sep=";", skiprows=1, encoding="latin-1")

    if "2025 faktisk (GL)" not in df.columns:
        sys.exit(
            f"Feil: Kolonnen '2025 faktisk (GL)' finnes ikke i {fil}.\n"
            f"Kolonner funnet: {list(df.columns)}"
        )

    df["2025 faktisk (GL)"] = (
        df["2025 faktisk (GL)"]
        .astype(str)
        .str.replace("\xa0", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    df["2025 faktisk (GL)"] = pd.to_numeric(df["2025 faktisk (GL)"], errors="coerce").fillna(0)

    if "Region" not in df.columns:
        df["Region"] = "Ukjent"
    df["Region"] = df["Region"].fillna("Ukjent").astype(str)

    if "Eiendom" not in df.columns:
        df["Eiendom"] = ""
    df["Eiendom"] = df["Eiendom"].fillna("").astype(str)

    return df


def bygg_fallback_kart(df: pd.DataFrame, flat_fallback: float) -> dict:
    """
    Returnerer {region: (fallback_verdi, metode_navn)} for alle regioner.
    Bruker regional median hvis gruppen er stabil nok, ellers flat_fallback.
    """
    kart = {}
    stats = (
        df[df["2025 faktisk (GL)"] > 0]
        .groupby("Region")["2025 faktisk (GL)"]
        .agg(["count", "median", "std"])
        .rename(columns={"count": "n", "median": "median", "std": "std"})
    )

    print("\n--- Gruppestatistikk for fallback-valg ---")
    print(f"{'Region':<30} {'N':>5} {'Median':>12} {'CV':>8} {'Fallback'}")
    print("-" * 70)

    for region, row in stats.iterrows():
        n = row["n"]
        median = row["median"]
        std = row["std"] if pd.notna(row["std"]) else 0
        cv = (std / median) if median > 0 else float("inf")

        if n >= 8 and cv <= 0.5:
            kart[region] = (median, "fallback_median")
            metode_label = f"median ({median:,.0f})"
        else:
            kart[region] = (flat_fallback, "fallback_flat")
            metode_label = f"flat ({flat_fallback:,.0f})"

        print(f"{region:<30} {n:>5} {median:>12,.0f} {cv:>8.2f}   {metode_label}")

    print("-" * 70)
    print()
    return kart


def beregn_rad(
    row: pd.Series,
    fallback_kart: dict,
    vekst_rate: float,
    flat_fallback: float,
) -> tuple:
    navn = row["Eiendom"].upper()
    faktisk = row["2025 faktisk (GL)"]
    region = row["Region"]

    # 1. Avvikles/stenges
    if any(k in navn for k in AVVIKLES_NOKKELORD):
        return 0.0, "avvikles"

    # 2. Manglende historikk
    if faktisk <= 0:
        fallback_verdi, fallback_metode = fallback_kart.get(
            region, (flat_fallback, "fallback_flat")
        )
        return fallback_verdi, fallback_metode

    # 3. Standard vekst + cap
    pred = faktisk * (1 + vekst_rate)
    cap = faktisk * 1.5
    return min(pred, cap), "vekst"


def main():
    parser = argparse.ArgumentParser(description="Beregn budsjett 2027 fra GL-data")
    parser.add_argument("input", help="Sti til input CSV-fil")
    parser.add_argument("--vekst", type=float, default=0.05, help="Vekstrate (default: 0.05 = 5%%)")
    parser.add_argument("--fallback", type=float, default=1_500_000, help="Flat fallback-verdi (default: 1500000)")
    parser.add_argument("--output", default="budsjett_2027.csv", help="Sti til output CSV-fil")
    args = parser.parse_args()

    print(f"Leser: {args.input}")
    df = les_og_rens(args.input)
    print(f"  {len(df)} rader lastet")

    fallback_kart = bygg_fallback_kart(df, args.fallback)

    resultater = [
        beregn_rad(row, fallback_kart, args.vekst, args.fallback)
        for _, row in df.iterrows()
    ]
    df["Budsjett_2027"] = [r[0] for r in resultater]
    df["Metode"] = [r[1] for r in resultater]

    # Oppsummering
    metode_teller = df["Metode"].value_counts()
    print("--- Oppsummering ---")
    for metode, antall in metode_teller.items():
        print(f"  {metode:<20} {antall:>5} rader")
    total = df["Budsjett_2027"].sum()
    print(f"\n  Totalt budsjett 2027: {total:>15,.0f} kr")
    print()

    ut = df[["Eiendom", "Region", "2025 faktisk (GL)", "Budsjett_2027", "Metode"]]
    ut.to_csv(args.output, index=False, sep=";")
    print(f"Lagret: {args.output}")


if __name__ == "__main__":
    main()
