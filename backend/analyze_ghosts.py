
import asyncio
from prisma import Prisma
from texttable import Texttable

async def analyze_ghosts():
    db = Prisma()
    await db.connect()

    # Fetch all properties
    properties = await db.property.find_many(
        include={
            'lease_contracts': True,
            'running_costs': True,
            'images': True
        }
    )

    ghosts = []

    for p in properties:
        # Calculate an "emptiness" score
        score = 0
        reasons = []

        is_empty_area = (p.total_area_m2 is None or p.total_area_m2 < 1)
        is_missing_year = (p.construction_year is None)
        is_missing_label = (p.energy_label is None)
        has_no_contracts = (len(p.lease_contracts) == 0)
        has_no_costs = (len(p.running_costs) == 0)
        has_no_images = (len(p.images) == 0)

        if is_empty_area:
            score += 2
            reasons.append("No Area")
        if is_missing_year:
            score += 1
            reasons.append("No Year")
        if is_missing_label:
            score += 1
            reasons.append("No Energy Label")
        if has_no_contracts:
            score += 2
            reasons.append("No Contracts")
        if has_no_costs:
            score += 2
            reasons.append("No Costs")
        if has_no_images:
            score += 1
            reasons.append("No Images")

        # Threshold for "Ghost": High score means very little info
        # Max score is 9. Let's look at anything >= 6 or specific combinations like No Area + No Financials
        if score >= 6 or (is_empty_area and has_no_contracts and has_no_costs):
            ghosts.append({
                "id": p.id,
                "name": p.name,
                "score": score,
                "reasons": ", ".join(reasons),
                "area": p.total_area_m2,
                "contracts": len(p.lease_contracts),
                "costs": len(p.running_costs)
            })

    # Sort by score descending (emptiest first)
    ghosts.sort(key=lambda x: x['score'], reverse=True)

    t = Texttable()
    t.add_rows([['ID', 'Name', 'Score', 'Area', 'Contracts', 'Costs', 'Reasons']] + 
               [[g['id'], g['name'], g['score'], g['area'], g['contracts'], g['costs'], g['reasons']] for g in ghosts])
    
    print(t.draw())
    
    # Also print a summary analysis
    print(f"\nFound {len(ghosts)} potential ghost properties out of {len(properties)} total.")

    await db.disconnect()

if __name__ == '__main__':
    asyncio.run(analyze_ghosts())
