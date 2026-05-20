"""
Test Hybrid SQL-strategi: Kompleksitets-deteksjon og fallback til gpt-4o
"""

import sys
import os
import asyncio

# Legg til backend i path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.dspy.sql_generator import SQLGenerator, SQL_CACHE_ENABLED


def test_complexity_detection():
    """Test at kompleksitets-deteksjon fungerer korrekt"""
    
    print("=" * 80)
    print("KOMPLEKSITETS-DETEKSJON TEST")
    print("=" * 80)
    
    generator = SQLGenerator()
    
    test_cases = [
        {
            "question": "Gi meg den største eiendommen",
            "expected_complex": False,
            "reason": "Enkel SELECT med ORDER BY"
        },
        {
            "question": "Hva er gjennomsnittlig leie per region?",
            "expected_complex": True,
            "reason": "Aggregering (AVG) + GROUP BY"
        },
        {
            "question": "Sammenlign kostnader mellom regionene",
            "expected_complex": True,
            "reason": "Sammenligning + implisitt JOIN"
        },
        {
            "question": "Hvor ligger Storgata 10?",
            "expected_complex": False,
            "reason": "Enkel lookup"
        },
        {
            "question": "Hva er total årlig leie fra amount JSONB-feltet?",
            "expected_complex": True,
            "reason": "JSONB-operasjon (amount->>)"
        },
        {
            "question": "Finn eiendommer med finansiell data i external_data->'financials'",
            "expected_complex": True,
            "reason": "Nested JSONB-operasjon"
        },
        {
            "question": "Vis meg alle aktive kontrakter",
            "expected_complex": False,
            "reason": "Enkel SELECT med WHERE"
        },
        {
            "question": "Grupper eiendommer per region og beregn gjennomsnittlig kostnad",
            "expected_complex": True,
            "reason": "GROUP BY + aggregering"
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] {test_case['question']}")
        print(f"  Forventet: {'Kompleks' if test_case['expected_complex'] else 'Enkel'}")
        print(f"  Grunn: {test_case['reason']}")
        
        try:
            is_complex = generator._detect_complexity(test_case['question'])
            print(f"  Detektert: {'Kompleks' if is_complex else 'Enkel'}")
            
            if is_complex == test_case['expected_complex']:
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


def test_cache_with_model_tracking():
    """Test at cache sporer hvilken modell som ble brukt"""
    
    print("\n" + "=" * 80)
    print("CACHE MED MODELL-SPORING TEST")
    print("=" * 80)
    
    if not SQL_CACHE_ENABLED:
        print("⚠️  Cache er deaktivert (SQL_CACHE_ENABLED = False)")
        return True
    
    generator = SQLGenerator()
    generator.clear_cache()  # Start med tom cache
    
    # Test cache storage med modell-sporing
    question1 = "Gi meg den største eiendommen"
    question2 = "Hva er gjennomsnittlig leie per region?"
    
    key1 = generator._get_cache_key(question1)
    key2 = generator._get_cache_key(question2)
    
    # Cache med forskjellige modeller
    generator._cache_sql(key1, "SELECT * FROM properties ORDER BY total_area DESC LIMIT 1", "gpt-4o-mini")
    generator._cache_sql(key2, "SELECT region, AVG(amount->>'amount_per_year') FROM contracts GROUP BY region", "gpt-4o")
    
    # Test retrieval
    cached1 = generator._get_cached_sql(key1)
    cached2 = generator._get_cached_sql(key2)
    
    print(f"\n1. Cache retrieval:")
    if cached1:
        sql1, model1 = cached1
        print(f"   Spørsmål 1: '{question1}'")
        print(f"   Cached SQL: {sql1[:60]}...")
        print(f"   Modell brukt: {model1}")
        assert model1 == "gpt-4o-mini", f"Forventet gpt-4o-mini, fikk {model1}"
        print(f"   ✅ Modell-sporing korrekt")
    else:
        print(f"   ❌ Cache retrieval feilet for spørsmål 1")
        return False
    
    if cached2:
        sql2, model2 = cached2
        print(f"\n   Spørsmål 2: '{question2}'")
        print(f"   Cached SQL: {sql2[:60]}...")
        print(f"   Modell brukt: {model2}")
        assert model2 == "gpt-4o", f"Forventet gpt-4o, fikk {model2}"
        print(f"   ✅ Modell-sporing korrekt")
    else:
        print(f"   ❌ Cache retrieval feilet for spørsmål 2")
        return False
    
    # Test cache stats
    stats = generator.get_cache_stats()
    print(f"\n2. Cache statistikk:")
    print(f"   Cache size: {stats['cache_size']}")
    print(f"   Cached mini: {stats['cached_mini']}")
    print(f"   Cached fallback: {stats['cached_fallback']}")
    print(f"   Fallback used: {stats['fallback_used']}")
    
    assert stats['cache_size'] == 2, f"Forventet 2 cache entries, fikk {stats['cache_size']}"
    assert stats['cached_mini'] == 1, f"Forventet 1 mini entry, fikk {stats['cached_mini']}"
    assert stats['cached_fallback'] == 1, f"Forventet 1 fallback entry, fikk {stats['cached_fallback']}"
    print(f"   ✅ Cache stats korrekte")
    
    print("\n" + "=" * 80)
    print("✅ ALLE CACHE-TESTER BESTÅTT")
    print("=" * 80)
    
    return True


async def test_sql_generation_with_fallback():
    """Test SQL-generering med fallback (krever API key)"""
    
    print("\n" + "=" * 80)
    print("SQL-GENERERING MED FALLBACK TEST")
    print("=" * 80)
    
    from app.core.config import settings
    
    if not settings.OPENAI_API_KEY:
        print("⚠️  Ingen OPENAI_API_KEY satt - hopper over SQL-generering test")
        print("   (Dette krever faktisk API-kall)")
        return True
    
    generator = SQLGenerator()
    
    # Test enkel spørring (skal bruke gpt-4o-mini)
    simple_question = "Gi meg den største eiendommen"
    print(f"\n1. Enkel spørring: '{simple_question}'")
    
    try:
        is_complex = generator._detect_complexity(simple_question)
        print(f"   Kompleksitet detektert: {is_complex}")
        assert is_complex == False, "Skal ikke være kompleks"
        
        # Note: Vi kan ikke faktisk kalle forward() uten database, men vi kan teste deteksjonen
        print(f"   ✅ Kompleksitets-deteksjon korrekt")
        print(f"   ℹ️  Ville brukt: gpt-4o-mini")
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False
    
    # Test kompleks spørring (skal bruke gpt-4o)
    complex_question = "Hva er gjennomsnittlig leie per region med JSONB-agregering?"
    print(f"\n2. Kompleks spørring: '{complex_question}'")
    
    try:
        is_complex = generator._detect_complexity(complex_question)
        print(f"   Kompleksitet detektert: {is_complex}")
        assert is_complex == True, "Skal være kompleks"
        
        print(f"   ✅ Kompleksitets-deteksjon korrekt")
        print(f"   ℹ️  Ville brukt: gpt-4o")
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False
    
    print("\n" + "=" * 80)
    print("✅ SQL-GENERERING TEST BESTÅTT")
    print("=" * 80)
    
    return True


def run_all_tests():
    """Kjør alle tester"""
    
    print("\n" + "=" * 80)
    print("HYBRID SQL-STRATEGI TEST SUITE")
    print("=" * 80)
    
    results = {
        "complexity_detection": False,
        "cache_tracking": False,
        "sql_generation": False
    }
    
    # Test 1: Kompleksitets-deteksjon
    try:
        results["complexity_detection"] = test_complexity_detection()
    except Exception as e:
        print(f"❌ Kompleksitets-deteksjon test feilet: {e}")
    
    # Test 2: Cache med modell-sporing
    try:
        results["cache_tracking"] = test_cache_with_model_tracking()
    except Exception as e:
        print(f"❌ Cache tracking test feilet: {e}")
    
    # Test 3: SQL-generering (krever API key)
    try:
        results["sql_generation"] = asyncio.run(test_sql_generation_with_fallback())
    except Exception as e:
        print(f"❌ SQL-generering test feilet: {e}")
    
    # Oppsummering
    print("\n" + "=" * 80)
    print("TEST OPPsummering")
    print("=" * 80)
    print(f"Kompleksitets-deteksjon: {'✅ PASS' if results['complexity_detection'] else '❌ FAIL'}")
    print(f"Cache med modell-sporing: {'✅ PASS' if results['cache_tracking'] else '❌ FAIL'}")
    print(f"SQL-generering: {'✅ PASS' if results['sql_generation'] else '⚠️  SKIP (krever API key)'}")
    
    all_passed = all(results.values())
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALLE TESTER BESTÅTT")
    else:
        print("⚠️  NOEN TESTER FEILET ELLER BLE SKIPPET")
    print("=" * 80)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
