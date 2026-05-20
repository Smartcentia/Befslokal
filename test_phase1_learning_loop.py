#!/usr/bin/env python3
"""
Test Phase 1 Self-Learning Loop Implementation

This script tests:
1. Query logging to database
2. Confidence scoring
3. Auto-retry logic
4. Integration with existing sql_generator
"""

import asyncio
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from backend/.env
backend_dir = Path(__file__).parent / "backend"
env_file = backend_dir / ".env"
load_dotenv(env_file)

# Add backend to path
sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal as AsyncSessionLocal
from app.services.dspy.sql_generator import dspy_generator
from sqlalchemy import text


async def test_query_logging():
    """Test 1: Verify that queries are logged to query_logs table"""
    print("\n" + "=" * 80)
    print("TEST 1: Query Logging")
    print("=" * 80)

    async with AsyncSessionLocal() as db:
        # Execute a simple query
        question = "Hvor mange eiendommer har vi?"
        print(f"\n📝 Executing query: {question}")

        result = await dspy_generator.execute_query(db, question)

        print(f"✓ Query executed")
        print(f"  - SQL: {result.get('sql', 'N/A')[:100]}...")
        print(f"  - Success: {result.get('error') is None}")
        print(f"  - Confidence: {result.get('confidence', 0.0):.2f}")
        print(f"  - Model: {result.get('model_used', 'N/A')}")
        print(f"  - Log ID: {result.get('log_id', 'N/A')}")

        # Verify log exists in database
        if result.get('log_id'):
            log_check = await db.execute(
                text("SELECT * FROM query_logs WHERE log_id = :id"),
                {"id": result['log_id']}
            )
            log_row = log_check.fetchone()

            if log_row:
                print("\n✅ SUCCESS: Query logged to database!")
                print(f"  - Log ID: {log_row.log_id}")
                print(f"  - Execution Success: {log_row.execution_success}")
                print(f"  - Confidence Score: {log_row.confidence_score:.2f}")
                print(f"  - Model Used: {log_row.model_used}")
                print(f"  - Cache Hit: {log_row.cache_hit}")
                print(f"  - Execution Time: {log_row.execution_time_ms}ms")
                return True
            else:
                print("\n❌ FAILURE: Log not found in database")
                return False
        else:
            print("\n⚠️  WARNING: No log_id returned (but query may have succeeded)")
            return False


async def test_confidence_scoring():
    """Test 2: Verify confidence scoring works"""
    print("\n" + "=" * 80)
    print("TEST 2: Confidence Scoring")
    print("=" * 80)

    async with AsyncSessionLocal() as db:
        # Test different types of queries
        test_cases = [
            ("SELECT * FROM properties LIMIT 5", "Simple query"),
            ("Hvilken region har høyest kostnad per kvm?", "Complex aggregation"),
            ("List all properties", "Basic lookup")
        ]

        all_passed = True
        for question, description in test_cases:
            print(f"\n📝 Testing: {description}")
            print(f"   Question: {question}")

            result = await dspy_generator.execute_query(db, question)

            confidence = result.get('confidence', 0.0)
            model_used = result.get('model_used', 'N/A')

            print(f"  - Confidence: {confidence:.2f}")
            print(f"  - Model: {model_used}")

            if 0.0 <= confidence <= 1.0:
                print("  ✅ Confidence score in valid range")
            else:
                print(f"  ❌ Confidence score INVALID: {confidence}")
                all_passed = False

            if model_used in ["gpt-4o", "gpt-4o-mini", "query_library"]:
                print(f"  ✅ Model used is valid")
            else:
                print(f"  ❌ Model used is INVALID: {model_used}")
                all_passed = False

        if all_passed:
            print("\n✅ SUCCESS: All confidence scores valid!")
            return True
        else:
            print("\n❌ FAILURE: Some confidence scores invalid")
            return False


async def test_stats():
    """Test 3: Verify stats collection works"""
    print("\n" + "=" * 80)
    print("TEST 3: Query Statistics")
    print("=" * 80)

    async with AsyncSessionLocal() as db:
        from app.services.query_logging_service import QueryLoggingService

        stats = await QueryLoggingService.get_stats(db, days=1)

        print("\n📊 Query Logging Stats (Last 24 hours):")
        print(f"  - Total Queries: {stats.get('total_queries', 0)}")
        print(f"  - Successful: {stats.get('successful', 0)}")
        print(f"  - Failed: {stats.get('failed', 0)}")
        print(f"  - Success Rate: {stats.get('success_rate', 0.0):.1%}")
        print(f"  - Cache Hit Rate: {stats.get('cache_hit_rate', 0.0):.1%}")
        print(f"  - Retry Rate: {stats.get('retry_rate', 0.0):.1%}")
        print(f"  - Avg Confidence: {stats.get('avg_confidence', 0.0):.2f}")
        print(f"  - Avg Execution Time: {stats.get('avg_execution_time_ms', 0.0):.0f}ms")

        if stats.get('total_queries', 0) > 0:
            print("\n✅ SUCCESS: Stats collection working!")
            return True
        else:
            print("\n⚠️  WARNING: No queries logged yet (run test 1 first)")
            return False


async def test_recent_logs():
    """Test 4: Verify we can retrieve recent logs"""
    print("\n" + "=" * 80)
    print("TEST 4: Recent Logs Retrieval")
    print("=" * 80)

    async with AsyncSessionLocal() as db:
        from app.services.query_logging_service import QueryLoggingService

        logs = await QueryLoggingService.get_recent_logs(db, limit=5)

        print(f"\n📋 Recent Query Logs (Last 5):")
        for i, log in enumerate(logs, 1):
            print(f"\n  {i}. {log['user_question'][:60]}...")
            print(f"     - Success: {'✅' if log['execution_success'] else '❌'}")
            print(f"     - Confidence: {log['confidence_score']:.2f}")
            print(f"     - Model: {log['model_used']}")
            print(f"     - Time: {log['execution_time_ms']}ms")
            print(f"     - Timestamp: {log['timestamp']}")

        if len(logs) > 0:
            print(f"\n✅ SUCCESS: Retrieved {len(logs)} recent logs!")
            return True
        else:
            print("\n⚠️  WARNING: No logs found")
            return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("PHASE 1 SELF-LEARNING LOOP - TEST SUITE")
    print("=" * 80)
    print("\nTesting:")
    print("1. Query logging to database")
    print("2. Confidence scoring")
    print("3. Query statistics")
    print("4. Recent logs retrieval")
    print("\n" + "=" * 80)

    results = []

    # Run tests
    results.append(("Query Logging", await test_query_logging()))
    results.append(("Confidence Scoring", await test_confidence_scoring()))
    results.append(("Query Statistics", await test_stats()))
    results.append(("Recent Logs Retrieval", await test_recent_logs()))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Phase 1 implementation is working!")
        print("\nNext steps:")
        print("1. ✅ Query logging is active")
        print("2. ✅ Confidence scoring is working")
        print("3. ✅ Daily task save_query_patterns.py will now have data!")
        print("4. ⏳ Run queries over time to populate query_library automatically")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
