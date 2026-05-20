"""
Kobler de 477 birk-enhetene (Barnevernsinstitusjon + Avdeling) til kostnadsdata
fra Eiendomsportfeb.csv og oppretter PropertyAnnualCost for hvert treff i DB.

Flyt:
  1. Match birk Barnevernsinstitusjon → portfeb-rad (navn/adresse)
  2. Avdelinger arver foreldreinstitusjonens portfeb-rad via TilhørighetEnhetID
  3. For hvert birk-treff: finn DB-property → upsert PropertyAnnualCost (år=2025)
"""
import sys, os, csv, re, uuid, requests
from collections import defaultdict

FINANS = "/Users/frank/Documents/BEFS_CLEAN/finans"
BIRK_FILE    = os.path.join(FINANS, "birk _og_plasser.csv")
PORTFEB_FILE = os.path.join(FINANS, "Eiendomsportfeb.csv")

SUPABASE_URL = "https://vwvhxcqxadblrftuvsds.supabase.co"
SERVICE_KEY  = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ3dmh4Y3F4YWRibHJmdHV2c2RzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTMzODUwMiwiZXhwIjoyMDg2OTE0NTAyfQ.h071E-xhKw1uPPuNzxtyv2a1oAXK1eJF8NXZ9EpMlWc"
HEADERS = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

YEAR = 2025


# ── helpers ──────────────────────────────────────────────────────────────────

def api_get(table, params):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}", headers=HEADERS, params=params)
    r.raise_for_status()
    return r.json()

def api_upsert(table, data):
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/{table}",
        headers={**HEADERS, "Prefer": "resolution=merge-duplicates,return=minimal"},
        json=data,
    )
    if not r.ok:
        raise RuntimeError(f"upsert {table}: {r.status_code} {r.text[:200]}")

def norm(s):
    if not s:
        return ""
    s = s.lower().strip()
    s = re.sub(r"[^\w\s]", " ", s)
    return " ".join(s.split())

def tokens(s):
    stop = {"og", "avd", "etg", "til", "postadresse", "postboks", "i", "for", "av"}
    return set(re.sub(r"[^\w\s]", " ", s.lower()).split()) - stop

def parse_float(val):
    if not val or not str(val).strip():
        return None
    v = str(val).strip().replace("\xa0", "").replace(" ", "").replace(",", ".")
    m = re.search(r"\d+\.?\d*", v)
    if m:
        try:
            result = float(m.group(0))
            return result if result != 0.0 else None
        except ValueError:
            pass
    return None

def cost_from_row(row):
    """Trekk ut kostnadsfelt fra en portfeb-rad."""
    kpi = parse_float(row.get("KPI-justert kontraktsleie til okt 2025"))
    imaint = parse_float(row.get("KPI-justert indre vedlikehold")) or parse_float(row.get("Indre vedlikehold"))
    return {
        "kpi_adjusted_rent":    kpi,
        "internal_maintenance": imaint,
        "common_costs":         parse_float(row.get("Felleskostnader per år (ved kontraktsinngåelse) ")),
        "energy_costs":         parse_float(row.get("Energi til leieobjektet kr per år")),
        "heating_costs":        parse_float(row.get("Oppvarming pr år")),
        "cleaning_costs":       parse_float(row.get("Renhold pr år")),
        "parking_rent":         parse_float(row.get("Parkeringsleie kr per år")),
        "caretaker_cost":       parse_float(row.get("Vaktmestertjenester kr per år")),
        "card_reader_cost":     parse_float(row.get("Kost kortleser")),
    }


# ── les birk ─────────────────────────────────────────────────────────────────

with open(BIRK_FILE, newline="", encoding="latin-1") as f:
    next(f)
    birk_all = [r for r in csv.DictReader(f) if r.get("Enhetsnavn", "").strip()]

birk_by_id  = {r["EnhetID"].strip(): r for r in birk_all if r.get("EnhetID", "").strip()}
avdelinger  = [r for r in birk_all if r.get("Enhetskorttype", "") == "Avdeling"]
institusjoner = [r for r in birk_all if r.get("Enhetskorttype", "") == "Barnevernsinstitusjon"]

# parent_id → list of avdelinger
avd_by_parent = defaultdict(list)
for a in avdelinger:
    pid = a.get("TilhørighetEnhetID", "").strip()
    if pid:
        avd_by_parent[pid].append(a)

print(f"Birk: {len(birk_all)} enheter  ({len(institusjoner)} inst + {len(avdelinger)} avd)")


