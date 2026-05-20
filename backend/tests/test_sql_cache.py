"""
Test SQL cache funksjonalitet
"""

import sys
import os

# Legg til backend i path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.dspy.sql_generator import SQLGenerator, SQL_CACHE_ENABLED


def test_cache_basic():
    """Test grunnleggende cache-funksjonalitet"""
    
    print("=" * 80)
    print("SQL CACHE TEST")
    print("=" * 80)
    
    if not SQL_CACHE_ENABLED:
        print("⚠️  Cache er deaktivert (SQL_CACHE_ENABLED = False)")
        return
    
    generator = SQLGenerator()
    
    # Test cache key generering
    question1 = "Gi meg den største eiendommen"
    question2 = "Gi meg den største eiendommen"  # Samme spørsmål
    question3 = "GI MEG DEN STØRSTE EIENDOMMEN"  # Samme, men uppercase
    
    key1 = generator._get_cache_key(question1)
    key2 = generator._get_cache_key(question2)
    key3 = generator._get_cache_key(question3)
    
    print(f"\n1. Cache key generering:")
    print(f"   Spørsmål 1: '{question1}'")
    print(f"   Cache key: {key1}")
    print(f"   Spørsmål 2: '{question2}'")
    print(f"   Cache key: {key2}")
    print(f"   Spørsmål 3: '{question3}'")
    print(f"   Cache key: {key3}")
    
    assert key1 == key2 == key3, "Cache keys skal være like for samme spørsmål"
    print("   ✅ Cache keys er konsistente")
    
    # Test cache storage og retrieval
    test_sql = "SELECT * FROM properties ORDER BY total_area DESC LIMIT 1"
    generator._cache_sql(key1, test_sql)
    
    cached = generator._get_cached_sql(key1)
    assert cached == test_sql, "Cached SQL skal matche original"
    print(f"\n2. Cache storage/retrieval:")
    print(f"   ✅ SQL cached og hentet korrekt")
    
    # Test cache stats
    stats = generator.get_cache_stats()
    print(f"\n3. Cache statistikk:")
    print(f"   Cache enabled: {stats['cache_enabled']}")
    print(f"   Cache size: {stats['cache_size']}")
    print(f"   Cache max size: {stats['cache_max_size']}")
    print(f"   Cache hits: {stats['cache_hits']}")
    print(f"   Cache misses: {stats['cache_misses']}")
    print(f"   Hit rate: {stats['hit_rate_percent']}%")
    
    assert stats['cache_size'] == 1, "Cache skal inneholde 1 entry"
    print(f"   ✅ Cache stats er korrekte")
    
    # Test cache clearing
    generator.clear_cache()
    stats_after = generator.get_cache_stats()
    assert stats_after['cache_size'] == 0, "Cache skal være tom etter clear"
    assert stats_after['cache_hits'] == 0, "Cache hits skal være nullstilt"
    print(f"\n4. Cache clearing:")
    print(f"   ✅ Cache cleared korrekt")
    
    print("\n" + "=" * 80)
    print("✅ ALLE CACHE-TESTER BESTÅTT")
    print("=" * 80)


if __name__ == "__main__":
    test_cache_basic()
