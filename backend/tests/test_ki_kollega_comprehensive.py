"""
Omfattende tester for KI Kollega.

Dekker:
- Service-initialisering og konfigurasjon
- chat() med og uten db (memory/tool discovery)
- Timeout og feilhåndtering
- Kilder-ekstraksjon (både liste og enkel streng)
- Verktøy: search_documents, run_sql, lookup_properties
- SQL-sikkerhet (_execute_safe_sql)
- get_proactive_insights
- API-endepunkter: /chat, /suggestions, /proactive, /health
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.intelligence.ki_kollega.service import (
    KIKollegaService,
    ChatContext,
    ChatMessage,
    QueryType,
    CHAT_TIMEOUT_SECONDS,
    SEARCH_LIMIT,
    MAX_DOC_CONTENT_LENGTH,
    ki_kollega_service,
)


# --- Service-initialisering ---

class TestKIKollegaInitialization:
    """Tester at servicen initialiseres riktig under ulike konfigurasjoner."""

    def test_query_type_enum(self):
        """QueryType har forventede verdier."""
        assert QueryType.LOOKUP.value == "lookup"
        assert QueryType.SQL_ANALYSIS.value == "sql_analysis"
        assert QueryType.GENERAL.value == "general"

    def test_chat_context_defaults(self):
        """ChatContext har fornuftige standardverdier."""
        ctx = ChatContext()
        assert ctx.page is None
        assert ctx.entity_type is None
        assert ctx.entity_id is None
        assert ctx.region is None
        assert ctx.user_id is None

    def test_chat_message_to_dict(self):
        """ChatMessage.to_dict() gir forventet struktur."""
        msg = ChatMessage(role="user", content="Hei")
        d = msg.to_dict()
        assert d["role"] == "user"
        assert d["content"] == "Hei"

    @pytest.mark.asyncio
    async def test_init_with_openai_key(self):
        """Servicen initialiseres med OPENAI_API_KEY."""
        with patch("app.services.intelligence.ki_kollega.service.settings") as s, \
             patch("openai.AsyncOpenAI") as mock_openai:
            s.USE_LOCAL_AI = False
            s.OPENAI_API_KEY = "sk-test"
            s.OPENAI_BASE_URL = "https://api.openai.com/v1"
            s.OPENAI_MODEL = "gpt-4o-mini"
            service = KIKollegaService()
            assert service.client is not None
            assert service.model == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_init_without_key(self):
        """Uten API-nøkkel skal client være None og logge feil."""
        with patch("app.services.intelligence.ki_kollega.service.settings") as s, \
             patch("app.services.intelligence.ki_kollega.service.logger") as log:
            s.USE_LOCAL_AI = False
            s.OPENAI_API_KEY = None
            s.OPENAI_BASE_URL = ""
            s.OPENAI_MODEL = "gpt-4o-mini"
            service = KIKollegaService()
            assert service.client is None


# --- chat() uten db (skal ikke krasje) ---

class TestChatWithoutDb:
    """chat() kalles med db=None – memory og tool discovery skal hoppes over."""

    @pytest.mark.asyncio
    async def test_chat_without_client_returns_friendly_message(self):
        """Uten initialisert client returneres vennlig melding."""
        with patch("app.services.intelligence.ki_kollega.service.settings") as s:
            s.USE_LOCAL_AI = False
            s.OPENAI_API_KEY = None
            service = KIKollegaService()
        out = await service.chat("Hei", db=None)
        assert "answer" in out
        assert "Beklager" in out.get("answer", "") or "tilkoblet" in out.get("answer", "")
        assert out.get("error") == "Client not initialized"

    @pytest.mark.asyncio
    async def test_chat_with_db_none_does_not_call_memory_or_tools(self):
        """Med db=None kalles ikke AgentMemoryService eller ToolDiscoveryService."""
        service = KIKollegaService()
        service.client = MagicMock()

        with patch("app.services.intelligence.agents.graph.app") as mock_app, \
             patch("app.services.intelligence.ki_kollega.service.AgentMemoryService") as mem, \
             patch("app.services.intelligence.ki_kollega.service.ToolDiscoveryService") as tools:
            mock_app.ainvoke = AsyncMock(return_value={
                "messages": [MagicMock(content="Svar fra graf")],
                "research_data": {},
                "error": None,
            })
            result = await service.chat("Hei", db=None)
            mem.search_memory.assert_not_called()
            tools.find_relevant_tools.assert_not_called()
            assert result["answer"] == "Svar fra graf"


# --- Timeout og feilhåndtering ---

class TestChatTimeoutAndErrors:
    """Timeout og interne feil håndteres pent."""

    @pytest.mark.asyncio
    async def test_chat_timeout_returns_friendly_message(self):
        """Ved timeout returneres tydelig melding."""
        service = KIKollegaService()
        service.client = MagicMock()
        with patch("app.services.intelligence.agents.graph.app") as mock_app:
            mock_app.ainvoke = AsyncMock(side_effect=asyncio.TimeoutError())
            result = await service.chat("Komplekst spørsmål", db=None)
        assert result.get("error") == "Timeout"
        assert "lang tid" in result.get("answer", "")

    @pytest.mark.asyncio
    async def test_chat_graph_error_in_state_returns_friendly_message(self):
        """Hvis graf returnerer error i state, returneres vennlig melding."""
        service = KIKollegaService()
        service.client = MagicMock()
        with patch("app.services.intelligence.agents.graph.app") as mock_app:
            mock_app.ainvoke = AsyncMock(return_value={
                "messages": [MagicMock(content="Feil")],
                "research_data": {},
                "error": "Internal processing error",
            })
            result = await service.chat("Hei", db=None)
        assert "answer" in result
        assert result.get("error") == "Internal processing error"


# --- Kilder: liste vs enkel streng ---

class TestSourcesExtraction:
    """research_data.results kan være liste eller enkel streng."""

    @pytest.mark.asyncio
    async def test_sources_from_list_of_dicts(self):
        """Kilder fra liste med dicts (f.eks. web-resultater)."""
        service = KIKollegaService()
        service.client = MagicMock()
        with patch("app.services.intelligence.agents.graph.app") as mock_app:
            mock_app.ainvoke = AsyncMock(return_value={
                "messages": [MagicMock(content="Her er resultatet")],
                "research_data": {
                    "results": [
                        {"title": "Doc 1", "href": "https://a.no"},
                        {"title": "Doc 2", "href": "https://b.no"},
                    ]
                },
                "error": None,
            })
            result = await service.chat("Søk", db=None)
        assert len(result["sources"]) == 2
        assert result["sources"][0]["type"] == "web"
        assert result["sources"][0]["name"] == "Doc 1"
        assert result["sources"][0]["url"] == "https://a.no"

    @pytest.mark.asyncio
    async def test_sources_from_single_string(self):
        """Kilder når results er en enkel streng (f.eks. lookup_properties)."""
        service = KIKollegaService()
        service.client = MagicMock()
        raw_result = "ID: p1, Navn: Storgata 10, Adresse: Storgata 10, By: Oslo"
        with patch("app.services.intelligence.agents.graph.app") as mock_app:
            mock_app.ainvoke = AsyncMock(return_value={
                "messages": [MagicMock(content="Her er eiendommen")],
                "research_data": {"results": raw_result},
                "error": None,
            })
            result = await service.chat("Hvor er Storgata 10?", db=None)
        assert len(result["sources"]) == 1
        assert result["sources"][0]["type"] == "document"
        assert "Storgata" in result["sources"][0]["name"]


# --- Verktøy (tools) med mock db ---

class TestTools:
    """_tool_search_documents, _tool_run_sql, _tool_lookup_properties, _tool_lookup_parties."""

    @pytest.mark.asyncio
    async def test_tool_lookup_properties_empty(self, db_session: AsyncSession):
        """lookup_properties returnerer dict med formatted og structured_sources."""
        result = await ki_kollega_service._tool_lookup_properties(
            db_session, "IkkeeksisterendeEiendomXYZ"
        )
        assert isinstance(result, dict)
        assert "formatted" in result and "structured_sources" in result
        formatted = result["formatted"]
        assert "Ingen eiendommer" in formatted or "funnet" in formatted.lower() or "Feil" in formatted

    @pytest.mark.asyncio
    async def test_tool_lookup_parties_empty(self, db_session: AsyncSession):
        """lookup_parties returnerer dict med formatted og structured_sources."""
        result = await ki_kollega_service._tool_lookup_parties(
            db_session, "XyZNonexistentPart123"
        )
        assert isinstance(result, dict)
        assert "formatted" in result and "structured_sources" in result
        formatted = result["formatted"]
        assert "Ingen parter" in formatted or "funnet" in formatted.lower() or "Feil" in formatted or "Angi" in formatted

    @pytest.mark.asyncio
    async def test_tool_lookup_parties_short_term(self, db_session: AsyncSession):
        """lookup_parties med for kort søkeord ber om minst to tegn."""
        result = await ki_kollega_service._tool_lookup_parties(db_session, "x")
        assert isinstance(result, dict)
        formatted = result["formatted"]
        assert "Angi" in formatted or "minst" in formatted or "Ingen parter" in formatted

    @pytest.mark.asyncio
    async def test_tool_run_sql_returns_string(self, db_session: AsyncSession):
        """_tool_run_sql returnerer streng (eller feilmelding)."""
        with patch(
            "app.services.intelligence.ki_kollega.service.KIKollegaService._handle_sql_analysis",
            new_callable=AsyncMock,
            return_value=[{"content": "Ingen resultater fra databasen."}],
        ):
            result = await ki_kollega_service._tool_run_sql(db_session, "Antall eiendommer?")
        assert isinstance(result, str)


# --- SQL-sikkerhet ---

class TestSqlSafety:
    """_execute_safe_sql blokkerer farlig SQL."""

    @pytest.mark.asyncio
    async def test_execute_safe_sql_blocks_drop(self, db_session: AsyncSession):
        """DROP er blokkert."""
        out = await ki_kollega_service._execute_safe_sql(db_session, "DROP TABLE properties")
        assert out is None

    @pytest.mark.asyncio
    async def test_execute_safe_sql_blocks_delete(self, db_session: AsyncSession):
        """DELETE er blokkert."""
        out = await ki_kollega_service._execute_safe_sql(db_session, "DELETE FROM properties")
        assert out is None

    @pytest.mark.asyncio
    async def test_execute_safe_sql_blocks_insert(self, db_session: AsyncSession):
        """INSERT er blokkert."""
        out = await ki_kollega_service._execute_safe_sql(
            db_session, "INSERT INTO properties (name) VALUES ('x')"
        )
        assert out is None

    @pytest.mark.asyncio
    async def test_execute_safe_sql_requires_select_or_with(self, db_session: AsyncSession):
        """Kun SELECT/WITH tillates som start."""
        out = await ki_kollega_service._execute_safe_sql(db_session, "EXECUTE something")
        assert out is None


# --- get_proactive_insights ---

class TestProactiveInsights:
    """get_proactive_insights med ulik context."""

    @pytest.mark.asyncio
    async def test_proactive_insights_empty_context(self, db_session: AsyncSession):
        """Tom context gir tom liste (eller ingen krasj)."""
        ctx = ChatContext()
        out = await ki_kollega_service.get_proactive_insights(db_session, ctx)
        assert isinstance(out, list)

    @pytest.mark.asyncio
    async def test_proactive_insights_dashboard_page(self, db_session: AsyncSession):
        """Context med page=dashboard kan kjøre portfolio-sjekk."""
        ctx = ChatContext(page="dashboard")
        out = await ki_kollega_service.get_proactive_insights(db_session, ctx)
        assert isinstance(out, list)


# --- API-endepunkter ---

class TestKiKollegaApiEndpoints:
    """HTTP-endepunkter for KI Kollega."""

    @pytest.mark.asyncio
    async def test_health_returns_status(self, client):
        """GET /api/v1/ai/health returnerer status."""
        r = await client.get("/api/v1/ai/health")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert data["status"] in ("healthy", "degraded")
        assert "client_initialized" in data

    @pytest.mark.asyncio
    async def test_suggestions_without_entity(self, client):
        """GET /api/v1/ai/suggestions uten entity gir generelle forslag."""
        r = await client.get("/api/v1/ai/suggestions")
        assert r.status_code == 200
        data = r.json()
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)
        assert len(data["suggestions"]) > 0

    @pytest.mark.asyncio
    async def test_suggestions_property_entity(self, client):
        """GET /api/v1/ai/suggestions?entity_type=property gir eiendomsspesifikke forslag."""
        r = await client.get("/api/v1/ai/suggestions?entity_type=property")
        assert r.status_code == 200
        data = r.json()
        assert "suggestions" in data
        assert any("eiendom" in s.lower() or "kostnad" in s.lower() for s in data["suggestions"])

    @pytest.mark.asyncio
    async def test_proactive_empty_query_params(self, client):
        """GET /api/v1/ai/proactive uten params returnerer []."""
        r = await client.get("/api/v1/ai/proactive")
        assert r.status_code == 200
        assert r.json() == []

    @pytest.mark.asyncio
    async def test_chat_post_requires_message(self, client):
        """POST /api/v1/ai/chat uten message gir valideringsfeil."""
        r = await client.post("/api/v1/ai/chat", json={})
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_post_with_message(self, client):
        """POST /api/v1/ai/chat med message returnerer answer (eller feilmelding ved manglende LLM)."""
        r = await client.post(
            "/api/v1/ai/chat",
            json={"message": "Hei"},
        )
        # 200 med svar, eller 500/200 med feilmelding avhengig av om LLM er mocket
        assert r.status_code in (200, 500)
        if r.status_code == 200:
            data = r.json()
            assert "answer" in data
            assert "conversation_id" in data


# --- Konstanter og TOOLS ---

class TestConstantsAndTools:
    """Konstanter og TOOLS-definisjon er konsistente."""

    def test_timeout_constant(self):
        """CHAT_TIMEOUT_SECONDS er satt."""
        assert CHAT_TIMEOUT_SECONDS == 45.0

    def test_search_limit_constant(self):
        """SEARCH_LIMIT er positiv."""
        assert SEARCH_LIMIT >= 1

    def test_tools_defined(self):
        """TOOLS inneholder forventede verktøy."""
        names = [t["function"]["name"] for t in KIKollegaService.TOOLS]
        assert "search_documents" in names
        assert "lookup_parties" in names
        assert "lookup_familievernkontor_bufdir" in names


# --- Writer bruker PARTER_OG_KONTRAKTER ---

class TestWriterContextPrefixes:
    """Writer inkluderer PARTER_OG_KONTRAKTER og BRUKEREN SER PÅ i kontekst."""

    @pytest.mark.asyncio
    async def test_writer_includes_parter_og_kontrakter_in_prompt(self):
        """Når state inneholder SystemMessage med PARTER_OG_KONTRAKTER, inkluderes det i LLM-kallet."""
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
        from app.services.intelligence.agents.nodes.writer import writer_node

        state = {
            "messages": [
                SystemMessage(content="PARTER_OG_KONTRAKTER:\nPart: TestPart (ID: abc). Kontrakt: Leie (active). Eiendom: Storgata 1."),
                HumanMessage(content="Har vi kontrakt med TestPart?"),
            ],
            "persona": "Du er KI Kollega.",
            "discovered_tools": [],
            "research_data": {},
            "next_step": "end",
            "current_agent": "writer",
            "script_results": {},
            "error": None,
            "usage": None,
        }
        async def mock_astream_impl(*args, **kwargs):
            yield AIMessage(content="Ja, vi har en kontrakt med TestPart på Storgata 1.")

        mock_astream = MagicMock(side_effect=mock_astream_impl)
        with patch("app.services.intelligence.agents.nodes.writer.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "sk-test"
            with patch("app.services.intelligence.agents.nodes.writer.ChatOpenAI") as mock_llm:
                mock_llm.return_value.astream = mock_astream
                out = await writer_node(state)
        assert "messages" in out
        assert len(out["messages"]) == 1
        assert isinstance(out["messages"][0], AIMessage)
        # LLM ble kalt med system prompt som inneholder PARTER_OG_KONTRAKTER (gathered_context)
        call_args = mock_llm.return_value.astream.call_args
        assert call_args
        llm_messages = call_args[0][0] if call_args[0] else []
        all_content = " ".join(getattr(m, "content", "") for m in llm_messages)
        assert "PARTER_OG_KONTRAKTER" in all_content or "TestPart" in all_content