# ── les portfeb ───────────────────────────────────────────────────────────────

portfeb_rows = []
for enc in ("utf-8-sig", "latin-1", "cp1252"):
    try:
        with open(PORTFEB_FILE, newline="", encoding=enc) as f:
            portfeb_rows = list(csv.DictReader(f))
        break
    except UnicodeDecodeError:
        continue

print(f"Portfeb: {len(portfeb_rows)} rader")


# ── match birk institusjon → portfeb ─────────────────────────────────────────

def best_portfeb_match(birk_row, portfeb_rows):
    navn = (birk_row.get("Enhetsnavn") or "").strip()
    adr  = (birk_row.get("Adresse") or "").strip()
    postnr = (birk_row.get("Postnummer") or "").strip()

    tb_navn = tokens(navn)
    tb_adr  = tokens(adr) if adr and not adr.lower().startswith("postboks") else set()

    best_score, best_row = 0, None

    for p in portfeb_rows:
        lok    = p.get("Lokalisering") or ""
        avtale = p.get("Avtalenavn") or ""
        p_adr  = (p.get("Adresselinje 1") or "") + " " + (p.get("Adresse og Postnummer ") or "")
        p_post = re.search(r"\b(\d{4})\b", p.get("Adresse og Postnummer ") or "")
        p_postnr = p_post.group(1) if p_post else ""

        # Navn-score
        for ref in (lok, avtale):
            tp = tokens(ref)
            overlap = tb_navn & tp
            meaningful = overlap - {"gate", "vei", "veien", "gata", "avd", "etg", "ungdomssenter"}
            score = len(meaningful) * 2 + (1 if any(t.isdigit() for t in overlap) else 0)
            if score > best_score:
                best_score, best_row = score, p

        # Adresse-score (kun hvis postnr stemmer eller begge er tomme)
        if tb_adr:
            if postnr and p_postnr and postnr != p_postnr:
                continue
            tp_adr = tokens(p_adr)
            ov = tb_adr & tp_adr
            me = ov - {"gate", "vei", "veien", "gata", "gaten"}
            score = len(me) * 2 + (2 if any(t.isdigit() for t in ov) else 0)
            if score > best_score:
                best_score, best_row = score, p

    return best_row if best_score >= 2 else None


# Finn match for alle institusjoner
inst_to_portfeb = {}
no_portfeb_match = []
for inst in institusjoner:
    eid = inst.get("EnhetID", "").strip()
    match = best_portfeb_match(inst, portfeb_rows)
    if match:
        inst_to_portfeb[eid] = match
    else:
        no_portfeb_match.append(inst)

print(f"\nInstitusjoner matchet mot portfeb: {len(inst_to_portfeb)} / {len(institusjoner)}")
print(f"Uten portfeb-match: {len(no_portfeb_match)}")


# ── hent alle DB-properties (Barnevernsinstitusjon + Avdeling) ────────────────

resp = api_get("properties", {
    "select": "property_id,name,lokalisering_id,unit_short_type",
    "unit_short_type": "in.(Barnevernsinstitusjon,Avdeling)",
    "limit": "1000",
})
db_props = resp
db_by_lok6 = {p["lokalisering_id"]: p for p in db_props
              if p.get("lokalisering_id") and len(str(p["lokalisering_id"])) == 6}
db_by_name = {}
for p in db_props:
    key = re.sub(r"[^a-z0-9]", "", (p.get("name") or "").lower())
    db_by_name[key] = p

print(f"DB formålsbygg: {len(db_props)}  ({len(db_by_lok6)} med 6-sifret kode)")


# ── finn DB-property for en birk-rad ─────────────────────────────────────────

def find_db_property(birk_row):
    lok = (birk_row.get("Lokasjonskode") or "").strip()
    if lok and lok in db_by_lok6:
        return db_by_lok6[lok]
    key = re.sub(r"[^a-z0-9]", "", (birk_row.get("Enhetsnavn") or "").lower())
    return db_by_name.get(key)


# ── hent eksisterende cost-records (år=2025) for formålsbygg ─────────────────

existing_costs = {}
page = 0
while True:
    batch = api_get("property_annual_costs", {
        "select": "property_annual_cost_id,property_id",
        "year": "eq.2025",
        "limit": "1000",
        "offset": str(page * 1000),
    })
    for r in batch:
        existing_costs[r["property_id"]] = r["property_annual_cost_id"]
    if len(batch) < 1000:
        break
    page += 1

print(f"Eksisterende cost-records (2025): {len(existing_costs)}")


