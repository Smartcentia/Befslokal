import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.intelligence.ki_kollega.service import KIKollegaService, ChatContext

@pytest.mark.asyncio
async def test_ki_kollega_initialization():
    """Test that service initializes correctly."""
    # Patch where settings is used, AND mock AsyncOpenAI to avoid real network/init basics
    with patch("app.services.intelligence.ki_kollega.service.settings") as mock_settings, \
         patch("openai.AsyncOpenAI") as mock_openai:
        
        mock_settings.USE_LOCAL_AI = False
        mock_settings.OPENAI_API_KEY = "sk-test-key"
        mock_settings.OPENAI_BASE_URL = "https://api.openai.com/v1"
        mock_settings.OPENAI_MODEL = "gpt-4o"
        
        service = KIKollegaService()
        assert service.client is not None
        assert service.model == "gpt-4o"

@pytest.mark.asyncio
async def test_chat_timeout():
    """Test that chat handles timeouts gracefully."""
    service = KIKollegaService()
    service.client = MagicMock() # Mock initialized client
    
    # Mock the graph app execution to hang
    async def mock_hang(*args, **kwargs):
        import asyncio
        await asyncio.sleep(60) 
        return {}

    # Correct patch path since 'app' is imported FROM app.services.intelligence.agents.graph
    with patch("app.services.intelligence.agents.graph.app") as mock_app, \
         patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
        
        mock_app.ainvoke = AsyncMock(side_effect=mock_hang)
        
        # We need to ensure logic reaches the graph invocation
        # Passes: client check (mocked above)
        
        response = await service.chat("Hello")
             
        assert response["error"] == "Timeout"
        assert "Forespørselen tok for lang tid" in response["answer"]

@pytest.mark.asyncio
async def test_chat_success():
    """Test a successful chat interaction."""
    service = KIKollegaService()
    service.client = MagicMock()
    
    # Mock successful state return
    mock_state = {
        "messages": [MagicMock(content="Hello user!")],
        "research_data": {
            "results": [{"title": "Test Doc", "href": "http://test.com"}]
        }
    }
    
    async def mock_invoke(*args, **kwargs):
        return mock_state

    # Correct patch path
    with patch("app.services.intelligence.agents.graph.app") as mock_app:
        mock_app.ainvoke = AsyncMock(side_effect=mock_invoke)
        
        # Execute
        response = await service.chat("Hi")
        
        assert response["answer"] == "Hello user!"
        assert len(response["sources"]) == 1
        assert response["sources"][0]["name"] == "Test Doc"


@pytest.mark.asyncio
async def test_chat_unified_success(db_session):
    """Test that chat_unified returns answer and extracts collected_sources."""
    from app.services.intelligence.ki_kollega.service import ki_kollega_service, ChatContext

    if not ki_kollega_service.client:
        pytest.skip("OpenAI client not initialized (missing API key)")

    # Mock the unified graph to return controlled state
    from langchain_core.messages import AIMessage, HumanMessage

    mock_state = {
        "messages": [
            HumanMessage(content="Hvilke eiendommer har vi?"),
            AIMessage(content="Vi har 3 eiendommer: [Test Eiendom](property:abc-123) med 1000 m²."),
        ],
        "collected_sources": [
            {"type": "property", "id": "abc-123", "name": "Test Eiendom"},
        ],
    }

    async def mock_ainvoke(inputs, config=None):
        return mock_state

    with patch("app.services.intelligence.unified_agent.create_unified_graph") as mock_create:
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(side_effect=mock_ainvoke)
        mock_create.return_value = mock_graph

        response = await ki_kollega_service.chat_unified(
            message="Hvilke eiendommer har vi?",
            context=ChatContext(page="/dashboard"),
            history=[],
            db=db_session,
        )

        assert response["answer"] == "Vi har 3 eiendommer: [Test Eiendom](property:abc-123) med 1000 m²."
        assert response["error"] is None
        assert len(response["sources"]) == 1
        assert response["sources"][0]["type"] == "property"
        assert response["sources"][0]["id"] == "abc-123"
        assert response["sources"][0]["name"] == "Test Eiendom"


@pytest.mark.asyncio
async def test_chat_unified_no_db_returns_error():
    """Test that chat_unified returns error when db is None."""
    from app.services.intelligence.ki_kollega.service import ki_kollega_service

    # Ensure client exists for the test
    with patch.object(ki_kollega_service, "client", MagicMock()):
        response = await ki_kollega_service.chat_unified(
            message="Hei",
            context=None,
            history=[],
            db=None,
        )

        assert response["error"] == "No database"
        assert "Database-tilkobling mangler" in response["answer"]
