#!/usr/bin/env python3
"""Oppretter standard admin-bruker for Befslokal (lokal auth)."""
import asyncio
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.domains.core.models.user import User, UserRole
from app.core.security.pwd import get_password_hash

ADMIN_EMAIL = os.getenv("BEFSLOCAL_ADMIN_EMAIL", "admin@befslokal.no")
ADMIN_PASSWORD = os.getenv("BEFSLOCAL_ADMIN_PASSWORD", "befslokal123")
ADMIN_NAME = os.getenv("BEFSLOCAL_ADMIN_NAME", "Befslokal Admin")


async def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL mangler")
        sys.exit(1)

    engine = create_async_engine(database_url, echo=False)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        stmt = select(User).where(User.email == ADMIN_EMAIL)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        hashed = get_password_hash(ADMIN_PASSWORD)

        if user:
            user.hashed_password = hashed
            user.is_active = True
            user.role = UserRole.ADMIN
            user.email_verified = True
            user.mfa_enabled = False
            print(f"Oppdatert passord for {ADMIN_EMAIL}")
        else:
            user = User(
                user_id=uuid.uuid4(),
                email=ADMIN_EMAIL,
                name=ADMIN_NAME,
                role=UserRole.ADMIN,
                region="National",
                hashed_password=hashed,
                is_active=True,
                email_verified=True,
                mfa_enabled=False,
            )
            session.add(user)
            print(f"Opprettet admin {ADMIN_EMAIL}")

        await session.commit()

    await engine.dispose()
    print(f"Innlogging: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(main())
