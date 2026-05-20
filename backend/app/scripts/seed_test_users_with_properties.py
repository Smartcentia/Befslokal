"""
Seed test-brukere for alle roller og regioner, og tildel dem eiendommer.

Kjøres med:
  railway run --service BEFS1 python3 backend/app/scripts/seed_test_users_with_properties.py

Oppretter:
  - Én DRIFTSANSVARLIG per region (manglende)
  - Én JANITOR per region (manglende)
  - Én FDVU_KOORDINATOR per region (manglende)
  - Én HMS_ANSVARLIG per region (manglende)
  - Én PROPERTY_MANAGER per region (manglende)

Tildeler alle regionale brukere til eiendommer i sin region via user_property_association.

Standard testpassord: Test1234!
"""

import asyncio, os, sys, uuid
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.db.session import SessionLocal
from app.core.security.pwd import get_password_hash
from sqlalchemy import text

TEST_PASSWORD = "Test1234!"

# Regioner i systemet
REGIONS = ["Nord", "Midt-Norge", "Vest", "Sør", "Øst"]

# Alle testbrukere som skal finnes – {email_prefix: (role, region)}
# REGIONAL_MANAGER trenger ikke property-tildelinger (bruker region-felt)
DESIRED_USERS = []

for region in REGIONS:
    slug = region.lower().replace("-", "").replace("ø", "o").replace("å", "a").replace("æ", "a")
    DESIRED_USERS.extend([
        (f"test.drift.{slug}@befs.no",       "DRIFTSANSVARLIG",   region),
        (f"test.vaktmester.{slug}@befs.no",  "JANITOR",           region),
        (f"test.fdvu.{slug}@befs.no",        "FDVU_KOORDINATOR",  region),
        (f"test.hms.{slug}@befs.no",         "HMS_ANSVARLIG",     region),
        (f"test.forvalter.{slug}@befs.no",   "PROPERTY_MANAGER",  region),
    ])

# Bufdir-brukere (ikke region-basert RBAC, men trenger noen eiendommer for testing)
DESIRED_USERS.extend([
    ("test.admin@befs.no",       "ADMIN",                 "Bufdir"),
    ("test.nasjonal@befs.no",    "NASJONAL_LEDER",        "Bufdir"),
    ("test.okonomi@befs.no",     "OKONOMIANSVARLIG",      "Bufdir"),
    ("test.kontrakt@befs.no",    "KONTRAKTSFORVALTER",    "Bufdir"),
    ("test.revisor@befs.no",     "REVISOR",               "Bufdir"),
    ("test.hms@befs.no",         "HMS_ANSVARLIG",         "Bufdir"),
    ("test.leietaker@befs.no",   "TENANT",                None),
])


