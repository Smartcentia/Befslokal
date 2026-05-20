#!/usr/bin/env python3
"""
Seed query_library med «største eiendommer med lav husleie».
Kjør: python backend/scripts/seed_query_library_storste_lav_husleie.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from app.db.session import SessionLocal
from app.services.query_library_service import query_library_service


SQL_STORSTE_LAV_HUSLEIE = """
SELECT 
    p.name,
    p.total_area,
    p.region,
    COALESCE(SUM((c.amount->>'amount_per_year')::numeric), 0)::bigint AS husleie_ar,
    ROUND((COALESCE(SUM((c.amount->>'amount_per_year')::numeric), 0) / NULLIF(p.total_area, 0))::numeric, 0) AS kr_per_kvm
FROM properties p
LEFT JOIN units u ON u.property_id = p.property_id
LEFT JOIN contracts c ON c.unit_id = u.unit_id AND c.status = 'active' AND c.amount->>'amount_per_year' IS NOT NULL
WHERE p.total_area > 0
GROUP BY p.property_id, p.name, p.total_area, p.region
HAVING COALESCE(SUM((c.amount->>'amount_per_year')::numeric), 0) > 0
ORDER BY p.total_area DESC, kr_per_kvm ASC
LIMIT 12
"""

USER_QUESTION_PATTERNS = [
    "hvilke er de største eiendommer som har lav husleie",
    "største eiendommer med lav husleie",
    "hvilke eiendommer er størst og har lavest leie per kvm",
    "de største eiendommer med lavest husleie per kvadratmeter",
]


async def main():
    async with SessionLocal() as db:
        inserted = await query_library_service.insert_manual_query(
            db=db,
            query_name="storste_eiendommer_lav_husleie",
            user_question_pattern=" ".join(USER_QUESTION_PATTERNS),
            sql_template=SQL_STORSTE_LAV_HUSLEIE.strip(),
            description="Største eiendommer (etter areal) med lavest husleie per kvm. Sortert på total_area DESC, kr_per_kvm ASC.",
        )
        if inserted:
            print("✅ Query 'storste_eiendommer_lav_husleie' lagt til i query_library")
        else:
            print("ℹ️ Query finnes allerede eller ble ikke lagt til")


if __name__ == "__main__":
    asyncio.run(main())
