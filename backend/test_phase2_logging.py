"""
Test Phase 2: Query Logging Functionality
Tests that execute_sql_query_tool properly logs all attempts
"""
import asyncio
from app.services.mcp.handler import execute_sql_query_tool
from app.db.session import SessionLocal
from sqlalchemy import text

async def test_logging():
    print("=== Testing Phase 2 Query Logging ===\n")

    # Test 1: Successful query with context
    print("Test 1: Successful SELECT query with context metadata")
    context = {
        "user_question": "Hva er de 10 største kontraktene basert på total verdi?",
        "query_type": "analysis",
        "entities": []
    }

    test_query = """
    SELECT
        c.contract_id,
        p.name as property_name,
        COALESCE(
            CASE
                WHEN c.amount IS NOT NULL AND c.amount->>'amount_per_year' ~ E'^[0-9]+\\.?[0-9]*$'
                THEN (c.amount->>'amount_per_year')::numeric
                ELSE 0
            END, 0
        ) +
        COALESCE(c.caretaker_cost, 0) +
        COALESCE(c.cleaning_cost, 0) +
        COALESCE(c.parking_cost, 0) +
        COALESCE(c.card_reader_cost, 0) as total_value
    FROM contracts c
    JOIN units u ON c.unit_id = u.unit_id
    JOIN properties p ON u.property_id = p.property_id
    WHERE c.status = 'active'
    ORDER BY total_value DESC
    LIMIT 10
    """

    result = await execute_sql_query_tool(test_query, context)
    print(f"Result preview: {str(result)[:200]}...\n")

    # Test 2: Blocked query (non-SELECT)
    print("Test 2: Blocked DELETE query")
    blocked_context = {
        "user_question": "Slett alle kontrakter",
        "query_type": "action",
        "entities": []
    }

    blocked_query = "DELETE FROM contracts WHERE status = 'terminated'"
    result2 = await execute_sql_query_tool(blocked_query, blocked_context)
    print(f"Result: {result2}\n")

    # Test 3: Failed query (syntax error)
    print("Test 3: Query with SQL syntax error")
    error_context = {
        "user_question": "Vis alle eiendommer",
        "query_type": "lookup",
        "entities": []
    }

    error_query = "SELECT * FORM properties LIMIT 5"  # FORM instead of FROM
    result3 = await execute_sql_query_tool(error_query, error_context)
    print(f"Result: {result3}\n")

    # Check logged entries
    print("=== Checking Query Logs ===\n")
    async with SessionLocal() as db:
        logs = await db.execute(text("""
            SELECT
                timestamp,
                user_question,
                LEFT(generated_sql, 60) as sql_preview,
                query_type,
                execution_success,
                result_count,
                execution_time_ms,
                LEFT(error_message, 100) as error_preview
            FROM query_logs
            ORDER BY timestamp DESC
        """))

        for i, row in enumerate(logs.fetchall(), 1):
            print(f"Log {i}:")
            print(f"  Question: {row.user_question}")
            print(f"  SQL: {row.sql_preview}...")
            print(f"  Type: {row.query_type}")
            print(f"  Success: {row.execution_success}")
            print(f"  Results: {row.result_count}")
            print(f"  Time: {row.execution_time_ms}ms")
            if row.error_preview:
                print(f"  Error: {row.error_preview}...")
            print()

if __name__ == "__main__":
    asyncio.run(test_logging())
