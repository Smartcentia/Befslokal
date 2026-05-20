"""
Sjekk om eiendommer med type næringseiendom (eller som vises som det) er matchet
til en parent-eiendom (avdeling → institusjon).

Matching i API skjer kun når:
  1. property.parent_unit_id_erp er satt OG en annen eiendom har unit_id_erp = den verdien, ELLER
  2. property.unit_short_type == "Avdeling" OG property har affiliation + region
     OG en eiendom med unit_short_type == "Barnevernsinstitusjon" har samme (affiliation, region).

Kjør fra backend: cd backend && python scripts/sjekk_naeringseiendom_matching.py
"""
from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except Exception:
    pass

from sqlalchemy import select
from app.db.session import SessionLocal
from app.domains.core.models.property import Property


async def main():
    async with SessionLocal() as db:
        # Alle eiendommer
        res = await db.execute(select(Property))
        all_props = res.scalars().all()

        # Usage som vises som "Næringseiendom": DB usage = Næringseiendom, eller null/blank (default i API)
        def vises_naering(p):
            u = (p.usage or "").strip()
            if u and u.lower() in ("næringseiendom", "naeringseiendom"):
                return True
            ext = p.external_data or {}
            if ext.get("usage") or ext.get("eiendomstype"):
                return False  # har annen type fra external
            return not u  # tom usage → default Næringseiendom i API

        naering = [p for p in all_props if vises_naering(p)]
        # Parent-map: unit_id_erp → property_id (alle eiendommer)
        erp_to_id = {}
        for p in all_props:
            if p.unit_id_erp:
                erp_to_id[p.unit_id_erp] = str(p.property_id)
        # (affiliation, region) → property_id for Barnevernsinstitusjon
        affil_region_to_id = {}
        for p in all_props:
            if (
                (p.unit_short_type or "").strip() == "Barnevernsinstitusjon"
                and (p.affiliation or "").strip()
                and (p.region or "").strip()
            ):
                key = (p.affiliation.strip(), p.region.strip())
                if key not in affil_region_to_id:
                    affil_region_to_id[key] = str(p.property_id)

        # Kategoriser næringseiendommer
        med_parent_erp_og_treff = []
        med_parent_erp_uten_treff = []
        avdeling_affil_med_treff = []
        avdeling_affil_uten_treff = []
        ingen_kobling = []

        for p in naering:
            pid = str(p.property_id)
            parent_id = None
            if p.parent_unit_id_erp:
                parent_id = erp_to_id.get(p.parent_unit_id_erp)
                if parent_id:
                    med_parent_erp_og_treff.append((p, parent_id))
                else:
                    med_parent_erp_uten_treff.append(p)
                continue
            if (p.unit_short_type or "").strip() == "Avdeling" and (p.affiliation or "").strip() and (p.region or "").strip():
                key = (p.affiliation.strip(), p.region.strip())
                parent_id = affil_region_to_id.get(key)
                if parent_id:
                    avdeling_affil_med_treff.append((p, parent_id))
                else:
                    avdeling_affil_uten_treff.append(p)
                continue
            ingen_kobling.append(p)

        # Rapporter
        print("=" * 60)
        print("NÆRINGSEIENDOM – matching mot parent-eiendom")
        print("=" * 60)
        print(f"Totalt antall eiendommer: {len(all_props)}")
        print(f"Antall som vises som næringseiendom (usage eller default): {len(naering)}")
        print()
        print("Matchet til parent (parent_unit_id_erp → unit_id_erp):")
        print(f"  Med treff: {len(med_parent_erp_og_treff)}")
        print(f"  Uten treff (forelder finnes ikke i DB): {len(med_parent_erp_uten_treff)}")
        print("Matchet til parent (Avdeling + affiliation + region):")
        print(f"  Med treff: {len(avdeling_affil_med_treff)}")
        print(f"  Uten treff: {len(avdeling_affil_uten_treff)}")
        print(f"Ingen kobling (mangler parent_unit_id_erp og/eller Avdeling+affiliation+region): {len(ingen_kobling)}")
        print()

        if med_parent_erp_uten_treff:
            print("Eksempel – har parent_unit_id_erp men ingen forelder i DB:")
            for p in med_parent_erp_uten_treff[:5]:
                print(f"  {p.name or p.address} | parent_unit_id_erp={p.parent_unit_id_erp}")
        if ingen_kobling:
            print("Eksempel – næringseiendom uten noen kobling (kandidater for manuell matching):")
            for p in ingen_kobling[:10]:
                print(f"  {p.name or p.address} | unit_short_type={p.unit_short_type!r} affiliation={p.affiliation!r} region={p.region!r}")
        print()
        print("Konklusjon: Matching er implementert i API (get_properties og get_sub_units).")
        print("Eiendommer får parent_property_id kun når parent_unit_id_erp eller Avdeling+affiliation+region matcher.")
        print("Mange næringseiendommer mangler disse feltene (f.eks. fra andre datakilder enn e-don2).")


if __name__ == "__main__":
    asyncio.run(main())
