"""
Cost Analysis Service - Kategoriserer og analyserer kostnader for eiendommer.

Skiller mellom:
1. Eiendomsrelaterte kostnader (direkte knyttet til bygget)
2. Driftskostnader (løpende utgifter for virksomheten i bygget)
3. Engangskostnader (investeringer, oppgraderinger)

Flaggrer også potensielle anomalier.
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# Kjente utleiere og identifikatorer for husleie-deteksjon
RENT_VENDORS: Set[str] = {"J&B Eiendom AS", "995407671", "Statsbygg"}


def is_rent_transaction(supplier_name: Optional[str], supplier_id: Optional[str] = None) -> bool:
    """
    Sjekker om en transaksjon er en husleie-betaling basert på leverandør.
    """
    if not supplier_name and not supplier_id:
        return False
        
    s_name = (supplier_name or "").lower()
    s_id = str(supplier_id or "")
    
    # Sjekk mot ORGNR / ID
    if s_id in RENT_VENDORS:
        return True
        
    # Sjekk mot navn (sub-string match)
    for vendor in RENT_VENDORS:
        if vendor.lower() in s_name:
            return True
            
    return False



class CostCategory(str, Enum):
    """Hovedkategorier for kostnader."""
    PROPERTY = "property"      # Eiendomsrelatert (husleie, fellesutgifter)
    OPERATIONS = "operations"  # Drift (renhold, vakthold, strøm)
    INVESTMENT = "investment"  # Investeringer (oppgraderinger, inventar)
    OTHER = "other"           # Andre kostnader


class CostFlag(str, Enum):
    """Flagg for potensielle problemer."""
    NORMAL = "normal"
    HIGH_RELATIVE_TO_RENT = "high_relative_to_rent"
    DUPLICATE_SUSPECTED = "duplicate_suspected"
    NEGATIVE_AMOUNT = "negative_amount"
    UNUSUALLY_HIGH = "unusually_high"
    MISSING_PROVIDER = "missing_provider"


# Mapping av utgiftstyper til kategorier
EXPENSE_CATEGORY_MAP = {
    # PROPERTY - Eiendomsrelaterte kostnader (bør være proporsjonale med husleie)
    "Leie lokaler andre utleiere": CostCategory.PROPERTY,
    "Leie lokaler fra Statsbygg": CostCategory.PROPERTY,
    "Husleie": CostCategory.PROPERTY,
    "Fellesutgifter andre utleiere": CostCategory.PROPERTY,
    "Fellesutgifter (BAD) Statsbygg": CostCategory.PROPERTY,
    "Fellesutgifter Statsbygg - indre vedlikehold": CostCategory.PROPERTY,
    "Fellesutgifter": CostCategory.PROPERTY,
    "Leie parkeringsplass": CostCategory.PROPERTY,
    "Leie av lager/naust/garsjer og lignende": CostCategory.PROPERTY,
    "Reparasjon og vedlikehold leide lokaler": CostCategory.PROPERTY,
    "Renovasjon, vann, avløp o.l.": CostCategory.PROPERTY,
    "Annen kostnad lokaler": CostCategory.PROPERTY,

    # OPERATIONS - Driftskostnader (løpende, varierer med aktivitet)
    "Strøm og oppvarming": CostCategory.OPERATIONS,
    "Renhold lokaler": CostCategory.OPERATIONS,
    "Vakthold lokaler": CostCategory.OPERATIONS,
    "Vaktmestertjenester": CostCategory.OPERATIONS,
    "Reparasjon og vedlikehold av anlegg, også serviceavtaler": CostCategory.OPERATIONS,

    # INVESTMENT - Engangskostnader/investeringer
    "Fast bygningsinventar over kr 50 000": CostCategory.INVESTMENT,
    "Fast bygningsinventar og påkostning, leide bygg": CostCategory.INVESTMENT,
    "Oppgradering og påkostning leide lokaler - under kr 50 000": CostCategory.INVESTMENT,
    "Ombygging/flytting lokaler": CostCategory.INVESTMENT,
    "Risikoavsetning - Hærverk, enetiltak/skjerming, etc.": CostCategory.INVESTMENT,

    # GL/Visma Innkjøpskategorier (engelsk) – importert via CSV Innkjøpskategorier-kolonne
    "CLEANING": CostCategory.OPERATIONS,
    "ENERGY": CostCategory.OPERATIONS,
    "JANITOR": CostCategory.OPERATIONS,
    "MAINTENANCE": CostCategory.OPERATIONS,
    "SECURITY": CostCategory.OPERATIONS,
    "CARETAKER": CostCategory.OPERATIONS,
    "WASTE": CostCategory.OPERATIONS,
    "WATER": CostCategory.OPERATIONS,
    "RENT": CostCategory.PROPERTY,
    "UTILITIES": CostCategory.PROPERTY,
    "FACILITY": CostCategory.PROPERTY,
    "COMMON_COSTS": CostCategory.PROPERTY,
    "PARKING": CostCategory.PROPERTY,
    "INVESTMENT": CostCategory.INVESTMENT,
    "RENOVATION": CostCategory.INVESTMENT,
    "UPGRADE": CostCategory.INVESTMENT,
}

# Forventede forhold mellom kostnader og husleie (basert på bransjestandard)
EXPECTED_RATIOS = {
    CostCategory.PROPERTY: {
        "min": 0.8,   # Fellesutgifter bør være minimum 80% av husleie
        "max": 2.0,   # Men ikke mer enn 200%
        "typical": 1.2  # Typisk rundt 120%
    },
    CostCategory.OPERATIONS: {
        "min": 0.05,  # Drift bør være minimum 5% av husleie
        "max": 0.5,   # Men ikke mer enn 50%
        "typical": 0.15  # Typisk rundt 15%
    },
    CostCategory.INVESTMENT: {
        "min": 0.0,   # Kan være 0
        "max": 1.0,   # Bør ikke overstige 100% av husleie per år
        "typical": 0.1  # Typisk rundt 10%
    }
}


@dataclass
class AnalyzedExpense:
    """En analysert utgift med kategorisering og flagg."""
    type: str
    provider: str
    amount: float
    category: CostCategory
    flags: List[CostFlag]
    notes: List[str]
    source: Optional[str] = None


@dataclass
class CostAnalysisResult:
    """Resultat av kostnadsanalyse for en eiendom."""
    property_id: str
    property_name: str
    annual_rent: float

    # Aggregerte tall per kategori
    property_costs: float
    operations_costs: float
    investment_costs: float
    other_costs: float
    total_costs: float

    # Forhold til husleie
    property_ratio: float
    operations_ratio: float
    investment_ratio: float
    total_ratio: float

    # Vurdering
    overall_assessment: str
    flags: List[Dict[str, Any]]

    # Detaljert breakdown
    expenses_by_category: Dict[str, List[Dict[str, Any]]]

    # Anomalier
    anomalies: List[Dict[str, Any]]

    # Duplikater
    suspected_duplicates: List[Dict[str, Any]]


def categorize_expense(expense_type: str, account: str = None) -> CostCategory:
    """Kategoriser en utgiftstype. Prøver 'type' først, deretter 'account' som fallback."""
    cat = EXPENSE_CATEGORY_MAP.get(expense_type)
    if cat is None and account:
        cat = EXPENSE_CATEGORY_MAP.get(account)
    return cat or CostCategory.OTHER


def _parse_year_from_date(date_val: Any) -> Optional[int]:
    """
    Hent år fra utgiftens date-felt. Støtter f.eks. '2024-01-01', '2026-Q1', '2024'.
    Returnerer None hvis ikke parsebar.
    """
    if date_val is None:
        return None
    s = str(date_val).strip()
    if not s:
        return None
    # "2024-01-01" eller "2024"
    if len(s) >= 4 and s[:4].isdigit():
        try:
            return int(s[:4])
        except ValueError:
            pass
    # "2026-Q1" -> 2026
    if "-Q" in s:
        part = s.split("-Q")[0].strip()
        if part.isdigit():
            try:
                return int(part)
            except ValueError:
                pass
    # "01.01.2024"
    if "." in s:
        parts = s.split(".")
        if len(parts) >= 3 and parts[-1].isdigit():
            try:
                return int(parts[-1])
            except ValueError:
                pass
    return None


def aggregate_consumption_by_year(
    property_data: Dict,
    years: Optional[List[int]] = None
) -> Dict[int, Dict[str, float]]:
    """
    Aggreger forbruk (manual_expenses) per år ut fra date-feltet.

    Returnerer { year: { "total", "property", "operations", "investment", "other" } }
    for hvert år i years (default 2024, 2025, 2026). Utgifter uten gyldig date
    telles inn i første år i listen.
    """
    if years is None:
        years = [2024, 2025, 2026]
    financials = property_data.get("external_data", {}).get("financials", {})
    expenses = financials.get("manual_expenses", [])
    # Initialiser per år
    by_year: Dict[int, Dict[str, float]] = {}
    for y in years:
        by_year[y] = {
            "total": 0.0,
            "property": 0.0,
            "operations": 0.0,
            "investment": 0.0,
            "other": 0.0,
        }
    fallback_year = years[0] if years else 2024
    for exp in expenses:
        amount = float(exp.get("amount", 0) or 0)
        exp_type = exp.get("type", "Annet")
        category = categorize_expense(exp_type)
        cat_key = category.value
        year = _parse_year_from_date(exp.get("date"))
        if year not in by_year:
            year = fallback_year
        by_year[year]["total"] += amount
        by_year[year][cat_key] += amount
    return by_year


def detect_duplicates(expenses: List[Dict]) -> List[Dict]:
    """Finn potensielle duplikater basert på beløp og leverandør."""
    from collections import defaultdict

    # Grupper etter provider + amount
    groups = defaultdict(list)
    for i, exp in enumerate(expenses):
        key = (exp.get("provider", "").lower(), round(exp.get("amount", 0), 2))
        groups[key].append((i, exp))

    duplicates = []
    for key, items in groups.items():
        if len(items) > 2:  # Mer enn 2 like poster er mistenkelig
            duplicates.append({
                "provider": key[0],
                "amount": key[1],
                "count": len(items),
                "indices": [i for i, _ in items],
                "total": key[1] * len(items)
            })

    return duplicates


def analyze_property_costs(
    property_data: Dict,
    annual_rent: float = 0.0
) -> CostAnalysisResult:
    """
    Analyserer kostnader for en eiendom.

    Args:
        property_data: Eiendomsdata inkludert external_data med financials
        annual_rent: Årlig husleie fra kontrakt(er)

    Returns:
        CostAnalysisResult med full analyse

    Note:
        - Ved annual_rent=0 settes alle ratioer til 0 (unngår deling på null).
        - total_costs summerer ALLE manual_expenses uten årfiltrering; annual_rent
          er per år. Ratioene gir kun mening når begge er sammenlignbare (per år).
          Flerårige utgifter gir systematisk for høye ratioer.
    """
    property_id = str(property_data.get("property_id", ""))
    property_name = property_data.get("name", "Ukjent")

    financials = property_data.get("external_data", {}).get("financials", {})
    expenses = financials.get("manual_expenses", [])

    # Initialiser kategorier
    by_category = {
        CostCategory.PROPERTY: [],
        CostCategory.OPERATIONS: [],
        CostCategory.INVESTMENT: [],
        CostCategory.OTHER: []
    }

    category_totals = {
        CostCategory.PROPERTY: 0.0,
        CostCategory.OPERATIONS: 0.0,
        CostCategory.INVESTMENT: 0.0,
        CostCategory.OTHER: 0.0
    }

    anomalies = []
    all_flags = []

    # Analyser hver utgift
    for exp in expenses:
        exp_type = exp.get("type", "Annet")
        account = exp.get("account")
        provider = exp.get("provider", "Ukjent")
        amount = exp.get("amount", 0.0)
        source = exp.get("source", "")

        # Prøv type-feltet først, deretter account som fallback (GL-kategorier)
        category = categorize_expense(exp_type, account)
        flags = []
        notes = []

        # Sjekk for flagg
        if amount < 0:
            flags.append(CostFlag.NEGATIVE_AMOUNT)
            notes.append("Negativt beløp - kan være kreditnota eller korrigering")

        if provider in ["Ukjent", "", None]:
            flags.append(CostFlag.MISSING_PROVIDER)
            notes.append("Mangler leverandørinformasjon")

        # Uvanlig høye enkeltposter (over 500k)
        if amount > 500000:
            flags.append(CostFlag.UNUSUALLY_HIGH)
            notes.append(f"Uvanlig høy enkeltpost: {amount:,.0f} kr")
            anomalies.append({
                "type": exp_type,
                "provider": provider,
                "amount": amount,
                "reason": "Enkeltpost over 500 000 kr"
            })

        # Legg til i kategori
        analyzed = {
            "type": exp_type,
            "provider": provider,
            "amount": amount,
            "category": category.value,
            "flags": [f.value for f in flags],
            "notes": notes,
            "source": source
        }

        by_category[category].append(analyzed)
        category_totals[category] += amount

        if flags:
            all_flags.append({
                "expense": exp_type,
                "provider": provider,
                "amount": amount,
                "flags": [f.value for f in flags]
            })

    # Beregn totaler
    total_costs = sum(category_totals.values())

    # Beregn forhold til husleie
    if annual_rent > 0:
        property_ratio = category_totals[CostCategory.PROPERTY] / annual_rent
        operations_ratio = category_totals[CostCategory.OPERATIONS] / annual_rent
        investment_ratio = category_totals[CostCategory.INVESTMENT] / annual_rent
        total_ratio = total_costs / annual_rent
    else:
        property_ratio = operations_ratio = investment_ratio = total_ratio = 0.0

    # Finn duplikater
    duplicates = detect_duplicates(expenses)

    # Vurder forhold til forventede verdier
    assessment_notes = []

    if annual_rent > 0:
        # Sjekk eiendomskostnader
        if property_ratio > EXPECTED_RATIOS[CostCategory.PROPERTY]["max"]:
            assessment_notes.append(
                f"Eiendomskostnader ({property_ratio:.0%}) er høyere enn forventet (maks {EXPECTED_RATIOS[CostCategory.PROPERTY]['max']:.0%})"
            )
        elif property_ratio < EXPECTED_RATIOS[CostCategory.PROPERTY]["min"] and total_costs > 0:
             assessment_notes.append(
                f"Eiendomskostnader ({property_ratio:.0%}) er lavere enn forventet (min {EXPECTED_RATIOS[CostCategory.PROPERTY]['min']:.0%})"
            )

        # Sjekk driftskostnader
        if operations_ratio > EXPECTED_RATIOS[CostCategory.OPERATIONS]["max"]:
            assessment_notes.append(
                f"Driftskostnader ({operations_ratio:.0%}) er høyere enn forventet (maks {EXPECTED_RATIOS[CostCategory.OPERATIONS]['max']:.0%})"
            )

        # Sjekk investeringer
        if investment_ratio > EXPECTED_RATIOS[CostCategory.INVESTMENT]["max"]:
            assessment_notes.append(
                f"Investeringskostnader ({investment_ratio:.0%}) er høyere enn forventet (maks {EXPECTED_RATIOS[CostCategory.INVESTMENT]['max']:.0%})"
            )

        # Total vurdering
        if total_costs == 0:
            if expenses:
                overall = "ADVARSEL: Netto kostnader er 0 kr, men det finnes poster som utligner hverandre"
                assessment_notes.append("Inneholder sannsynligvis korrigeringer eller motposter")
            else:
                overall = "MANGLER DATA: Ingen kostnader registrert for denne eiendommen"
                assessment_notes.append("Vurdering kan ikke gjennomføres uten regnskapsdata")
        elif total_ratio > 3.0:
            overall = "KRITISK: Totale kostnader er over 3x husleie"
        elif total_ratio > 2.0:
            overall = "HØY: Totale kostnader er over 2x husleie"
        elif total_ratio > 1.5:
            overall = "MODERAT: Totale kostnader er over 1.5x husleie"
        else:
            overall = "NORMAL: Kostnader er innenfor forventet nivå"
    else:
        overall = "UKJENT: Mangler husleiedata for sammenligning"
        assessment_notes.append("Kan ikke vurdere uten husleiedata")

    if assessment_notes:
        overall += "\n" + "\n".join(f"- {note}" for note in assessment_notes)

    if duplicates:
        overall += f"\n- {len(duplicates)} potensielle duplikatgrupper funnet"

    return CostAnalysisResult(
        property_id=property_id,
        property_name=property_name,
        annual_rent=annual_rent,
        property_costs=category_totals[CostCategory.PROPERTY],
        operations_costs=category_totals[CostCategory.OPERATIONS],
        investment_costs=category_totals[CostCategory.INVESTMENT],
        other_costs=category_totals[CostCategory.OTHER],
        total_costs=total_costs,
        property_ratio=property_ratio,
        operations_ratio=operations_ratio,
        investment_ratio=investment_ratio,
        total_ratio=total_ratio,
        overall_assessment=overall,
        flags=all_flags,
        expenses_by_category={
            "property": by_category[CostCategory.PROPERTY],
            "operations": by_category[CostCategory.OPERATIONS],
            "investment": by_category[CostCategory.INVESTMENT],
            "other": by_category[CostCategory.OTHER]
        },
        anomalies=anomalies,
        suspected_duplicates=duplicates
    )


async def get_property_cost_analysis(db, property_id: str, year: Optional[int] = None) -> Optional[Dict]:
    """
    Henter kostnadsanalyse for en spesifikk eiendom.
    """
    from sqlalchemy import text

    # Hent eiendomsdata
    result = await db.execute(text("""
        SELECT
            p.property_id,
            p.name,
            p.external_data,
            COALESCE(SUM(
                COALESCE(
                    (c.amount->>'total_per_year')::float,
                    (c.amount->>'amount_per_year')::float,
                    (c.amount->>'monthly_rent')::float * 12,
                    0
                )
            ), 0) as annual_rent
        FROM properties p
        LEFT JOIN units u ON u.property_id = p.property_id
        LEFT JOIN contracts c ON c.unit_id = u.unit_id AND c.status = 'active'
        WHERE p.property_id = :property_id
        GROUP BY p.property_id, p.name, p.external_data
    """), {"property_id": property_id})

    row = result.fetchone()
    if not row:
        return None

    property_data = {
        "property_id": str(row[0]),
        "name": row[1],
        "external_data": row[2] or {}
    }
    annual_rent = row[3] or 0.0

    # Bruk syntetisk estimat (rent_summary) som fallback når ingen kontrakter
    synthetic_rent = False
    if annual_rent <= 0:
        ext = property_data.get("external_data") or {}
        fin = ext.get("financials") or {}
        rent_summary = fin.get("rent_summary")
        if rent_summary is not None:
            try:
                annual_rent = float(rent_summary)
                synthetic_rent = annual_rent > 0
            except (TypeError, ValueError):
                pass

    # ── Hent data fra økonomiavdelingens regnskap 2026 (finance_dept_2026) ──────
    # GL-transaksjoner brukes ikke lenger. Eneste kilde er finance_budget.
    try:
        fin_rows = (await db.execute(text("""
            SELECT category, konto_navn, SUM(amount) AS total
            FROM finance_budget
            WHERE property_id = :property_id
              AND year = 2026
              AND data_source = 'finance_dept_2026'
            GROUP BY category, konto_navn
            HAVING SUM(amount) > 0
            ORDER BY total DESC
        """), {"property_id": property_id})).all()

        _CAT_MAP = {"lokaler": "property", "drift": "operations", "vedlikehold": "investment"}
        fin_totals: Dict[str, float] = {"property": 0.0, "operations": 0.0, "investment": 0.0, "other": 0.0}
        fin_by_category: Dict[str, List[Dict]] = {"property": [], "operations": [], "investment": [], "other": []}

        for r in fin_rows:
            cat_key = _CAT_MAP.get((r.category or "").lower(), "other")
            amt = float(r.total or 0)
            fin_totals[cat_key] += amt
            fin_by_category[cat_key].append({
                "type": r.category or "Annet",
                "provider": r.konto_navn or "Ukjent",
                "description": r.konto_navn or "",
                "amount": amt,
                "source": "finance_dept_2026",
                "flags": [],
                "notes": [],
            })

        fin_total_all = sum(fin_totals.values())
        total_ratio = fin_total_all / annual_rent if annual_rent > 0 else 0.0

        if annual_rent <= 0:
            assessment = "UKJENT: Mangler husleiedata for sammenligning"
        elif total_ratio > 3.0:
            assessment = "KRITISK: Totale kostnader er over 3x husleie"
        elif total_ratio > 2.0:
            assessment = "HØY: Totale kostnader er over 2x husleie"
        elif total_ratio > 1.5:
            assessment = "MODERAT: Totale kostnader er over 1.5x husleie"
        else:
            assessment = "NORMAL: Kostnader er innenfor forventet nivå"

        prop_name = property_data.get("name") if isinstance(property_data, dict) else (property_data[1] if property_data else property_id)

        return {
            "property_id": property_id,
            "property_name": prop_name,
            "annual_rent": annual_rent,
            "synthetic_rent": synthetic_rent,
            "summary": {
                "property_costs": fin_totals["property"],
                "operations_costs": fin_totals["operations"],
                "investment_costs": fin_totals["investment"],
                "other_costs": fin_totals["other"],
                "total_costs": fin_total_all,
            },
            "ratios": {
                "property_ratio": fin_totals["property"] / annual_rent if annual_rent > 0 else 0.0,
                "operations_ratio": fin_totals["operations"] / annual_rent if annual_rent > 0 else 0.0,
                "investment_ratio": fin_totals["investment"] / annual_rent if annual_rent > 0 else 0.0,
                "total_ratio": total_ratio,
            },
            "assessment": assessment,
            "flags": [],
            "expenses_by_category": fin_by_category,
            "anomalies": [],
            "suspected_duplicates": [],
            "year": 2026,
            "data_source": "finance_dept_2026",
        }
    except Exception as exc:
        logger.warning("cost_analysis: finance_dept_2026 feil for %s: %s", property_id, exc)

    # Fallback: tom respons dersom finance_dept_2026 feiler
    return {
        "property_id": property_id,
        "property_name": property_id,
        "annual_rent": annual_rent,
        "synthetic_rent": synthetic_rent,
        "summary": {
            "property_costs": 0.0,
            "operations_costs": 0.0,
            "investment_costs": 0.0,
            "other_costs": 0.0,
            "total_costs": 0.0,
        },
        "ratios": {
            "property_ratio": 0.0,
            "operations_ratio": 0.0,
            "investment_ratio": 0.0,
            "total_ratio": 0.0,
        },
        "assessment": "UKJENT: Kunne ikke hente økonomidata",
        "flags": [],
        "expenses_by_category": {"property": [], "operations": [], "investment": [], "other": []},
        "anomalies": [],
        "suspected_duplicates": [],
        "year": 2026,
        "data_source": "finance_dept_2026",
    }
