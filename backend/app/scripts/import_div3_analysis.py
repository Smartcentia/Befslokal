
import asyncio
import sys
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property

# --- EXTRACTED DATA FROM div3.txt ---

STATSBYGG_MODEL_PROPS = [
    "Solfallsveien 27", "Uglevn 1", "Aurdalslia 96", "Svanehaugvegen 3", 
    "Haugane 15", "Liaveien 2", "Bastian Withs gt 11", "Kvalvågveien 113", 
    "Mindeveien 8", "Marknesringen 48", "Østmarkveien 26", "Snorres veg 2", 
    "Torleiv Kvalviks gate 9", "Nedre Nattland 69", "Tertneshøyden 33b", 
    "Klukevegen 30"
]

PRIVATE_MODEL_PROPS = [
    "Kjørbekksvingen 38", "Løkkeveien 33", "Oscarsgate 20", "Tærudgata 16", 
    "Elias Smiths vei", "Solheimsgaten 11", "Storgata 10", "Kabelgata 2", 
    "Vangsvegen 121", "Ramsrudveien 32", "Glemmengaten 55", "Rådhusgata 16", 
    "Energiveien 14", "Just Brochs gate 13", "Bekkegata 2A", "Håkonsgt 4", 
    "Storgata 70"
]

SHADOW_PORTFOLIO = [
    "Barkåker", "Mynten", "Kvammen", "Silsand", "Toppe"
]

CONTRACTS_2099 = [
    "Ramsrudveien 32", "Bjørlistubben 14", "Ullsvei 16", "Alfheimvn 6", 
    "Skolegata 53", "Wiulls gate 3", "Lundebyveien 363", "Veslekila 1", 
    "Kantarellveien 4"
]

RISK_HAERVERK = [
    "St. Hansgården", "Thorøya", "Røvika", "Nye Kvæfjord", "Lamo", 
    "Nye Toppen", "Østheim", "Vien", "Bredal"
]

RISK_CAPEX = [
    "Skatval", "Eikelund", "Vikhovlia", "Meltunet", "Skjerven", 
    "Nes", "Stokke", "Solepilot"
]

async def update_property_analysis(db: AsyncSession, name_snippet: str, data_update: dict):
    """
    Finds a property by fuzzy name match and updates its external_data['analysis_2026'].
    """
    # Simple ILIKE match
    stmt = select(Property).where(Property.name.ilike(f"%{name_snippet}%"))
    result = await db.execute(stmt)
    prop = result.scalars().first()
    
    if prop:
        print(f"MATCH: '{name_snippet}' -> '{prop.name}'")
        
        # Init external_data if None
        if prop.external_data is None:
            prop.external_data = {}
            
        # Init analysis_2026 dict
        analysis = prop.external_data.get('analysis_2026', {})
        
        # Merge updates
        analysis.update(data_update)
        
        # Write back
        prop.external_data['analysis_2026'] = analysis
        
        # Force SQLAlchemy to detect change in JSONB
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(prop, "external_data")
        
        db.add(prop)
        return True
    else:
        print(f"MISSING: '{name_snippet}' not found in DB.")
        return False

async def main():
    print("--- Starting div3.txt Analysis Import ---")
    
    async with SessionLocal() as db:
        
        # 1. Statsbygg Model
        print("\n[1/6] Tagging Statsbygg Model (80/100)...")
        for name in STATSBYGG_MODEL_PROPS:
            await update_property_analysis(db, name, {
                "kpi_model": "STATSBYGG_SHARED_80_100",
                "risk_profile": "HIGH_MAINTENANCE_INFLATION",
                "description": "Statsbygg model: Rent 80% KPI, Maintenance 100% KPI."
            })
            
        # 2. Private Model
        print("\n[2/6] Tagging Private Model (100%)...")
        for name in PRIVATE_MODEL_PROPS:
            await update_property_analysis(db, name, {
                "kpi_model": "PRIVATE_STANDARD_100",
                "risk_profile": "STANDARD_COMMERCIAL",
                "description": "Standard Private model: 100% KPI on gross rent."
            })

        # 3. Shadow Portfolio
        print("\n[3/6] Tagging Shadow Portfolio (Missing in Contract ID)...")
        for name in SHADOW_PORTFOLIO:
            await update_property_analysis(db, name, {
                "shadow_portfolio": True,
                "data_quality_alert": "MISSING_IN_CONTRACT_REGISTRY",
                "risk_level": "CRITICAL"
            })
            
        # 4. 2099 Contracts
        print("\n[4/6] Tagging 2099 Contracts...")
        for name in CONTRACTS_2099:
            await update_property_analysis(db, name, {
                "contract_type": "PERPETUAL_OR_OWNERSHIP_LIKE",
                "lease_end_year": 2099
            })

        # 5. Hærverk Risk
        print("\n[5/6] Tagging High Vandalism Risk...")
        for name in RISK_HAERVERK:
            await update_property_analysis(db, name, {
                "operational_risk": "HIGH_VANDALISM",
                "maintenance_flag": "REQUIRES_ROBUST_MATERIALS"
            })

        # 6. CAPEX Risk
        print("\n[6/6] Tagging CAPEX/Investment Risk...")
        for name in RISK_CAPEX:
            await update_property_analysis(db, name, {
                "financial_risk": "TENANT_FUNDED_CAPEX",
                "audit_flag": "CHECK_OBLIGATIONS"
            })
            
        print("\nCommitting changes...")
        await db.commit()
    
    print("--- Import Complete ---")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
        print("Dry run mode not fully implemented, running for real but check logs.")
        
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Execution failed: {e}")
        # Identify firewall issues
        if "Connection refereed" in str(e) or "timeout" in str(e).lower():
            print("\nNOTE: Database connection likely blocked by Firewall.")
