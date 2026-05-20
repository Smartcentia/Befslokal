"""
Detaljert analyse av adressedata og koordinater
"""
import asyncio
from sqlalchemy import text
from app.db.session import SessionLocal

async def detailed_address_analysis():
    async with SessionLocal() as db:
        # Sjekk adressekvalitet
        result = await db.execute(text("""
            SELECT 
                COUNT(*) as totalt,
                SUM(CASE WHEN address IS NOT NULL AND address != '' THEN 1 ELSE 0 END) as med_adresse,
                SUM(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL THEN 1 ELSE 0 END) as med_koordinater,
                SUM(CASE WHEN geom IS NOT NULL THEN 1 ELSE 0 END) as med_postgis_geom,
                SUM(CASE WHEN postal_code IS NOT NULL THEN 1 ELSE 0 END) as med_postnr,
                SUM(CASE WHEN municipality IS NOT NULL THEN 1 ELSE 0 END) as med_kommune
            FROM properties
        """))
        row = result.one()
        total = row.totalt
        print('=== ADRESSEKVALITET ===')
        print(f'Totalt eiendommer: {total}')
        print(f'Med adresse: {row.med_adresse} ({row.med_adresse/total*100:.1f}%)')
        print(f'Med koordinater (lat/lon): {row.med_koordinater} ({row.med_koordinater/total*100:.1f}%)')
        print(f'Med PostGIS geometri: {row.med_postgis_geom} ({row.med_postgis_geom/total*100:.1f}%)')
        print(f'Med postnummer: {row.med_postnr} ({row.med_postnr/total*100:.1f}%)')
        print(f'Med kommune: {row.med_kommune} ({row.med_kommune/total*100:.1f}%)')
        
        # Sjekk manglende koordinater per region
        result = await db.execute(text("""
            SELECT 
                region,
                COUNT(*) as totalt,
                SUM(CASE WHEN latitude IS NULL OR longitude IS NULL THEN 1 ELSE 0 END) as uten_koordinater
            FROM properties
            GROUP BY region
            ORDER BY region
        """))
        print('\n=== MANGLENDE KOORDINATER PER REGION ===')
        for row in result:
            pct = row.uten_koordinater / row.totalt * 100 if row.totalt > 0 else 0
            print(f'{row.region:12} | Totalt: {row.totalt:3} | Uten koordinater: {row.uten_koordinater:3} ({pct:.1f}%)')
        
        # Sjekk Bufdir-eiendommer spesifikt
        result = await db.execute(text("""
            SELECT 
                COUNT(*) as totalt,
                SUM(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL THEN 1 ELSE 0 END) as med_koordinater,
                SUM(CASE WHEN address IS NOT NULL AND address != '' THEN 1 ELSE 0 END) as med_adresse
            FROM properties
            WHERE external_data::text LIKE '%bufdir%'
        """))
        row = result.one()
        print('\n=== BUFDIR-EIENDOMMER ===')
        print(f'Totalt: {row.totalt}')
        print(f'Med adresse: {row.med_adresse} ({row.med_adresse/row.totalt*100:.1f}%)')
        print(f'Med koordinater: {row.med_koordinater} ({row.med_koordinater/row.totalt*100:.1f}%)')
        
        # Eksempler på eiendommer uten koordinater
        result = await db.execute(text("""
            SELECT 
                name,
                address,
                postal_code,
                city,
                region,
                CASE 
                    WHEN external_data::text LIKE '%bufdir%' THEN 'Bufdir'
                    WHEN external_data::text LIKE '%is_synthetic%' THEN 'Syntetisk'
                    ELSE 'Normal'
                END as type
            FROM properties
            WHERE latitude IS NULL OR longitude IS NULL
            LIMIT 20
        """))
        print('\n=== EKSEMPLER PÅ EIENDOMMER UTEN KOORDINATER ===')
        print(f'{"Navn":50} | {"Adresse":40} | {"Type":10} | {"Region":12}')
        print('-' * 120)
        for row in result:
            name = (row.name or "[Ingen navn]")[:49]
            addr = (row.address or "-")[:39]
            print(f'{name:50} | {addr:40} | {row.type:10} | {row.region:12}')

if __name__ == "__main__":
    asyncio.run(detailed_address_analysis())