# ── upsert PropertyAnnualCost ─────────────────────────────────────────────────

def upsert_cost(property_id, portfeb_row, source_label):
    costs = cost_from_row(portfeb_row)
    lok = (portfeb_row.get("Lokalisering") or "").strip()

    record = {
        "property_id": property_id,
        "year": YEAR,
        **costs,
        "external_data": {
            "portfeb_lokalisering": lok,
            "portfeb_avtalenavn": portfeb_row.get("Avtalenavn", ""),
            "portfeb_adresse": portfeb_row.get("Adresselinje 1", ""),
            "birk_source": source_label,
        },
    }

    if property_id in existing_costs:
        rec_id = existing_costs[property_id]
        r = requests.patch(
            f"{SUPABASE_URL}/rest/v1/property_annual_costs",
            headers=HEADERS,
            params={"property_annual_cost_id": f"eq.{rec_id}"},
            json=record,
        )
        if not r.ok:
            raise RuntimeError(f"PATCH failed {r.status_code}: {r.text[:200]}")
        return "updated"
    else:
        record["property_annual_cost_id"] = str(uuid.uuid4())
        r = requests.post(f"{SUPABASE_URL}/rest/v1/property_annual_costs",
                          headers=HEADERS, json=record)
        if not r.ok:
            raise RuntimeError(f"POST failed {r.status_code}: {r.text[:200]}")
        existing_costs[property_id] = record["property_annual_cost_id"]
        return "inserted"


# ── hovedløkke ────────────────────────────────────────────────────────────────

ins = upd = skipped_no_portfeb = skipped_no_db = 0

print("\n--- Institusjoner ---")
for inst in institusjoner:
    eid = inst.get("EnhetID", "").strip()
    navn = inst.get("Enhetsnavn", "").strip()

    portfeb = inst_to_portfeb.get(eid)
    if not portfeb:
        skipped_no_portfeb += 1
        continue

    db_p = find_db_property(inst)
    if not db_p:
        skipped_no_db += 1
        continue

    action = upsert_cost(db_p["property_id"], portfeb, f"birk_inst:{eid}")
    lok_ref = (portfeb.get("Lokalisering") or "")[:35]
    print(f"  [{action}] {navn[:45]} → {lok_ref}")
    if action == "inserted":
        ins += 1
    else:
        upd += 1

print(f"\n--- Avdelinger (arver foreldres portfeb) ---")

# Bygg oppslag: parent-navn → portfeb (for avdelinger der parent ikke er i inst_to_portfeb)
parent_name_to_portfeb = {}
for avd in avdelinger:
    pid        = avd.get("TilhørighetEnhetID", "").strip()
    pnavn      = avd.get("Tilhørighet", "").strip()
    if not pnavn:
        continue
    if pid in inst_to_portfeb:
        parent_name_to_portfeb[pnavn] = inst_to_portfeb[pid]
    elif pnavn not in parent_name_to_portfeb:
        # Lag en midlertidig birk-rad med foreldrenavnet og match mot portfeb
        fake = {"Enhetsnavn": pnavn, "Adresse": avd.get("Adresse",""), "Postnummer": avd.get("Postnummer","")}
        match = best_portfeb_match(fake, portfeb_rows)
        if match:
            parent_name_to_portfeb[pnavn] = match
            inst_to_portfeb[pid] = match  # cache

for avd in avdelinger:
    eid    = avd.get("EnhetID", "").strip()
    pid    = avd.get("TilhørighetEnhetID", "").strip()
    pnavn  = avd.get("Tilhørighet", "").strip()
    navn   = avd.get("Enhetsnavn", "").strip()

    portfeb = inst_to_portfeb.get(pid) or parent_name_to_portfeb.get(pnavn)
    if not portfeb:
        skipped_no_portfeb += 1
        continue

    db_p = find_db_property(avd)
    if not db_p:
        skipped_no_db += 1
        continue

    action = upsert_cost(db_p["property_id"], portfeb, f"birk_avd:{eid}->inst:{pid}")
    lok_ref = (portfeb.get("Lokalisering") or "")[:35]
    print(f"  [{action}] {navn[:45]} → {lok_ref}")
    if action == "inserted":
        ins += 1
    else:
        upd += 1

print(f"""
=== Ferdig ===
  Inserted:           {ins}
  Updated:            {upd}
  Skip (ingen portfeb-match): {skipped_no_portfeb}
  Skip (ikke i DB):   {skipped_no_db}
""")