async def run():
    hashed_pw = get_password_hash(TEST_PASSWORD)

    async with SessionLocal() as db:
        # --- Hent eksisterende brukere ---
        existing = {
            row[0]: row[1]
            for row in (await db.execute(
                text("SELECT email, user_id FROM users")
            )).fetchall()
        }
        print(f"Eksisterende brukere: {len(existing)}")

        # --- Opprett manglende brukere ---
        created = 0
        for email, role, region in DESIRED_USERS:
            if email in existing:
                continue
            uid = uuid.uuid4()
            name_parts = email.split("@")[0].split(".")
            name = " ".join(p.capitalize() for p in name_parts[1:])
            await db.execute(text("""
                INSERT INTO users (user_id, email, name, role, region, hashed_password,
                                   is_active, email_verified, mfa_enabled)
                VALUES (:uid, :email, :name, :role, :region, :pw,
                        true, true, false)
                ON CONFLICT (email) DO NOTHING
            """), {
                "uid": uid, "email": email, "name": name,
                "role": role, "region": region, "pw": hashed_pw,
            })
            existing[email] = uid
            created += 1
            print(f"  Opprettet: {email} [{role}] region={region}")

        await db.commit()
        print(f"\n✅ Opprettet {created} nye brukere")

        # --- Hent user_id for alle relevante brukere ---
        all_users = {
            row[0]: (str(row[1]), row[2], row[3])
            for row in (await db.execute(text(
                "SELECT email, user_id, role, region FROM users WHERE email LIKE 'test.%'"
            ))).fetchall()
        }

        # --- Hent eiendommer per region ---
        props_by_region: dict = {}
        rows = (await db.execute(text(
            "SELECT property_id, region FROM properties WHERE region IS NOT NULL"
        ))).fetchall()
        for row in rows:
            region = row[1]
            if region not in props_by_region:
                props_by_region[region] = []
            props_by_region[region].append(str(row[0]))

        print(f"\nEiendommer per region:")
        for r, pids in props_by_region.items():
            print(f"  {r}: {len(pids)} eiendommer")

        # --- Tildel eiendommer ---
        # Roller som trenger eksplisitte property-tildelinger (ikke REGIONAL_MANAGER som bruker region-felt)
        NEEDS_ASSIGNMENT = {
            "DRIFTSANSVARLIG", "JANITOR", "FDVU_KOORDINATOR",
            "HMS_ANSVARLIG", "PROPERTY_MANAGER", "KONTRAKTSFORVALTER",
        }

        # Slett eksisterende assignments for testbrukere (for å rydde opp gammel data)
        test_user_ids = [uid for (uid, role, region) in all_users.values()]
        if test_user_ids:
            ids_literal = ", ".join(f"'{uid}'::uuid" for uid in test_user_ids)
            await db.execute(text(f"""
                DELETE FROM user_property_association
                WHERE user_id IN ({ids_literal})
            """))
            await db.commit()
            print(f"\n🧹 Ryddet eksisterende property-tildelinger for {len(test_user_ids)} testbrukere")

        inserted = 0
        for email, (uid, role, region) in all_users.items():
            if role not in NEEDS_ASSIGNMENT:
                continue
            if not region or region == "Bufdir":
                # Bufdir-brukere: gi dem et lite utvalg av eiendommer (5 fra Øst)
                sample_ids = (props_by_region.get("Øst") or [])[:5]
                prop_ids = sample_ids
            else:
                prop_ids = props_by_region.get(region, [])

            if not prop_ids:
                continue

            # Batch insert
            values = ", ".join(
                f"('{uid}'::uuid, '{pid}'::uuid)"
                for pid in prop_ids
            )
            await db.execute(text(f"""
                INSERT INTO user_property_association (user_id, property_id)
                VALUES {values}
                ON CONFLICT DO NOTHING
            """))
            inserted += len(prop_ids)
            print(f"  {email} [{role}] → {len(prop_ids)} eiendommer i {region}")

        await db.commit()
        print(f"\n✅ Totalt {inserted} property-tildelinger opprettet")

        # --- Oppsummering ---
        print("\n" + "="*60)
        print("TESTBRUKERE – OVERSIKT")
        print("="*60)
        print(f"Passord: {TEST_PASSWORD}")
        print()

        by_role: dict = {}
        for email, (uid, role, region) in sorted(all_users.items()):
            by_role.setdefault(role, []).append((email, region))

        role_labels = {
            "DRIFTSANSVARLIG": "Driftsansvarlig (FDVU/drift, egne eiendommer)",
            "JANITOR": "Vaktmester (sjekklister, avvik, egne eiendommer)",
            "FDVU_KOORDINATOR": "FDVU-koordinator (vedlikehold, tilstand)",
            "HMS_ANSVARLIG": "HMS-ansvarlig (risiko, avvik, HMS-rapporter)",
            "PROPERTY_MANAGER": "Eiendomsforvalter (egne eiendommer)",
            "KONTRAKTSFORVALTER": "Kontraktsforvalter (kontrakter, leietakere)",
            "REGIONAL_MANAGER": "Regionleder (alle i sin region)",
            "OKONOMIANSVARLIG": "Økonomiansvarlig (budsjett, regnskap)",
            "NASJONAL_LEDER": "Nasjonal leder (les alt)",
            "ADMIN": "Admin (full tilgang)",
            "REVISOR": "Revisor (les alt, ingen skriving)",
            "TENANT": "Leietaker (egne kontrakter)",
        }

        for role, users in sorted(by_role.items()):
            print(f"[{role}] — {role_labels.get(role, role)}")
            for email, region in sorted(users):
                print(f"  ✉  {email}  (region: {region})")
            print()

if __name__ == "__main__":
    asyncio.run(run())
