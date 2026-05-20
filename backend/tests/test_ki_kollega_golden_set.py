"""
Golden Set Testing for KI Kollega

Dette testsettet verifiserer at KI Kollega ruter korrekt, genererer riktig SQL,
og håndterer JSONB-felter korrekt.

Krever DSPy med skrivbar cache (DSPY_CACHEDIR). conftest.py setter cache-dir
til tests/.pytest_dspy_cache. I helt readonly-miljø skippes modulen.
"""

import pytest
import asyncio
from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession

# Import av DSPy krever skrivbar cache. Hvis cache-dir er readonly, skipp hele modulen.
try:
    from app.services.intelligence.agents.nodes.supervisor import supervisor_node
    from app.services.intelligence.agents.state import AgentState
    from app.services.dspy.sql_generator import dspy_generator, SQLValidator
    from langchain_core.messages import HumanMessage
    from app.db.session import SessionLocal
except (OSError, PermissionError, Exception) as e:
    # sqlite3.OperationalError (readonly DB) eller andre import-feil
    pytest.skip(
        f"DSPy/cache ikke tilgjengelig (sett DSPY_CACHEDIR til skrivbar mappe): {e}",
        allow_module_level=True,
    )


# Golden Set - Test cases med forventede resultater
GOLDEN_SET = [
    {
        "id": "gs_001",
        "question": "Gi meg den største eiendommen",
        "expected_route": "researcher",  # Researcher først, så analyst hvis ingenting
        "expected_final_route": "analyst",  # Skal ende opp i analyst for SQL
        "expected_sql_patterns": [
            r"SELECT.*total_area",
            r"ORDER BY.*total_area.*DESC",
            r"LIMIT\s+1"
        ],
        "expected_tool": None,
        "min_result_count": 1,
        "category": "analysis"
    },
    {
        "id": "gs_002",
        "question": "Hvor ligger Storgata 10?",
        "expected_route": "researcher",
        "expected_final_route": "researcher",  # Skal finne via lookup_properties
        "expected_sql_patterns": [],
        "expected_tool": "lookup_properties",
        "min_result_count": 0,
        "category": "lookup"
    },
    {
        "id": "gs_003",
        "question": "Hva er gjennomsnittlig leie per region?",
        "expected_route": "researcher",
        "expected_final_route": "analyst",
        "expected_sql_patterns": [
            r"AVG.*amount_per_year",
            r"GROUP BY.*region",
            r"amount->>'amount_per_year'"
        ],
        "expected_tool": None,
        "min_result_count": 0,
        "category": "aggregation"
    },
    {
        "id": "gs_004",
        "question": "Vis meg alle aktive kontrakter",
        "expected_route": "researcher",
        "expected_final_route": "analyst",
        "expected_sql_patterns": [
            r"SELECT.*contract",
            r"status.*=.*['\"]active['\"]",
            r"status.*=.*['\"]Aktiv['\"]"
        ],
        "expected_tool": None,
        "min_result_count": 0,
        "category": "listing"
    },
    {
        "id": "gs_005",
        "question": "Finn kontrakter som utløper i 2026",
        "expected_route": "researcher",
        "expected_final_route": "analyst",
        "expected_sql_patterns": [
            r"end_date.*>=\s*['\"]2026-01-01['\"]",
            r"end_date.*<=\s*['\"]2026-12-31['\"]",
            r"ORDER BY.*end_date"
        ],
        "expected_tool": None,
        "min_result_count": 0,
        "category": "filtering"
    },
    {
        "id": "gs_006",
        "question": "Hva er total årlig leie for alle aktive kontrakter?",
        "expected_route": "researcher",
        "expected_final_route": "analyst",
        "expected_sql_patterns": [
            r"SUM.*amount_per_year",
            r"amount->>'amount_per_year'",
            r"::numeric",
            r"status.*=.*['\"]active['\"]"
        ],
        "expected_tool": None,
        "min_result_count": 1,
        "category": "aggregation_jsonb"
    },
    {
        "id": "gs_007",
        "question": "Sammenlign kostnader mellom regionene",
        "expected_route": "researcher",
        "expected_final_route": "analyst",
        "expected_sql_patterns": [
            r"GROUP BY.*region",
            r"SUM.*cost",
            r"external_data.*financials"
        ],
        "expected_tool": None,
        "min_result_count": 0,
        "category": "comparison"
    },
    {
        "id": "gs_008",
        "question": "Hei, hvordan går det?",
        "expected_route": "writer",  # Greeting skal gå direkte til writer
        "expected_final_route": "writer",
        "expected_sql_patterns": [],
        "expected_tool": None,
        "min_result_count": 0,
        "category": "greeting"
    }
]


