#!/usr/bin/env python3
"""
Test BRREG (Brønnøysundregistrene) connectivity.
Kjør fra prosjektrot: ./scripts/kjor_test_brreg.sh
eller fra backend:  python3 scripts/test_brreg_connectivity.py [orgnr]
Uten orgnr: tester med 984851006 (DNB).
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Test org numbers: DNB (known to exist), and optional from args
TEST_ORGNRS = ["984851006"]


async def main():
    orgnr = (sys.argv[1] if len(sys.argv) > 1 else "").replace(" ", "")
    if orgnr and len(orgnr) == 9 and orgnr.isdigit():
        TEST_ORGNRS.insert(0, orgnr)

    from app.services.external.brreg_service import BrregService

    print("BRREG connectivity test")
    print("=" * 50)
    for org in TEST_ORGNRS:
        print(f"\nTesting orgnr {org}...")
        try:
            enhet = await BrregService.get_enhet(org, db=None)
            if enhet:
                print(f"  OK: {enhet.get('name', 'N/A')} ({enhet.get('source', 'N/A')})")
                print(f"  Adresse: {enhet.get('address', 'N/A')}")
            else:
                print(f"  FEIL: Ingen data returnert (enhet finnes kanskje ikke i BRREG)")
        except Exception as e:
            print(f"  FEIL: {type(e).__name__}: {e}")
    print("\n" + "=" * 50)
    print("Ferdig. Hvis du ser 'OK' for 984851006, er BRREG tilgjengelig.")


if __name__ == "__main__":
    asyncio.run(main())
