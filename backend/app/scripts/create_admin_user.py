"""
Oppretter eller oppdaterer admin-bruker med passord.

Kjøres én gang for å sette opp din admin-konto:
    cd backend
    python -m app.scripts.create_admin_user

Eller med egendefinert e-post/passord:
    python -m app.scripts.create_admin_user <email> <password>
"""
import asyncio
import sys
from sqlalchemy import select
import app.db.base  # noqa: F401 – registrerer alle SQLAlchemy-modeller og relasjoner
from app.db.session import SessionLocal
from app.domains.core.models.user import User, UserRole
from app.core.security.pwd import get_password_hash

DEFAULT_EMAIL = "frankvevle@gmail.com"
DEFAULT_PASSWORD = "Befs2026!"  # Bytt dette etter første login


async def create_or_update_admin(email: str, password: str) -> None:
    async with SessionLocal() as db:
        try:
            stmt = select(User).where(User.email == email)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            hashed = get_password_hash(password)

            if user:
                user.role = UserRole.ADMIN
                user.hashed_password = hashed
                user.is_active = True
                user.email_verified = True
                action = "Oppdatert"
            else:
                user = User(
                    email=email,
                    name="Frank Vevle",
                    role=UserRole.ADMIN,
                    hashed_password=hashed,
                    is_active=True,
                    email_verified=True,
                    mfa_enabled=False,
                )
                db.add(user)
                action = "Opprettet"

            await db.commit()
            await db.refresh(user)

            print(f"✅ {action} admin-bruker:")
            print(f"   E-post : {user.email}")
            print(f"   Rolle  : {user.role}")
            print(f"   Passord: satt (bcrypt)")
            print(f"   MFA    : {'På' if user.mfa_enabled else 'Av'}")
            print()
            print("Du kan nå logge inn med disse kredensialene.")

        except Exception as e:
            print(f"❌ Feil: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_EMAIL
    password = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PASSWORD
    asyncio.run(create_or_update_admin(email, password))
