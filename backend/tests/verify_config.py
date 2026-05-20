
import os
import sys
import pytest
from pydantic import ValidationError

# Set minimal valid env vars BEFORE importing config to avoid crash on module level instantiation
os.environ["POSTGRES_SERVER"] = "localhost"
os.environ["POSTGRES_USER"] = "postgres"
os.environ["POSTGRES_DB"] = "testdb"
# OPENAI_API_KEY is optional if we don't trigger that validator yet or if defaults allow it?
# The validator I added checks: if v and len(v) < 10. Default is None. So it should pass if None.
# BUT wait, does my validator running on None?
# @field_validator("OPENAI_API_KEY", mode="after") receives None? yes.
# if v and len(v) < 10: None is falsy, so it passes.

from app.core.config import Settings

def test_cors_validation():
    # Test valid string
    os.environ["BACKEND_CORS_ORIGINS"] = "http://localhost:3000,https://example.com"
    settings = Settings(_env_file=None)
    assert "https://example.com" in settings.BACKEND_CORS_ORIGINS
    
def test_openai_key_validation():
    # Test short key
    os.environ["OPENAI_API_KEY"] = "short"
    try:
        Settings(_env_file=None)
        assert False, "Should have raised ValueError"
    except ValidationError as e:
        assert "OPENAI_API_KEY seems too short" in str(e)
        
    # Test valid key
    os.environ["OPENAI_API_KEY"] = "sk-proj-1234567890abcdef"
    settings = Settings(_env_file=None)
    assert settings.OPENAI_API_KEY == "sk-proj-1234567890abcdef"

def test_database_validation():
    # Helper to check validation fails when cleared
    old_server = os.environ.get("POSTGRES_SERVER")
    os.environ["POSTGRES_SERVER"] = ""
    try:
        Settings(_env_file=None)
        assert False, "Should have raised ValueError for empty POSTGRES_SERVER"
    except ValidationError as e:
        assert "class_name" not in str(e) # specific check?
        # The error message from my validator is "{info.field_name} cannot be empty."
        assert "POSTGRES_SERVER cannot be empty" in str(e)
    finally:
        if old_server:
            os.environ["POSTGRES_SERVER"] = old_server

if __name__ == "__main__":
    print("Running manual config checks...")
    try:
        test_openai_key_validation()
        print("✅ OpenAI Key Validation Passed")
    except Exception as e:
        print(f"❌ OpenAI Key Validation Failed: {e}")

    try:
        test_database_validation()
        print("✅ Database Validation Passed")
    except Exception as e:
        print(f"❌ Database Validation Failed: {e}")
        
    try:
        test_cors_validation()
        print("✅ CORS Validation Passed")
    except Exception as e:
        print(f"❌ CORS Validation Failed: {e}")
