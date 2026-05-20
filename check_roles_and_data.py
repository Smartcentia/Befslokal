import asyncio
import os
import sys

# Add backend to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(current_dir, "backend")
sys.path.append(backend_path)

from app.db.session import engine
from sqlalchemy import text

async def check():
    async with engine.connect() as conn:
        # 1. Check admin user
        res = await conn.execute(text("SELECT email, role, region FROM users WHERE email = 'admin@befs.no'"))
        user = res.fetchone()
        if user:
            print(f'User: {user.email}, Role: {user.role}, Region: {user.region}')
        else:
            print('User admin@befs.no NOT FOUND')
            
        # 2. Check roles summary
        res = await conn.execute(text("SELECT role, count(*) FROM users GROUP BY role"))
        print('\nRole Summary:')
        for role, count in res.all():
            print(f'  {role}: {count}')
            
        # 3. Check property assignments count
        res = await conn.execute(text("SELECT count(*) FROM user_property_association"))
        print(f'\nTotal Property Assignments: {res.scalar()}')
        
        # 4. Check properties count
        res = await conn.execute(text("SELECT count(*) FROM properties"))
        print(f'Total Properties: {res.scalar()}')
        
        # 5. Check property regions
        res = await conn.execute(text("SELECT region, count(*) FROM properties GROUP BY region"))
        print('\nProperty Regions:')
        for reg, count in res.all():
            print(f'  {reg}: {count}')

        # 6. Check users with properties assigned
        res = await conn.execute(text("""
            SELECT u.email, u.role, count(upa.property_id) 
            FROM users u 
            JOIN user_property_association upa ON u.user_id = upa.user_id 
            GROUP BY u.email, u.role
        """))
        print('\nUsers with direct property assignments:')
        for email, role, count in res.all():
            print(f'  {email} ({role}): {count} properties')


if __name__ == '__main__':
    asyncio.run(check())
