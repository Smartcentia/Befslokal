"""
Oppretter testbrukere for alle roller og regioner.

Brukes til å teste impersonering og rollebasert tilgangsstyring.

Kjøring:
    cd backend
    python -m app.scripts.seed_test_users

Alle testbrukere får passordet:  Test2026!
E-poster følger mønsteret:       test.<rolle>@befs.no  /  test.<rolle>.<region>@befs.no
"""
import asyncio
import app.db.base  # noqa: F401 – registrerer alle modeller
from sqlalchemy import select
from app.db.session import SessionLocal
from app.domains.core.models.user import User, UserRole
from app.core.security.pwd import get_password_hash

PASSWORD = "Test2026!"

REGIONS = ["Nord", "Midt-Norge", "Vest", "Sør", "Øst", "Bufdir"]

# (email, name, role, region)
TEST_USERS = [
    # --- Ledelse ---
    ("test.admin@befs.no",            "Test Admin",               UserRole.ADMIN,              "Bufdir"),
    ("test.nasjonal@befs.no",         "Test Nasjonal Leder",      UserRole.NASJONAL_LEDER,     "Bufdir"),

    # --- Regionledere — én per region ---
    ("test.regionleder.nord@befs.no",        "Test Regionleder Nord",        UserRole.REGIONAL_MANAGER, "Nord"),
    ("test.regionleder.midtnorge@befs.no",   "Test Regionleder Midt-Norge",  UserRole.REGIONAL_MANAGER, "Midt-Norge"),
    ("test.regionleder.vest@befs.no",        "Test Regionleder Vest",        UserRole.REGIONAL_MANAGER, "Vest"),
    ("test.regionleder.sor@befs.no",         "Test Regionleder Sør",         UserRole.REGIONAL_MANAGER, "Sør"),
    ("test.regionleder.ost@befs.no",         "Test Regionleder Øst",         UserRole.REGIONAL_MANAGER, "Øst"),
    ("test.regionleder.bufdir@befs.no",      "Test Regionleder Bufdir",      UserRole.REGIONAL_MANAGER, "Bufdir"),

    # --- Økonomi ---
    ("test.okonomi@befs.no",          "Test Økonomiansvarlig",    UserRole.OKONOMIANSVARLIG,   "Bufdir"),

    # --- Eiendomsforvaltning ---
    ("test.forvalter.nord@befs.no",       "Test Eiendomsforvalter Nord",    UserRole.PROPERTY_MANAGER,    "Nord"),
    ("test.forvalter.vest@befs.no",       "Test Eiendomsforvalter Vest",    UserRole.PROPERTY_MANAGER,    "Vest"),
    ("test.forvalter.ost@befs.no",        "Test Eiendomsforvalter Øst",     UserRole.PROPERTY_MANAGER,    "Øst"),
    ("test.kontrakt@befs.no",             "Test Kontraktsforvalter",         UserRole.KONTRAKTSFORVALTER,  "Bufdir"),

    # --- FDVU / Drift ---
    ("test.fdvu.nord@befs.no",       "Test FDVU-koordinator Nord",   UserRole.FDVU_KOORDINATOR,  "Nord"),
    ("test.fdvu.vest@befs.no",       "Test FDVU-koordinator Vest",   UserRole.FDVU_KOORDINATOR,  "Vest"),
    ("test.fdvu.ost@befs.no",        "Test FDVU-koordinator Øst",    UserRole.FDVU_KOORDINATOR,  "Øst"),
    ("test.drift.nord@befs.no",      "Test Driftsansvarlig Nord",    UserRole.DRIFTSANSVARLIG,   "Nord"),
    ("test.drift.sor@befs.no",       "Test Driftsansvarlig Sør",     UserRole.DRIFTSANSVARLIG,   "Sør"),
    ("test.vaktmester.nord@befs.no", "Test Vaktmester Nord",         UserRole.JANITOR,            "Nord"),
    ("test.vaktmester.vest@befs.no", "Test Vaktmester Vest",         UserRole.JANITOR,            "Vest"),
    ("test.vaktmester.ost@befs.no",  "Test Vaktmester Øst",          UserRole.JANITOR,            "Øst"),

    # --- HMS ---
    ("test.hms@befs.no",             "Test HMS-ansvarlig",           UserRole.HMS_ANSVARLIG,     "Bufdir"),

    # --- Ekstern / read-only ---
    ("test.leietaker@befs.no",       "Test Leietaker",               UserRole.TENANT,            None),
    ("test.revisor@befs.no",         "Test Revisor",                 UserRole.REVISOR,           "Bufdir"),
]


async def seed() -> None:
    hashed = get_password_hash(PASSWORD)

    async with SessionLocal() as db:
        created = 0
        updated = 0

        for email, name, role, region in TEST_USERS:
            stmt = select(User).where(User.email == email)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                user.name = name
                user.role = role
                user.region = region
                user.hashed_password = hashed
                user.is_active = True
                user.email_verified = True
                user.mfa_enabled = False
                updated += 1
            else:
                user = User(
                    email=email,
                    name=name,
                    role=role,
                    region=region,
                    hashed_password=hashed,
                    is_active=True,
                    email_verified=True,
                    mfa_enabled=False,
                )
                db.add(user)
                created += 1

        await db.commit()

        print(f"\n✅ Testbrukere seedet: {created} opprettet, {updated} oppdatert")
        print(f"   Passord for alle: {PASSWORD}\n")
        print("   Roller og e-poster:")
        for email, name, role, region in TEST_USERS:
            reg = f"  [{region}]" if region else ""
            print(f"   {role.value:<22} {email:<42}{reg}")
        print("\n   Bruk /admin/impersonate for å teste roller.\n")


if __name__ == "__main__":
    asyncio.run(seed())
