#!/usr/bin/env python3
"""
Analyze which properties can still be linked to GL data.
Approach:
1. koststed_mapping.koststed_kode = gl_transactions.dim1_kode
2. koststed_mapping.property_id → properties
3. Find koststed_mapping entries without property_id but with GL data
4. Try to match their koststed_navn to property names
"""
import asyncio, sys, json, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from app.db.session import SessionLocal
from sqlalchemy import text


def normalize(s):
    if not s: return ""
    s = str(s).lower().strip()
    s = re.sub(r"[^\w\sæøå]", " ", s)
    return " ".join(s.split())


def words(s, min_len=4):
    return [w for w in normalize(s).split() if len(w) >= min_len]


def score(prop_name, kost_name):
    if not prop_name or not kost_name: return 0.0
    pn = normalize(prop_name)
    kn = normalize(kost_name)
    if pn in kn or kn in pn: return 0.95
    pw = set(words(prop_name))
    kw = set(words(kost_name))
    if not pw or len(pw) < 2: return 0.0
    return len(pw & kw) / len(pw)


async def main():
    async with SessionLocal() as db:
        # 1. Unmapped koststed with GL data
        r = await db.execute(text("""
            SELECT km.koststed_kode, km.koststed_navn, km.region,
                   SUM(g.belop) FILTER(WHERE g.ar=2025 AND g.belop>0) as gl25,
                   SUM(g.belop) FILTER(WHERE g.belop>0) as gl_any
            FROM koststed_mapping km
            JOIN gl_transactions g ON g.dim1_kode = km.koststed_kode
            WHERE km.property_id IS NULL
            GROUP BY km.koststed_kode, km.koststed_navn, km.region
            HAVING SUM(g.belop) FILTER(WHERE g.belop>0) > 0
            ORDER BY gl25 DESC NULLS LAST
        """))
        unmapped = [(row[0], row[1] or "", row[2] or "", float(row[3] or 0), float(row[4] or 0))
                    for row in r.fetchall()]
        print(f"Unmapped koststed with GL data: {len(unmapped)}")

        # 2. Properties NOT in prediction
        r2 = await db.execute(text("""
            SELECT property_id::text, name, unit_id_erp, region, municipality, unit_type_derived
            FROM properties
            WHERE property_id NOT IN (
                SELECT DISTINCT property_id FROM budget WHERE year=2027 AND is_synthetic=true
            )
            AND (closed_at IS NULL OR closed_at > NOW())
        """))
        missing_props = [(row[0], row[1] or "", row[2], row[3] or "", row[4] or "", row[5] or "")
                         for row in r2.fetchall()]
        print(f"Active properties without prediction: {len(missing_props)}")

        # 3. Match by name
        matches = []
        for kode, kname, kreg, gl25, gl_any in unmapped:
            best_pid, best_score, best_pname = None, 0.0, ""
            for pid, pname, _, preg, _, _ in missing_props:
                sc = score(pname, kname)
                if sc > best_score and sc >= 0.55:
                    best_score = sc
                    best_pid = pid
                    best_pname = pname
            if best_pid:
                matches.append({
                    "kode": kode, "kname": kname, "kreg": kreg,
                    "pid": best_pid, "pname": best_pname, "score": round(best_score, 2),
                    "gl25": gl25, "gl_any": gl_any
                })

        print(f"\nName matches (score>=0.55): {len(matches)}")
        for m in sorted(matches, key=lambda x: -x["gl25"])[:30]:
            print(f"  {m['pname'][:38]:<40} ← {m['kname'][:38]:<40} score={m['score']:.2f}  gl25={m['gl25']/1e6:.2f}M")

        print(f"\nTotal reachable if matched: {155 + len(matches)}")

asyncio.run(main())
