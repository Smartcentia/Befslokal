
import asyncio
import os
import sys
from unittest.mock import MagicMock

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

async def test_agent():
    # Set fake API key for initialization if not present
    if not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = "sk-placeholder"
    
    try:
        from app.services.intelligence.ki_kollega.service import ki_kollega_service
        from app.domains.core.models.user import User, UserRole
        
        print("Initializing service...")
        ki_kollega_service._initialize_client()
        
        # Mock user
        mock_user = MagicMock()
        mock_user.user_id = "test-user"
        mock_user.name = "Test User"
        mock_user.role = UserRole.ADMIN
        
        print("Testing chat_unified...")
        # We need a DB session for most internal tools, but let's see if it fails early
        # Passing None for db might trigger the "No database" error message
        result = await ki_kollega_service.chat_unified(
            message="Hei, hvem er du?",
            user=mock_user,
            db=None
        )
        
        print(f"Result: {result.get('answer')}")
        if result.get('error'):
            print(f"Error: {result.get('error')}")

    except Exception as e:
        print(f"FAILED with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent())
