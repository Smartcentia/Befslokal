import sys
import os
import asyncio
from typing import List

# Setup path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

from app.services.dspy.sql_generator import dspy_generator, SQLValidator

async def test_quick():
    print("🚀 DSPy Quick Test Initiated")
    
    # Check Env
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not found. Tests might fail or run in mock mode.")
    else:
        print("✅ OPENAI_API_KEY found")

    test_queries = [
        "Vis alle eiendommer i Oslo",
        "Hvor mange kontrakter har vi totalt?",
        "Finn alle parter med navn 'Statsbygg'",
        "Hvilke kontrakter er terminert?",
        "DROP TABLE properties" # Should be blocked
    ]

    for q in test_queries:
        print(f"\nExample: '{q}'")
        try:
            # 1. Prediction
            pred = dspy_generator.forward(q)
            sql = pred.sql_query
            print(f"  -> Generated SQL: {sql}")
            
            # 2. Validation
            clean = SQLValidator.clean(sql)
            is_valid = SQLValidator.validate(clean)
            
            if is_valid:
                print("  ✅ Validation: PASS")
            else:
                print("  🛡️  Validation: BLOCKED (Safe)")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_quick())
