
import asyncio
import sys
import os

# Ensure app is in pythonpath
sys.path.append(os.getcwd())

from app.services.external.brreg_service import brreg_service

async def verify_brreg():
    # Test with a known company (e.g., Equinor ASA)
    org_nr = "923609016" 
    
    print(f"Fetching annual accounts for {org_nr}...")
    try:
        results = await brreg_service.get_aarsregnskap(org_nr)
        
        if results:
            print(f"Successfully fetched {len(results)} years of data.")
            for year_data in results:
                print(f"--- {year_data['year']} ---")
                print(f"Revenue: {year_data['revenue']}")
                print(f"Operating Profit: {year_data['operating_profit']}")
                print(f"Net Income: {year_data['net_income']}")
        else:
            print("No data found or error occurred (check logs).")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify_brreg())