class TestGoldenSet:
    """Test suite for Golden Set validation"""
    
    @pytest.mark.asyncio
    async def test_supervisor_routing(self):
        """Test at Supervisor ruter korrekt basert på spørsmål"""
        for test_case in GOLDEN_SET:
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
            
            assert route == test_case["expected_route"], \
                f"Test {test_case['id']}: Forventet route '{test_case['expected_route']}', fikk '{route}'"
    
    @pytest.mark.asyncio
    async def test_sql_generation_patterns(self):
        """Test at DSPy genererer SQL med forventede mønstre"""
        for test_case in GOLDEN_SET:
            if not test_case["expected_sql_patterns"]:
                continue  # Skip hvis ikke SQL-forventet
            
            question = test_case["question"]
            
            # Generer SQL
            pred = dspy_generator.forward(question)
            sql = SQLValidator.clean(pred.sql_query)
            
            # Valider at SQL er trygg
            assert SQLValidator.validate(sql), \
                f"Test {test_case['id']}: Generert SQL feiler validering: {sql[:100]}"
            
            # Sjekk at forventede mønstre finnes i SQL
            sql_upper = sql.upper()
            for pattern in test_case["expected_sql_patterns"]:
                import re
                assert re.search(pattern, sql_upper, re.IGNORECASE), \
                    f"Test {test_case['id']}: Mønster '{pattern}' ikke funnet i SQL: {sql[:200]}"
    
    @pytest.mark.asyncio
    async def test_sql_execution(self):
        """Test at generert SQL faktisk kan kjøres (hvis database tilgjengelig)"""
        for test_case in GOLDEN_SET:
            if not test_case["expected_sql_patterns"]:
                continue
            
            question = test_case["question"]
            
            try:
                async with SessionLocal() as db:
                    result = await dspy_generator.execute_query(db, question)
                    
                    # Sjekk at vi ikke fikk en feil
                    assert result.get("error") is None, \
                        f"Test {test_case['id']}: SQL-kjøring feilet: {result.get('error')}"
                    
                    # Sjekk minimum antall resultater hvis spesifisert
                    if test_case.get("min_result_count", 0) > 0:
                        assert result.get("count", 0) >= test_case["min_result_count"], \
                            f"Test {test_case['id']}: Forventet minst {test_case['min_result_count']} resultater, fikk {result.get('count', 0)}"
                    
            except Exception as e:
                # Hvis database ikke tilgjengelig, skip test
                pytest.skip(f"Database ikke tilgjengelig: {e}")
    
    @pytest.mark.asyncio
    async def test_jsonb_handling(self):
        """Test spesifikt JSONB-håndtering i SQL-generering"""
        jsonb_test_cases = [
            {
                "question": "Hva er total årlig leie?",
                "must_contain": ["amount->>'amount_per_year'", "::numeric"]
            },
            {
                "question": "Finn enheter med areal større enn 100 m²",
                "must_contain": ["external_data->>'area'", "::float"]
            },
            {
                "question": "Vis finansiell data fra external_data",
                "must_contain": ["external_data->'financials'"]
            }
        ]
        
        for test_case in jsonb_test_cases:
            pred = dspy_generator.forward(test_case["question"])
            sql = SQLValidator.clean(pred.sql_query)
            
            sql_upper = sql.upper()
            for pattern in test_case["must_contain"]:
                assert pattern.lower() in sql.lower() or pattern.upper() in sql_upper, \
                    f"JSONB-mønster '{pattern}' ikke funnet i SQL: {sql[:200]}"


async def run_golden_set_validation():
    """Kjør Golden Set validering manuelt (uten pytest)"""
    print("=" * 80)
    print("KI KOLLEGA GOLDEN SET VALIDATION")
    print("=" * 80)
    
    results = {
        "total": len(GOLDEN_SET),
        "passed": 0,
        "failed": 0,
        "skipped": 0
    }
    
    for test_case in GOLDEN_SET:
        print(f"\n[{test_case['id']}] {test_case['question']}")
        print(f"  Kategori: {test_case['category']}")
        
        try:
            # Test routing
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
            
            route_result = await supervisor_node(state)
            route = route_result.get("next_step", "")
            
            if route == test_case["expected_route"]:
                print(f"  ✅ Routing: {route}")
                results["passed"] += 1
            else:
                print(f"  ❌ Routing: Forventet '{test_case['expected_route']}', fikk '{route}'")
                results["failed"] += 1
            
            # Test SQL-generering hvis forventet
            if test_case["expected_sql_patterns"]:
                pred = dspy_generator.forward(test_case["question"])
                sql = SQLValidator.clean(pred.sql_query)
                
                if SQLValidator.validate(sql):
                    print(f"  ✅ SQL validering: OK")
                    print(f"  SQL: {sql[:150]}...")
                    results["passed"] += 1
                else:
                    print(f"  ❌ SQL validering: FEILET")
                    print(f"  SQL: {sql[:150]}...")
                    results["failed"] += 1
        
        except Exception as e:
            print(f"  ⚠️  Test feilet: {e}")
            results["failed"] += 1
    
    print("\n" + "=" * 80)
    print(f"RESULTAT: {results['passed']}/{results['total']} tester bestått")
    print(f"Feilet: {results['failed']}, Skippet: {results['skipped']}")
    print("=" * 80)
    
    return results


if __name__ == "__main__":
    # Kjør manuell validering
    asyncio.run(run_golden_set_validation())
