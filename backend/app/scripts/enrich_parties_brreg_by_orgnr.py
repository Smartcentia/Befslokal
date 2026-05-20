"""
Beriker alle partier som har orgnr med full BRREG-enhet (brreg_enhet i external_data).
Inkluderer risiko-felter: slettedato, konkurs, underAvvikling, tvangsoppløsning, etc.

Kjør fra prosjektrot: python -m app.scripts.enrich_parties_brreg_by_orgnr
eller fra backend: python app/scripts/enrich_parties_brreg_by_orgnr.py
"""
import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), "backend", ".env"))
load_dotenv(os.path.join(os.getcwd(), ".env"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.attributes import flag_modified

from app.db.session import engine
from app.domains.core.models.party import Party
from app.services.external.brreg_service import BrregService


async def enrich_parties_by_orgnr(dry_run: bool = False) -> int:
    """
    For alle partier med orgnr: hent full enhet fra BRREG og lagre i party.external_data["brreg_enhet"].
    Returnerer antall partier oppdatert.
    """
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    updated_count = 0
    async with AsyncSessionLocal() as db:
        stmt = select(Party).where(
            Party.orgnr.isnot(None),
            Party.orgnr != "",
            Party.orgnr != "000000000",
        )
        result = await db.execute(stmt)
        parties = result.scalars().all()

        print(f"Fant {len(parties)} partier med orgnr. Beriker med BRREG get_enhet...")

        for party in parties:
            orgnr = (party.orgnr or "").strip()
            if len(orgnr) != 9 or not orgnr.isdigit():
                print(f"  Hopper over {party.name}: ugyldig orgnr {orgnr!r}")
                continue

            enhet = await BrregService.get_enhet(orgnr, db=db)
            if not enhet:
                print(f"  Ingen BRREG-data for {party.name} ({orgnr})")
                continue

            if dry_run:
                print(f"  [dry-run] Ville satt brreg_enhet for {party.name} ({orgnr})")
                updated_count += 1
                continue

            ext = dict(party.external_data or {})
            ext["brreg_enhet"] = enhet
            # Hent roller for aktive enheter (ikke SlettetEnhet)
            if enhet.get("respons_klasse") != "SlettetEnhet":
                roller = await BrregService.get_roller(orgnr)
                if roller:
                    ext["brreg_roller"] = roller
                    # Sett roles slik at partysiden viser Daglig leder, Styreleder, Revisor
                    roles_list = roller.get("roller") or []
                    roles = {}
                    for r in roles_list:
                        rt = (r.get("rolletype") or "").lower()
                        navn = r.get("navn")
                        if not navn:
                            continue
                        if "daglig" in rt and not roles.get("dagligLeder"):
                            roles["dagligLeder"] = navn
                        elif ("styreleder" in rt or ("styre" in rt and "leder" in rt)) and not roles.get("styretsLeder"):
                            roles["styretsLeder"] = navn
                        elif "revisor" in rt and not roles.get("revisor"):
                            roles["revisor"] = navn
                    if roles:
                        ext["roles"] = roles
            party.external_data = ext
            flag_modified(party, "external_data")
            updated_count += 1

            # Risiko-felter: logg hvis slettet/konkurs/avvikling
            if enhet.get("respons_klasse") == "SlettetEnhet":
                print(f"  Slettet enhet: {party.name} ({orgnr}) slettedato={enhet.get('slettedato')}")
            elif enhet.get("konkurs"):
                print(f"  Konkurs: {party.name} ({orgnr})")
            elif enhet.get("underAvvikling"):
                print(f"  Under avvikling: {party.name} ({orgnr})")
            elif enhet.get("underTvangsavviklingEllerTvangsopplosning"):
                print(f"  Tvangsavvikling/tvangsoppløsning: {party.name} ({orgnr})")

            try:
                await db.commit()
            except Exception as e:
                print(f"  Feil ved commit for {party.name}: {e}")
                await db.rollback()

        print(f"Ferdig. Oppdatert {updated_count} partier med brreg_enhet.")
    return updated_count


def main():
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    if dry_run:
        print("Kjører i dry-run (ingen endringer lagres).")
    asyncio.run(enrich_parties_by_orgnr(dry_run=dry_run))


if __name__ == "__main__":
    main()
