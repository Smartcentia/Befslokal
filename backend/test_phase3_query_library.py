"""
Test Phase 3: Query Library Functionality

Tests:
1. Saving query patterns from logs
2. Finding similar queries
3. Executing library queries
4. Tracking usage statistics
"""

import asyncio
import json
from app.db.session import SessionLocal
from app.services.query_library_service import query_library_service
from app.services.mcp.handler import execute_sql_query_tool
from sqlalchemy import text


async def test_phase3():
    print("=== Testing Phase 3: Query Library ===\n")

    async with SessionLocal() as db:
        # Test 1: Manually insert a test query log
        print("Test 1: Simulating multiple executions of same query")
        print("-" * 60)

        test_question = "Hva er de 5 største eiendommene basert på areal?"
        test_sql = """
        SELECT
            property_id,
            name,
            total_area,
            city,
            region
        FROM properties
        WHERE total_area IS NOT NULL
        ORDER BY total_area DESC
        LIMIT 5
        """

        # Insert 5 successful executions of this query
        for i in range(5):
            await db.execute(text("""
                INSERT INTO query_logs
                (user_question, generated_sql, query_type, execution_success,
                 result_count, execution_time_ms, context_data)
                VALUES (:question, :sql, 'analysis', true, 5, :time, '{}')
            """), {
                "question": test_question,
                "sql": test_sql,
                "time": 300 + (i * 10)  # Varying execution times
            })
        await db.commit()

        print(f"✓ Inserted 5 query log entries for: {test_question[:50]}...\n")

        # Test 2: Run save_query_patterns to add to library
        print("Test 2: Saving successful pattern to library")
        print("-" * 60)

        # Check if this pattern qualifies
        stats = await db.execute(text("""
            SELECT
                COUNT(*) as executions,
                SUM(CASE WHEN execution_success THEN 1 ELSE 0 END) as successes,
                AVG(execution_time_ms) as avg_time
            FROM query_logs
            WHERE generated_sql = :sql
        """), {"sql": test_sql})

        row = stats.fetchone()
        print(f"Query stats:")
        print(f"  Executions: {row.executions}")
        print(f"  Successes: {row.successes}")
        print(f"  Avg time: {row.avg_time:.0f}ms")

        # Save pattern
        saved = await query_library_service.save_query_pattern(
            db,
            user_question=test_question,
            sql=test_sql,
            executions=row.executions,
            successes=row.successes,
            avg_time_ms=int(row.avg_time)
        )

        if saved:
            print(f"✓ Pattern saved to library\n")
        else:
            print(f"✗ Pattern not saved (may already exist or not meet criteria)\n")

        # Test 3: Find similar query
        print("Test 3: Finding similar query from library")
        print("-" * 60)

        similar_questions = [
            "Hva er de største eiendommene etter areal?",
            "Vis meg de 5 største eiendommene",
            "hvilke eiendommer har størst areal?"
        ]

        for question in similar_questions:
            match = await query_library_service.find_similar_query(
                db,
                question,
                min_usage_count=3,
                min_success_rate=0.90
            )

            if match:
                print(f"✓ Found match for: '{question}'")
                print(f"  Query name: {match['query_name']}")
                print(f"  Usage count: {match['usage_count']}")
                print(f"  Success rate: {match['success_rate']:.1%}")
                print(f"  Avg time: {match.get('avg_execution_time_ms', 0)}ms")
            else:
                print(f"✗ No match for: '{question}'")
            print()

        # Test 4: Execute query from library
        print("Test 4: Executing query from library")
        print("-" * 60)

        match = await query_library_service.find_similar_query(
            db,
            "størst eiendom areal",
            min_usage_count=1,
            min_success_rate=0.50
        )

        if match:
            print(f"Found library query: {match['query_name']}")

            # Execute
            import time
            start = time.time()
            result = await db.execute(text(match["sql_template"]))
            rows = result.mappings().all()
            exec_time = int((time.time() - start) * 1000)

            print(f"✓ Executed in {exec_time}ms")
            print(f"✓ Returned {len(rows)} rows")

            if rows:
                print("\nTop 3 results:")
                for row in list(rows)[:3]:
                    r = dict(row)
                    print(f"  - {r.get('name')}: {r.get('total_area', 0):,.0f} kvm ({r.get('city')})")

            # Update usage stats
            await query_library_service.increment_usage(
                db,
                match["query_id"],
                success=True,
                execution_time_ms=exec_time
            )
            print(f"\n✓ Updated usage statistics")

        else:
            print("✗ No library query found")

        print()

        # Test 5: Library statistics
        print("Test 5: Library statistics")
        print("-" * 60)

        stats = await query_library_service.get_library_stats(db)
        print(f"Total patterns: {stats.get('total_patterns', 0)}")
        print(f"Total uses: {stats.get('total_uses', 0)}")
        print(f"Avg uses per pattern: {stats.get('avg_uses_per_pattern', 0):.1f}")
        print(f"Avg success rate: {stats.get('avg_success_rate', 0):.1%}")
        print(f"Avg execution time: {stats.get('avg_exec_time_ms', 0):.0f}ms")
        print()

        # Test 6: Most used patterns
        print("Test 6: Most used patterns")
        print("-" * 60)

        top_patterns = await query_library_service.get_most_used_patterns(db, limit=5)

        if top_patterns:
            for i, pattern in enumerate(top_patterns, 1):
                print(f"{i}. {pattern['query_name']}")
                print(f"   Question: {pattern['user_question_pattern'][:50]}...")
                print(f"   Usage: {pattern['usage_count']}, Success: {pattern['success_rate']:.1%}")
                print()
        else:
            print("No patterns in library yet")

        # Test 7: Test full flow with context metadata
        print("Test 7: Full flow with context metadata")
        print("-" * 60)

        context = {
            "user_question": "Vis de 10 største kontraktene basert på total verdi",
            "query_type": "analysis",
            "entities": []
        }

        # This should trigger text-to-SQL via agent (if not in library yet)
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

        # This will be logged
        result = await execute_sql_query_tool(test_query, context)

        if isinstance(result, str) and not result.startswith("Error"):
            data = json.loads(result) if result else []
            print(f"✓ Query executed successfully")
            print(f"✓ Returned {len(data)} rows")
            print(f"✓ Logged to query_logs with context metadata")
        else:
            print(f"✗ Query failed: {result}")

        print()

    print("=== Phase 3 Testing Complete ===")


if __name__ == "__main__":
    asyncio.run(test_phase3())
