
import asyncio
import uuid
import json
from sqlalchemy import text
from app.db.session import SessionLocal

async def seed_data():
    print("🌱 Seeding query_logs with a candidate for evolution...")
    
    async with SessionLocal() as db:
        sql = "SELECT p.name, (c.amount->>'total')::numeric as rent FROM contracts c JOIN units u ON c.unit_id = u.unit_id JOIN properties p ON u.property_id = p.property_id ORDER BY rent DESC LIMIT 5"
        question = "Hvilke 5 kontrakter har høyest totalverdi?"
        
        stmt = text("""
            INSERT INTO query_logs 
            (log_id, user_question, generated_sql, query_type, execution_success, result_count, execution_time_ms, context_data)
            VALUES (:id, :q, :sql, 'analysis', true, 5, 120, :ctx)
        """)
        
        await db.execute(stmt, {
            "id": uuid.uuid4(),
            "q": question,
            "sql": sql,
            "ctx": json.dumps({"source": "seed_script"})
        })
        await db.commit()
        print(f"✅ Inserted query: {question}")

if __name__ == "__main__":
    asyncio.run(seed_data())
