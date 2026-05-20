import asyncio
import sys
import os

# Add backend directory to path to import app modules
sys.path.append("/Users/frank/Documents/BEFS3/KNOWME/backend")

from app.services.mock_data_service import MockDataService

async def verify_connectivity():
    print("--- Verifying 'Everything is Connected' Flow ---")

    # 1. Fetch a Property
    print("\n1. Fetching Property 'p1'...")
    prop = MockDataService.get_property("p1")
    if not prop:
        print("FAIL: Could not fetch property p1")
        return
    print(f"SUCCESS: Found property: {prop['name']} at {prop['address']}")
    
    # 2. Check for Linked Contracts
    contracts = prop.get("contracts", [])
    if not contracts:
        print("FAIL: Property has no linked contracts")
        return
    
    first_contract_ref = contracts[0]
    contract_id = first_contract_ref["id"]
    print(f"SUCCESS: Found linked contract ref: {contract_id} ({first_contract_ref['tenant']})")

    # 3. Fetch the Contract Detail
    print(f"\n2. Fetching Contract Detail '{contract_id}'...")
    contract = MockDataService.get_contract(contract_id)
    if not contract:
        print(f"FAIL: Could not fetch contract details for {contract_id}")
        return
    
    print(f"SUCCESS: Retrieved contract details. Rent: {contract['rent']}")
    
    # 4. Check for Linked Party
    party_id = contract.get("partyId")
    if not party_id:
        print("FAIL: Contract has no linked partyId")
        return
    print(f"SUCCESS: Found linked party ID: {party_id}")

    # 5. Fetch Party Detail
    print(f"\n3. Fetching Party Detail '{party_id}'...")
    party = MockDataService.get_party(party_id)
    if not party:
        print(f"FAIL: Could not fetch party details for {party_id}")
        return
    
    print(f"SUCCESS: Retrieved party: {party['name']} (Org: {party['orgNr']})")
    
    print("\n-------------------------------------------")
    print("✅ VERIFIED: Full Connectivity Chain Works!")
    print("Property -> Contract -> Party")
    print("-------------------------------------------")

if __name__ == "__main__":
    asyncio.run(verify_connectivity())
