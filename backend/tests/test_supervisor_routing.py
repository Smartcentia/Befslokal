"""
Enkel test for Supervisor routing (uten DSPy-avhengigheter)
"""

import asyncio
import sys
import os

# Legg til backend i path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage
from app.services.intelligence.agents.nodes.supervisor import supervisor_node
from app.services.intelligence.agents.state import AgentState


async def test_supervisor_routing():
    """Test at Supervisor ruter korrekt"""
    
    test_cases = [
        {
            "question": "Gi meg den største eiendommen",
            "expected": "researcher",
            "reason": "Analysis query skal gå til researcher først"
        },
        {
            "question": "Hei, hvordan går det?",
            "expected": "writer",
            "reason": "Greeting skal gå direkte til writer"
        },
        {
            "question": "Hvor ligger Storgata 10?",
            "expected": "researcher",
            "reason": "Lookup query skal gå til researcher"
        },
        {
            "question": "SQL query: SELECT * FROM properties",
            "expected": "analyst",
            "reason": "Eksplisitt SQL query skal gå til analyst"
        },
        {
            "question": "Sammenlign regionene",
            "expected": "researcher",
            "reason": "Comparison query skal gå til researcher først"
        },
        {
            "question": "Oversikt over porteføljen",
            "expected": "researcher",  # Kan bli "analyst" med LLM routing
            "reason": "Ambiguous query - kan gå til researcher eller analyst"
        }
    ]
    
    print("=" * 80)
    print("SUPERVISOR ROUTING TEST")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] {test_case['question']}")
        print(f"  Forventet: {test_case['expected']}")
        print(f"  Grunn: {test_case['reason']}")
        
        try:
            state: AgentState = {
                "messages": [HumanMessage(content=test_case["question"])],
                "next_step": "",
                "current_agent": "",
                "research_data": {},
                "discovered_tools": [],
                "persona": None,
                "available_scripts": [],
                "script_results": {},
                "error": None,
                "usage": None
            }
            
            result = await supervisor_node(state)
            route = result.get("next_step", "")
            
            print(f"  Faktisk route: {route}")
            
            # For ambiguous queries, aksepter både researcher og analyst
            if test_case["question"] == "Oversikt over porteføljen":
                if route in ["researcher", "analyst"]:
                    print(f"  ✅ PASS (aksepterer både researcher og analyst)")
                    passed += 1
                else:
                    print(f"  ❌ FAIL (forventet researcher eller analyst)")
                    failed += 1
            elif route == test_case["expected"]:
                print(f"  ✅ PASS")
                passed += 1
            else:
                print(f"  ❌ FAIL")
                failed += 1
                
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"RESULTAT: {passed}/{len(test_cases)} tester bestått")
    print(f"Feilet: {failed}")
    print("=" * 80)
    
    return passed == len(test_cases)


if __name__ == "__main__":
    success = asyncio.run(test_supervisor_routing())
    sys.exit(0 if success else 1)
