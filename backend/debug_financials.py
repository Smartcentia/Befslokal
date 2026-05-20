import asyncio
from sqlalchemy import select
from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.user import User
from app.domains.core.models.center import Center

async def main():
    async with SessionLocal() as db:
        query = select(Property)
        result = await db.execute(query)
        props = result.scalars().all()

        print(f"Total properties: {len(props)}")
        
        # Collect properties with their maintenance cost
        prop_costs = []
        for p in props:
            if p.external_data and isinstance(p.external_data, dict):
                financials = p.external_data.get('financials', {})
                
                cost = 0.0
                components = {}
                
                for key in ['total_spend_csv', 'total_manual_expenses', 'municipal_fees', 'energy_cost', 'heating_cost']:
                    val = float(financials.get(key, 0) or 0)
                    cost += val
                    if val > 0:
                        components[key] = val
                
                prop_costs.append({
                    "id": p.property_id,
                    "address": p.address,
                    "total_cost": cost,
                    "components": components
                })
        
        # Sort by total cost descending
        prop_costs.sort(key=lambda x: x['total_cost'], reverse=True)
        
        grand_total = sum(p['total_cost'] for p in prop_costs)
        print(f"\nGRAND TOTAL MAINTENANCE: {grand_total:,.2f}")
        
        print("\nTop 10 properties by maintenance cost:")
        for i, p in enumerate(prop_costs[:10]):
            print(f"{i+1}. {p['address']} (ID: {p['id']})")
            print(f"   Total: {p['total_cost']:,.2f}")
            print(f"   Components: {p['components']}")

if __name__ == "__main__":
    asyncio.run(main())
