# --- Pydantic V2 Monkeypatch for Semantic Kernel ---
try:
    import pydantic.networks
    if not hasattr(pydantic.networks, "Url"):
        from pydantic import AnyUrl
        pydantic.networks.Url = AnyUrl
except ImportError:
    pass
# ----------------------------------------------------

from semantic_kernel.memory.volatile_memory_store import VolatileMemoryStore
from semantic_kernel.connectors.ai.open_ai import OpenAITextEmbedding
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv("../.env") 
if not os.getenv("OPENAI_API_KEY"):
    load_dotenv(".env")

async def create_memory_store():
    # 1. Configure Embedding Service
    api_key = os.getenv("OPENAI_API_KEY") or settings.OPENAI_API_KEY
    embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    
    if not api_key:
        print("⚠️ Missing OPENAI_API_KEY. AI Lab memory will be disabled.")
        return None

    print(f"🧠 AI Lab Memory: Using OpenAI Embedding model: {embedding_model}")
    
    from semantic_kernel.connectors.ai.open_ai import OpenAITextEmbedding
    
    try:
        embedding_generator = OpenAITextEmbedding(
            service_id="openai_embedding",
            ai_model_id=embedding_model,
            api_key=api_key
        )

        # 2. Create Volatile Memory (RAM)
        memory = SemanticTextMemory(
            storage=VolatileMemoryStore(),
            embeddings_generator=embedding_generator
        )
        
        print(f"✅ AI Lab Memory Store initialized.")
        return memory
    except Exception as e:
        print(f"❌ Failed to initialize AI Lab Memory: {e}")
        return None
