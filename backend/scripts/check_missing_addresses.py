"""
Sjekk eiendommer med manglende adressedata
"""
import asyncio
from sqlalchemy import text
from app.db.session import SessionLocal

async def check_missing_addresses():
    async with SessionLocal() as db:
        # Totalt antall eiendommer
        result = await db.execute(text('SELECT COUNT(*) FROM properties'))
        total = result.scalar()
        
        # Eiendommer uten adresse
        result = await db.execute(text("""
            SELECT COUNT(*) 
            FROM properties 
            WHERE address IS NULL OR address = ''
        """))
        no_address = result.scalar()
        
        # Eiendommer uten navn
        result = await db.execute(text("""
            SELECT COUNT(*) 
            FROM properties 
            WHERE name IS NULL OR name = ''
        """))
        no_name = result.scalar()
        
        # Eiendommer uten både navn og adresse
        result = await db.execute(text("""
            SELECT COUNT(*) 
            FROM properties 
            WHERE (name IS NULL OR name = '') 
            AND (address IS NULL OR address = '')
        """))
        no_name_or_address = result.scalar()
        
        print('=== OVERSIKT MANGLENDE DATA ===')
        print(f'Totalt eiendommer: {total}')
        print(f'Uten adresse: {no_address} ({no_address/total*100:.1f}%)')
        print(f'Uten navn: {no_name} ({no_name/total*100:.1f}%)')
        print(f'Uten både navn og adresse: {no_name_or_address} ({no_name_or_address/total*100:.1f}%)')
        
        # Sjekk syntetiske eiendommer
        result = await db.execute(text("""
            SELECT 
                COUNT(*) as totalt,
                SUM(CASE WHEN external_data::text LIKE '%is_synthetic%true%' THEN 1 ELSE 0 END) as syntetisk,
                SUM(CASE WHEN external_data::text LIKE '%bufdir%' THEN 1 ELSE 0 END) as bufdir
            FROM properties
            WHERE address IS NULL OR address = ''
        """))
        row = result.one()
        print(f'\n=== EIENDOMMER UTEN ADRESSE ===')
        print(f'Totalt: {row.totalt}')
        print(f'Syntetiske: {row.syntetisk}')
        print(f'Bufdir: {row.bufdir}')
        
        # Datakilder
        result = await db.execute(text("""
            SELECT 
                CASE 
                    WHEN external_data::text LIKE '%bufdir%' THEN 'Bufdir'
                    WHEN external_data::text LIKE '%is_synthetic%true%' THEN 'Syntetisk'
                    WHEN external_data::text LIKE '%kartverket%' THEN 'Kartverket'
                    WHEN external_data::text LIKE '%eiendomsdata%' THEN 'Eiendomsdata'
                    ELSE 'Ukjent'
                END as kilde,
                COUNT(*) as antall
            FROM properties
            WHERE address IS NULL OR address = ''
            GROUP BY kilde
            ORDER BY antall DESC
        """))
        print(f'\n=== DATAKILDER (uten adresse) ===')
        for row in result:
            print(f'{row.kilde}: {row.antall}')
        
        # Alternative identifikatorer
        result = await db.execute(text("""
            SELECT 
                COUNT(*) as totalt,
                SUM(CASE WHEN gnr IS NOT NULL THEN 1 ELSE 0 END) as med_gnr,
                SUM(CASE WHEN municipality IS NOT NULL THEN 1 ELSE 0 END) as med_kommune,
                SUM(CASE WHEN postal_code IS NOT NULL THEN 1 ELSE 0 END) as med_postnr
            FROM properties
            WHERE address IS NULL OR address = ''
        """))
        row = result.one()
        print(f'\n=== ALTERNATIVE IDENTIFIKATORER (uten adresse) ===')
        print(f'Totalt: {row.totalt}')
        print(f'Med gnr/bnr: {row.med_gnr}')
        print(f'Med kommune: {row.med_kommune}')
        print(f'Med postnummer: {row.med_postnr}')
        
        # Eksempler
        result = await db.execute(text("""
            SELECT 
                property_id,
                name,
                region,
                municipality,
                postal_code,
                CASE 
                    WHEN external_data::text LIKE '%is_synthetic%true%' THEN 'Syntetisk'
                    WHEN external_data::text LIKE '%bufdir%' THEN 'Bufdir'
                    ELSE 'Annen'
                END as type
            FROM properties
            WHERE address IS NULL OR address = ''
            LIMIT 15
        """))
        print('\n=== EKSEMPLER PÅ EIENDOMMER UTEN ADRESSE ===')
        for row in result:
            name = row.name or "[Ingen navn]"
            kommune = row.municipality or "-"
            postnr = row.postal_code or "-"
            print(f'{name[:50]:50} | {row.type:10} | {row.region:12} | {kommune:20} | {postnr}')
        
        # Sjekk koordinater
        result = await db.execute(text("""
            SELECT COUNT(*)
            FROM properties
            WHERE (address IS NOT NULL AND address != '')
            AND (latitude IS NULL OR longitude IS NULL)
        """))
        no_coords = result.scalar()
        print(f'\n=== KOORDINATER ===')
        print(f'Med adresse men uten koordinater: {no_coords}')

if __name__ == "__main__":
    asyncio.run(check_missing_addresses())
