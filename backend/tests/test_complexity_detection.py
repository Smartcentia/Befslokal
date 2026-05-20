"""
Test kompleksitets-deteksjon for Hybrid SQL-strategi
(Uten DSPy-avhengigheter)
"""

import sys
import os
import re

# Legg til backend i path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def detect_complexity(question: str) -> bool:
    """
    Detekterer om spørsmålet krever kompleks SQL (JSONB, JOINs, aggregering).
    Kopiert fra sql_generator.py for testing uten DSPy.
    """
    question_lower = question.lower()
    
    # Kompleksitets-indikatorer
    complexity_keywords = [
        # JSONB-operasjoner
        "jsonb", "external_data", "amount->>", "->>'", "->'",
        # Aggregering
        "gjennomsnitt", "snitt", "total", "sum", "antall", "count", "avg", "sum",
        "sammenlign", "sammenligning", "sammenligne",
        # JOINs (implisitt)
        "kombiner", "kombinere", "sammen", "per region", "per eiendom",
        "gruppe", "gruppere", "fordelt på",
        # Komplekse spørringer
        "kompleks", "avansert", "detaljert", "dybde", "dybdeanalyse"
    ]
    
    # Sjekk om spørsmålet inneholder kompleksitets-indikatorer
    is_complex = any(keyword in question_lower for keyword in complexity_keywords)
    
    # Ekstra sjekk: Hvis spørsmålet er langt (>100 ord), kan det være komplekst
    word_count = len(question.split())
    if word_count > 100:
        is_complex = True
    
    return is_complex


def test_complexity_detection():
    """Test at kompleksitets-deteksjon fungerer korrekt"""
    
    print("=" * 80)
    print("KOMPLEKSITETS-DETEKSJON TEST")
    print("=" * 80)
    
    test_cases = [
        {
            "question": "Gi meg den største eiendommen",
            "expected_complex": False,
            "reason": "Enkel SELECT med ORDER BY"
        },
        {
            "question": "Hva er gjennomsnittlig leie per region?",
            "expected_complex": True,
            "reason": "Aggregering (gjennomsnitt) + per region"
        },
        {
            "question": "Sammenlign kostnader mellom regionene",
            "expected_complex": True,
            "reason": "Sammenlign + implisitt JOIN"
        },
        {
            "question": "Hvor ligger Storgata 10?",
            "expected_complex": False,
            "reason": "Enkel lookup"
        },
        {
            "question": "Hva er total årlig leie fra amount JSONB-feltet?",
            "expected_complex": True,
            "reason": "JSONB-operasjon (amount->>) + total"
        },
        {
            "question": "Finn eiendommer med finansiell data i external_data->'financials'",
            "expected_complex": True,
            "reason": "Nested JSONB-operasjon (external_data)"
        },
        {
            "question": "Vis meg alle aktive kontrakter",
            "expected_complex": False,
            "reason": "Enkel SELECT med WHERE"
        },
        {
            "question": "Grupper eiendommer per region og beregn gjennomsnittlig kostnad",
            "expected_complex": True,
            "reason": "Gruppere + gjennomsnittlig"
        },
        {
            "question": "Hva er summen av alle kontrakter?",
            "expected_complex": True,
            "reason": "Aggregering (summen)"
        },
        {
            "question": "Tell antall eiendommer",
            "expected_complex": True,
            "reason": "Aggregering (antall/count)"
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] {test_case['question']}")
        print(f"  Forventet: {'✅ Kompleks' if test_case['expected_complex'] else '❌ Enkel'}")
        print(f"  Grunn: {test_case['reason']}")
        
        try:
            is_complex = detect_complexity(test_case['question'])
            detected_str = '✅ Kompleks' if is_complex else '❌ Enkel'
            print(f"  Detektert: {detected_str}")
            
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
    
    if failed == 0:
        print("✅ ALLE TESTER BESTÅTT")
    else:
        print("❌ NOEN TESTER FEILET")
    
    print("=" * 80)
    
    return failed == 0


def test_keyword_detection():
    """Test at spesifikke keywords detekteres korrekt"""
    
    print("\n" + "=" * 80)
    print("KEYWORD-DETEKSJON TEST")
    print("=" * 80)
    
    keyword_tests = [
        ("jsonb", True),
        ("external_data", True),
        ("amount->>", True),
        ("->>'", True),
        ("gjennomsnitt", True),
        ("snitt", True),
        ("total", True),
        ("sum", True),
        ("antall", True),
        ("sammenlign", True),
        ("per region", True),
        ("gruppe", True),
        ("enkel spørring", False),  # Ingen keywords
        ("hvor er", False),  # Ingen keywords
    ]
    
    passed = 0
    failed = 0
    
    for keyword, expected in keyword_tests:
        question = f"Spørsmål med {keyword}"
        is_complex = detect_complexity(question)
        
        status = "✅" if is_complex == expected else "❌"
        print(f"{status} Keyword '{keyword}': {'Kompleks' if is_complex else 'Enkel'} (forventet: {'Kompleks' if expected else 'Enkel'})")
        
        if is_complex == expected:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"RESULTAT: {passed}/{len(keyword_tests)} tester bestått")
    print(f"Feilet: {failed}")
    print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("HYBRID SQL-STRATEGI - KOMPLEKSITETS-DETEKSJON TEST")
    print("=" * 80)
    
    test1_passed = test_complexity_detection()
    test2_passed = test_keyword_detection()
    
    all_passed = test1_passed and test2_passed
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALLE TESTER BESTÅTT")
    else:
        print("❌ NOEN TESTER FEILET")
    print("=" * 80)
    
    sys.exit(0 if all_passed else 1)
