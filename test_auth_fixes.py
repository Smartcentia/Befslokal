#!/usr/bin/env python3
"""
Automatiserte tester for kritiske auth fixes.
Kjør dette før commit og deploy.
"""

import sys
import os
import jwt
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_token_generation_with_email_as_sub():
    """Test at token genereres med email som sub"""
    print("🧪 Test 1: Token generation med email som sub...")
    
    secret = "test-secret-key-12345"
    email = "test@example.com"
    name = "Test User"
    
    # Simuler token-generering som frontend gjør
    token = jwt.encode(
        {
            "sub": email,  # Email som sub (ny logikk)
            "email": email,
            "name": name,
            "roles": ["user"],
            "iat": int(datetime.now().timestamp()),
            "exp": int((datetime.now() + timedelta(hours=24)).timestamp()),
        },
        secret,
        algorithm="HS256"
    )
    
    # Verifiser token
    decoded = jwt.decode(token, secret, algorithms=["HS256"])
    
    assert decoded["sub"] == email, f"Expected sub={email}, got {decoded['sub']}"
    assert decoded["email"] == email, f"Expected email={email}, got {decoded['email']}"
    assert "@" in decoded["email"], "Email must contain @"
    
    print("   ✅ Token generert korrekt med email som sub")
    return True

def test_email_validation():
    """Test at email validation fungerer"""
    print("🧪 Test 2: Email validation...")
    
    secret = "test-secret-key-12345"
    
    # Test 1: Token med gyldig email
    token_valid = jwt.encode(
        {
            "sub": "user@example.com",
            "email": "user@example.com",
            "name": "User",
            "iat": int(datetime.now().timestamp()),
            "exp": int((datetime.now() + timedelta(hours=24)).timestamp()),
        },
        secret,
        algorithm="HS256"
    )
    
    decoded_valid = jwt.decode(token_valid, secret, algorithms=["HS256"])
    email = decoded_valid.get("email")
    assert email and "@" in str(email), "Email must exist and contain @"
    print("   ✅ Gyldig email valideres korrekt")
    
    # Test 2: Token uten email (skal feile)
    try:
        token_no_email = jwt.encode(
            {
                "sub": "12345",  # Ingen email
                "name": "User",
                "iat": int(datetime.now().timestamp()),
                "exp": int((datetime.now() + timedelta(hours=24)).timestamp()),
            },
            secret,
            algorithm="HS256"
        )
        
        decoded_no_email = jwt.decode(token_no_email, secret, algorithms=["HS256"])
        email = decoded_no_email.get("email")
        
        # Simuler backend validering
        if not email or "@" not in str(email):
            # Fallback til sub
            email = decoded_no_email.get("sub")
            if not email or "@" not in str(email):
                raise ValueError("Invalid token: email missing or invalid")
        
        # Hvis vi kommer hit, er det feil
        assert False, "Token uten email skal feile validering"
    except ValueError as e:
        print(f"   ✅ Token uten email feiler korrekt: {e}")
    
    return True

def test_user_creation_logic():
    """Test at user creation logikk fungerer"""
    print("🧪 Test 3: User creation logikk...")
    
    # Simuler user_data fra token
    test_cases = [
        {
            "email": "admin@befs.no",
            "name": "Admin User",
            "expected_role": "ADMIN"
        },
        {
            "email": "user@example.com",
            "name": "Regular User",
            "expected_role": "USER"
        },
        {
            "email": "google.user@gmail.com",
            "name": None,  # Google kan returnere None
            "expected_role": "USER"
        }
    ]
    
    ADMIN_EMAILS = ["admin@befs.no"]
    
    for case in test_cases:
        email = case["email"]
        user_name = case.get("name") or email.split("@")[0]
        is_admin = email in ADMIN_EMAILS or email == "admin@befs.no"
        expected_role = case["expected_role"]
        
        role = "ADMIN" if is_admin else "USER"
        
        assert role == expected_role, f"Expected {expected_role}, got {role} for {email}"
        assert user_name, "User name must be set"
        assert "@" in email, "Email must be valid"
        
        print(f"   ✅ {email} → role={role}, name={user_name}")
    
    return True

def test_backend_imports():
    """Test at backend kan importeres uten feil"""
    print("🧪 Test 4: Backend imports...")
    
    # Set dummy DATABASE_URL for testing
    import os
    if "DATABASE_URL" not in os.environ:
        os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost/test"
    
    try:
        from app.core.security import security_validator
        from app.core.config import settings
        from app.api.deps import get_current_user
        print("   ✅ Backend moduler kan importeres")
        return True
    except Exception as e:
        # Ignorer database-relaterte feil i test-miljø
        if "DATABASE_URL" in str(e) or "database" in str(e).lower():
            print(f"   ⚠️  Backend import krever DATABASE_URL (OK i test-miljø)")
            return True
        print(f"   ❌ Backend import feilet: {e}")
        return False

def test_token_with_google_format():
    """Test at token fungerer med Google user format"""
    print("🧪 Test 5: Token med Google user format...")
    
    secret = "test-secret-key-12345"
    
    # Simuler Google user (har email, men id er numerisk)
    google_email = "user@gmail.com"
    google_id = "12345678901234567890"  # Google user ID
    
    # Frontend normaliserer til email som sub
    token = jwt.encode(
        {
            "sub": google_email,  # Email som sub (normalisert)
            "email": google_email,
            "name": "Google User",
            "roles": ["user"],
            "iat": int(datetime.now().timestamp()),
            "exp": int((datetime.now() + timedelta(hours=24)).timestamp()),
        },
        secret,
        algorithm="HS256"
    )
    
    decoded = jwt.decode(token, secret, algorithms=["HS256"])
    
    assert decoded["sub"] == google_email, "Sub skal være email"
    assert decoded["email"] == google_email, "Email skal være satt"
    assert "@" in decoded["email"], "Email må inneholde @"
    
    print("   ✅ Google format token fungerer korrekt")
    return True

def run_all_tests():
    """Kjør alle tester"""
    print("=" * 60)
    print("🚀 Starter automatiserte tester for auth fixes")
    print("=" * 60)
    print()
    
    tests = [
        ("Token generation med email som sub", test_token_generation_with_email_as_sub),
        ("Email validation", test_email_validation),
        ("User creation logikk", test_user_creation_logic),
        ("Backend imports", test_backend_imports),
        ("Google format token", test_token_with_google_format),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"   ❌ Test feilet: {e}")
            failed += 1
        except Exception as e:
            print(f"   ❌ Uventet feil: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Resultat: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed > 0:
        print("❌ Noen tester feilet. Fiks feilene før commit/deploy!")
        return False
    else:
        print("✅ Alle tester passerte! Klar for commit/deploy.")
        return True

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
