import dspy
import os
import logging
import hashlib
import time
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.config import settings
from functools import lru_cache
from datetime import datetime, timedelta
from app.services.query_logging_service import QueryLoggingService
from app.services.confidence_scorer import ConfidenceScorer

logger = logging.getLogger(__name__)

# Cache-konfigurasjon
SQL_CACHE_ENABLED = True
SQL_CACHE_TTL_SECONDS = 3600  # 1 time
SQL_CACHE_MAX_SIZE = 100  # Maks antall cached entries

# Query cost limits (sikkerhet mot dyre queries)
MAX_QUERY_COST = 10000.0  # Maksimal tillatt query cost fra EXPLAIN
ENABLE_COST_LIMIT_CHECK = True  # Kan slås av for testing

# --- 1. SIGNATURES ---

class TextToSQL(dspy.Signature):
    """
    Oversetter et naturlig spørsmål til PostgreSQL SQL basert på et gitt databaseskjema.
    
    KRITISKE REGLER FOR JSONB-FELTER:
    
    1. JSONB-syntaks i PostgreSQL:
       - Hent tekstverdi: field->>'key' (returnerer TEXT)
       - Hent objekt/array: field->'key' (returnerer JSONB)
       - Nested: field->'parent'->>'child'
       - Array-element: field->0->>'key' (første element)
    
    2. Type-casting for JSONB-verdier (MÅ gjøres for sammenligning/agregering):
       - Til tall: (field->>'amount')::numeric eller (field->>'amount')::float
       - Til dato: (field->>'date')::date
       - Til boolean: (field->>'active')::boolean
    
    3. JSONB-eksempler fra contracts.amount:
       - Årlig leie: (amount->>'amount_per_year')::numeric
       - Månedlig leie: (amount->>'amount_per_month')::numeric
       - Aggregering: SUM((amount->>'amount_per_year')::numeric)
       - Gjennomsnitt: AVG((amount->>'amount_per_year')::numeric)
    
    4. JSONB-eksempler fra units.external_data:
       - Areal: (external_data->>'area')::float
       - Brukstype: external_data->>'usage_type'
       - Nested: external_data->'master_data'->>'area'
    
    5. JSONB-eksempler fra properties.external_data:
       - Finansiell data: external_data->'financials'->'transactions_2025'
       - Array-iterasjon: jsonb_array_elements(external_data->'financials'->'transactions_2025')
    
    6. BRUK AV SIDEKONTEKST (page_context):
       - Hvis page_context inneholder en ID (f.eks. property_id eller party_id), og brukeren spør om "denne", "her", "dette firmaet", osv:
       - Du SKAL legge til en WHERE-setning som filtrerer på denne ID-en.
       - Eksempel: Kontekst er "property with ID '123'". Spørsmål: "Hva er leien her?". 
         SQL: SELECT sum(...) FROM contracts WHERE property_id = '123'
    
    7. ALLTID VELG ID-KOLONNER FOR LENKER:
       - For at brukeren skal kunne klikke på resultatene, MÅ du inkludere ID-kolonner i SELECT-setningen.
       - Fra properties: Inkluder property_id.
       - Fra contracts: Inkluder contract_id.
       - Fra parties: Inkluder party_id.
       - Fra internal_control_cases: Inkluder case_id.
       - Fra gl_transactions: Inkluder property_id.
    
    ANDRE REGLER:
    - Generer KUN SQL (ingen markdown, ingen forklaring).
    - Bruk KUN SELECT (READ-ONLY).
    - Bruk ILIKE for tekstsøk.
    - Returner maks 10 rader med mindre annet er spurt om.
    - For NULL-sjekk: WHERE field IS NOT NULL eller WHERE field->>'key' IS NOT NULL

    8. AGGREGERING OG GRUPPERING (VIKTIG):
    - "Antall kontrakter per status":
      SELECT status, COUNT(*) as count FROM contracts GROUP BY status ORDER BY count DESC
    
    - "Snitt leie per region":
      SELECT p.region, AVG((c.amount->>'amount_per_year')::numeric) as avg_rent
      FROM contracts c
      JOIN units u ON c.unit_id = u.unit_id
      JOIN properties p ON u.property_id = p.property_id
      GROUP BY p.region
      ORDER BY avg_rent DESC

    - "Totalt areal per kommune":
      SELECT municipality, SUM(total_area) as total_area
      FROM properties
      WHERE municipality IS NOT NULL
      GROUP BY municipality
      ORDER BY total_area DESC
    """
    
    schema_context = dspy.InputField(desc="PostgreSQL CREATE TABLE statements, relasjoner og JSONB-eksempler")
    question = dspy.InputField(desc="Brukerens spørsmål på norsk")
    page_context = dspy.InputField(desc="Kontekst om siden brukeren ser på (f.eks. ID til eiendom/part). Bruk dette for å løse referanser som 'her' eller 'denne'.")
    sql_query = dspy.OutputField(desc="Gyldig PostgreSQL SQL spørring med korrekt JSONB-syntaks")


class FinancialAssessment(dspy.Signature):
    """Du er regnskapsekspert for Bufetat eiendomsforvaltning.
    Analyser tallene fra SQL-spørringen og gi en kortfattet forretningsvurdering.

    REGLER:
    - Svar med 2-4 setninger på norsk.
    - Vær konkret: nevn eiendomsnavn og konkrete tall der det er relevant.
    - Nevn: hva tallene betyr i praksis, avvik fra budsjett (hvis kontekst finnes), mulige årsaker.
    - IKKE gjenta rådataene – tolk og vurder dem.
    - Eksempel: "Tærudgata 16 har totale GL-kostnader på 4,2 MNOK i 2025.
                 Leie til Statsbygg utgjør 72% av kostnadene.
                 Dette er innenfor normal husleieandel for porteføljen."
    """
    question = dspy.InputField(desc="Brukerens opprinnelige spørsmål")
    sql_results_json = dspy.InputField(desc="JSON-liste med topp 10 rader fra SQL-resultatet")
    business_context = dspy.InputField(desc="Forretningskontekst: eiendom, periode, budsjett om tilgjengelig")
    assessment = dspy.OutputField(desc="Forretningsvurdering på norsk: tolkning, avvik, årsaker (2-4 setninger)")

# --- 2. VALIDATOR ---

class SQLValidator:
    """Sikrer at generert SQL er trygg og gyldig."""
    
    FORBIDDEN_KEYWORDS = [
        "DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "TRUNCATE", 
        "GRANT", "REVOKE", "EXECUTE", "CREATE", "REPLACE"
    ]

    @staticmethod
    def validate(sql: str) -> bool:
        # 1. Clean formatting
        clean_sql = sql.strip().strip('`').replace('sql\n', '')
        upper_sql = clean_sql.upper()
        
        # 2. Must start with SELECT or WITH
        if not (upper_sql.startswith("SELECT") or upper_sql.startswith("WITH")):
            logger.warning(f"Blocked SQL: Må starte med SELECT/WITH. Input: {sql[:50]}...")
            return False

        # 3. Check forbidden words
        for kw in SQLValidator.FORBIDDEN_KEYWORDS:
            # Check for whole words to avoid blocking valid columns like 'updated_at'
            if f" {kw} " in f" {upper_sql} " or f"\n{kw}" in upper_sql:
                logger.warning(f"Blocked SQL: Inneholder forbudt ord '{kw}'. Input: {sql[:50]}...")
                return False
                
        return True

    @staticmethod
    def clean(sql: str) -> str:
        s = sql.strip()
        if s.startswith("```sql"): s = s[6:]
        if s.startswith("```"): s = s[3:]
        if s.endswith("```"): s = s[:-3]
        return s.strip()

# --- 3. GENERATOR MODULE ---

class SQLGenerator(dspy.Module):
    def __init__(self):
        super().__init__()
        
        # Configure LM
        try:
            # Use settings for consistency
            api_key = settings.OPENAI_API_KEY
            model_name = settings.OPENAI_MODEL  # Standard: gpt-4o-mini
            
            if api_key:
                # Configure DSPy with standard OpenAI (gpt-4o-mini)
                self.primary_lm = dspy.LM(model=f"openai/{model_name}", api_key=api_key)
                dspy.configure(lm=self.primary_lm)
                logger.info(f"DSPy initialized with {model_name} (primary)")
                
                # Configure fallback LM (gpt-4o) for complex queries
                self.fallback_lm = dspy.LM(model="openai/gpt-4o", api_key=api_key)
                logger.info("DSPy fallback model (gpt-4o) configured")
            else:
                logger.warning("DSPy initialized without API KEY (Mock mode possible)")
                self.primary_lm = None
                self.fallback_lm = None
                
        except Exception as e:
            logger.error(f"Failed to init DSPy LM: {e}")
            self.primary_lm = None
            self.fallback_lm = None

        self.generate_mini = dspy.Predict(TextToSQL)  # Raskere enn ChainOfThought
        self.generate_fallback = dspy.ChainOfThought(TextToSQL)  # Bruk CoT kun ved fallback/kompleksitet
        self.schema_cache = None
        
        # SQL Cache: question_hash -> (sql, timestamp, model_used)
        self._sql_cache: Dict[str, tuple[str, datetime, str]] = {}
        self._cache_hits = 0
        self._cache_misses = 0
        self._fallback_used = 0  # Track how often we use fallback

    def _get_schema(self) -> str:
        if self.schema_cache:
            return self.schema_cache
            
        try:
            # Load schema from file or define minimal fallback
            schema_path = os.path.join(os.path.dirname(__file__), "../../config/SCHEMA.md")
            if os.path.exists(schema_path):
                with open(schema_path, "r") as f:
                    self.schema_cache = f.read()
            else:
                # Fallback schema (Complete enough for basic queries)
                self.schema_cache = """
                CREATE TABLE properties (
                    property_id TEXT PRIMARY KEY,
                    name TEXT,
                    address TEXT,
                    city TEXT,
                    region TEXT,
                    total_area FLOAT, -- Totalt areal i m2 (direkte felt)
                    land_area FLOAT, -- Tomteareal i m2
                    construction_year INTEGER,
                    external_data JSONB -- Tilleggsdata
                );
                
                CREATE TABLE contracts (
                    contract_id TEXT PRIMARY KEY,
                    unit_id TEXT, -- F.K. to units
                    party_id TEXT, -- F.K. to parties
                    amount NUMERIC,
                    status TEXT, -- 'active', 'terminated'
                    periods JSONB -- [{start: date, end: date, amount: float}]
                );
                
                CREATE TABLE parties (
                    party_id TEXT PRIMARY KEY,
                    name TEXT,
                    orgnr TEXT
                );

                CREATE TABLE gl_transactions (
                    transaction_id UUID PRIMARY KEY,
                    property_id UUID, -- F.K. to properties, can be NULL
                    ar INTEGER, -- Regnskapsår, f.eks. 2025. BRUK `ar`, ikke `year`.
                    maaned INTEGER,
                    belop NUMERIC, -- Beløp i NOK. BRUK `belop`, ikke `amount`.
                    konto_navn TEXT, -- Kontonavn, f.eks. 'Leie lokaler fra Statsbygg'. BRUK `konto_navn`.
                    srs_kategori TEXT, -- 'Husleie', 'Drift', 'Investering', 'Gjennomstrømning'
                    dim1_kode TEXT, -- Koststedskode. BRUK `dim1_kode`, ikke `department_code`.
                    region TEXT, -- Region. BRUK `region`, ikke `region_name`.
                    leverandor_navn TEXT, -- Leverandørnavn. BRUK `leverandor_navn`, ikke `supplier_name`.
                    source_system TEXT
                );
                -- Husleie: srs_kategori = 'Husleie' (eller konto_navn ILIKE '%leie%')
                """
        except Exception:
            self.schema_cache = "Schema loading failed."
            
        return self.schema_cache

    def _detect_complexity(self, question: str) -> bool:
        """
        Detekterer om spørsmålet krever kompleks SQL (JSONB, JOINs, aggregering).
        
        Returns:
            True hvis kompleks (bruk gpt-4o), False hvis enkel (bruk gpt-4o-mini)
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
            # Beregninger/ratio
            "per kvm", "per m2", "per kvadratmeter", "kostnad per", "leie per",
            "kvm", "kvadratmeter", "pris per", "ratio", "forhold",
            # Økonomi og budsjett (ofte JSONB/komplekse aggregeringer/egne tabeller)
            "budsjett", "avvik", "regnskap", "økonomi", "kostnadskategori", "faktiske kostnader",
            "kpi", "kpi-justert", "leie", "vedlikehold", "felleskostnader", "strøm", "oppvarming", 
            "renhold", "parkeringsleie", "vaktmester",
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
    
    def _get_cache_key(self, question: str) -> str:
        """Generer cache key basert på spørsmålet"""
        # Normaliser spørsmålet (lowercase, strip whitespace)
        normalized = question.lower().strip()
        # Hash for konsistent key
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _get_cached_sql(self, cache_key: str) -> Optional[tuple[str, str]]:
        """
        Hent cached SQL hvis tilgjengelig og ikke utløpt.
        
        Returns:
            Tuple of (sql, model_used) eller None
        """
        if not SQL_CACHE_ENABLED:
            return None
        
        if cache_key not in self._sql_cache:
            return None
        
        sql, timestamp, model_used = self._sql_cache[cache_key]
        
        # Sjekk om cache er utløpt
        if datetime.now() - timestamp > timedelta(seconds=SQL_CACHE_TTL_SECONDS):
            del self._sql_cache[cache_key]
            return None
        
        return (sql, model_used)
    
    def _cache_sql(self, cache_key: str, sql: str, model_used: str):
        """Cache SQL med timestamp og modell brukt"""
        if not SQL_CACHE_ENABLED:
            return
        
        # Håndter cache size limit (FIFO eviction)
        if len(self._sql_cache) >= SQL_CACHE_MAX_SIZE:
            # Fjern eldste entry (enkel implementering)
            oldest_key = min(self._sql_cache.keys(), 
                           key=lambda k: self._sql_cache[k][1])
            del self._sql_cache[oldest_key]
        
        self._sql_cache[cache_key] = (sql, datetime.now(), model_used)
    
    def forward(self, question: str, page_context: str = "", use_fallback: bool = False) -> dspy.Prediction:
        """
        Generate SQL with caching and fallback support.
        
        Args:
            question: User's question in Norwegian
            page_context: Information about the current entity being viewed
            use_fallback: Force use of gpt-4o (skip gpt-4o-mini)
        
        Returns:
            dspy.Prediction with sql_query field
        """
        # Cache key inkluderer nå også page_context for å unngå feil treff
        cache_key = self._get_cache_key(f"{question}_{page_context}")
        
        # Sjekk cache først
        cached_result = self._get_cached_sql(cache_key)
        if cached_result:
            cached_sql, model_used = cached_result
            self._cache_hits += 1
            logger.info(f"SQL cache HIT for question: {question[:50]}... (model: {model_used})")
            # Returner cached SQL som Prediction-objekt
            class CachedPrediction:
                def __init__(self, sql):
                    self.sql_query = sql
            return CachedPrediction(cached_sql)
        
        # Cache miss - generer ny SQL
        self._cache_misses += 1
        
        # Detekter kompleksitet eller bruk fallback hvis eksplisitt bedt om
        is_complex = self._detect_complexity(question) or use_fallback
        
        schema = self._get_schema()
        model_used = "gpt-4o-mini"
        
        try:
            if is_complex and self.fallback_lm:
                # Bruk gpt-4o for komplekse spørringer
                logger.info(f"SQL cache MISS - Kompleks spørring detektert, bruker gpt-4o: {question[:50]}...")
                self._fallback_used += 1
                
                # Initialize fallback generator hvis ikke allerede gjort
                if self.generate_fallback is None:
                    # Create a new ChainOfThought - will use configured LM at call time
                    self.generate_fallback = dspy.ChainOfThought(TextToSQL)
                
                # Temporarily configure DSPy with fallback model
                dspy.configure(lm=self.fallback_lm)
                pred = self.generate_fallback(question=question, page_context=page_context, schema_context=schema)
                # Restore original LM
                dspy.configure(lm=self.primary_lm)
                model_used = "gpt-4o"
            else:
                # Bruk gpt-4o-mini for enkle spørringer
                logger.info(f"SQL cache MISS - Enkel spørring, bruker gpt-4o-mini: {question[:50]}...")
                pred = self.generate_mini(question=question, page_context=page_context, schema_context=schema)
            
            # Cache den genererte SQL
            if pred.sql_query:
                clean_sql = SQLValidator.clean(pred.sql_query)
                if SQLValidator.validate(clean_sql):
                    self._cache_sql(cache_key, clean_sql, model_used)
            
            return pred
            
        except Exception as e:
            # Hvis gpt-4o-mini feiler, prøv fallback til gpt-4o
            if not is_complex and self.fallback_lm:
                logger.warning(f"gpt-4o-mini feilet, prøver fallback til gpt-4o: {e}")
                try:
                    if self.generate_fallback is None:
                        self.generate_fallback = dspy.ChainOfThought(TextToSQL)
                    dspy.configure(lm=self.fallback_lm)
                    pred = self.generate_fallback(question=question, schema_context=schema)
                    dspy.configure(lm=self.primary_lm)  # Restore original
                    model_used = "gpt-4o"
                    self._fallback_used += 1
                    
                    # Cache fallback resultat
                    if pred.sql_query:
                        clean_sql = SQLValidator.clean(pred.sql_query)
                        if SQLValidator.validate(clean_sql):
                            self._cache_sql(cache_key, clean_sql, model_used)
                    
                    return pred
                except Exception as fallback_error:
                    logger.error(f"Fallback til gpt-4o feilet også: {fallback_error}")
                    raise e  # Re-raise original error
            else:
                raise  # Re-raise if no fallback available or already using fallback
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Hent cache-statistikk"""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        # Tell hvor mange ganger hver modell ble brukt (fra cache)
        mini_count = sum(1 for _, _, model in self._sql_cache.values() if model == "gpt-4o-mini")
        fallback_count = sum(1 for _, _, model in self._sql_cache.values() if model == "gpt-4o")
        
        return {
            "cache_enabled": SQL_CACHE_ENABLED,
            "cache_size": len(self._sql_cache),
            "cache_max_size": SQL_CACHE_MAX_SIZE,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate_percent": round(hit_rate, 2),
            "fallback_used": self._fallback_used,
            "cached_mini": mini_count,
            "cached_fallback": fallback_count
        }
    
    def clear_cache(self):
        """Tøm cache (nyttig for testing eller ved schema-endringer)"""
        self._sql_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        self._fallback_used = 0
        logger.info("SQL cache cleared")
    
    async def _estimate_query_cost(self, db: AsyncSession, sql: str) -> float:
        """
        Estimate query cost using EXPLAIN without actually executing the query.

        Args:
            db: Database session
            sql: SQL query to analyze

        Returns:
            Estimated cost as float (from PostgreSQL EXPLAIN)

        Raises:
            Exception: If EXPLAIN fails
        """
        try:
            explain_sql = f"EXPLAIN {sql}"
            result = await db.execute(text(explain_sql))
            rows = result.fetchall()

            # Parse first line of EXPLAIN output to get cost estimate
            # Format: "Seq Scan on table  (cost=0.00..X.XX rows=N width=N)"
            if rows:
                first_line = str(rows[0][0])
                if "cost=" in first_line:
                    # Extract the upper cost estimate (the second number)
                    cost_part = first_line.split("cost=")[1].split(")")[0]
                    # Format: "0.00..X.XX"
                    upper_cost = float(cost_part.split("..")[1])
                    return upper_cost

            # Fallback: return 0 if we can't parse (allow query to proceed)
            logger.warning(f"Could not parse EXPLAIN output for cost estimation: {rows}")
            return 0.0

        except Exception as e:
            logger.warning(f"EXPLAIN failed for cost estimation: {e}")
            # Return 0 to allow query (fail open rather than blocking valid queries)
            return 0.0

    async def _execute_with_retry(
        self,
        db: AsyncSession,
        sql: str,
        max_retries: int = 3,
        initial_delay: float = 1.0
    ):
        """
        Execute SQL with exponential backoff retry logic and cost limiting.
        Viktig for serverless database som kan ha cold starts.

        Args:
            db: Database session
            sql: SQL query to execute
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds (doubles each retry)

        Returns:
            SQLAlchemy result object

        Raises:
            ValueError: If query cost exceeds MAX_QUERY_COST
            Exception: If all retries fail
        """
        import asyncio
        from sqlalchemy.exc import OperationalError, DisconnectionError

        # Check query cost before executing (security measure)
        if ENABLE_COST_LIMIT_CHECK:
            estimated_cost = await self._estimate_query_cost(db, sql)
            if estimated_cost > MAX_QUERY_COST:
                logger.error(
                    f"Query blocked: estimated cost {estimated_cost:.2f} exceeds limit {MAX_QUERY_COST}. "
                    f"SQL: {sql[:200]}..."
                )
                raise ValueError(
                    f"Query er for dyr å kjøre (estimert kostnad: {estimated_cost:.0f}, "
                    f"maks: {MAX_QUERY_COST:.0f}). Prøv å begrense søket eller bruk mer spesifikke filtre."
                )
            elif estimated_cost > MAX_QUERY_COST * 0.5:
                # Warn if cost is more than 50% of limit
                logger.warning(
                    f"Query has high estimated cost {estimated_cost:.2f} "
                    f"({estimated_cost/MAX_QUERY_COST*100:.1f}% of limit)"
                )

        last_error = None

        for attempt in range(max_retries):
            try:
                result = await db.execute(text(sql))
                if attempt > 0:
                    logger.info(f"SQL execution succeeded on retry attempt {attempt + 1}")
                return result
                
            except (OperationalError, DisconnectionError) as e:
                last_error = e
                error_msg = str(e).lower()
                
                # Sjekk om dette er en transient error (cold start, connection timeout)
                is_transient = any(keyword in error_msg for keyword in [
                    "connection", "timeout", "server closed", "broken pipe",
                    "could not connect", "network", "temporarily unavailable"
                ])
                
                if not is_transient:
                    # Ikke en transient error, ikke prøv igjen
                    logger.error(f"Non-transient database error: {e}")
                    raise
                
                if attempt < max_retries - 1:
                    delay = initial_delay * (2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(
                        f"Database error (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"SQL execution failed after {max_retries} attempts: {e}")
                    raise
                    
            except Exception as e:
                # Non-retryable error (syntax error, etc.)
                logger.error(f"Non-retryable SQL error: {e}")
                raise
        
        # Should not reach here, but just in case
        if last_error:
            raise last_error
        raise Exception("SQL execution failed for unknown reason")

    async def execute_query(
        self,
        db: AsyncSession,
        question: str,
        page_context: str = "",
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point with comprehensive logging and confidence scoring.

        Query library (100+ mønstre) -> eller generer SQL -> Valider -> Kjør -> Returner -> LOGG ALT

        New in Phase 1 (Self-Learning Loop):
        - Logs ALL query attempts (success and failure) to query_logs table
        - Calculates confidence score (0.0-1.0) for each query
        - Auto-retries low-confidence failures with gpt-4o
        - Returns log_id for feedback integration (Phase 2)
        """
        start_time = time.time()
        confidence = 0.0
        model_used = "gpt-4o-mini"
        cache_hit = False
        clean_sql = None
        lib_match = None
        log_id = None
        is_complex = False

        try:
            # 0. Prøv query_library først (mange lagrede SQL-mønstre fra tidligere kjøringer)
            try:
                from app.services.query_library_service import query_library_service
                lib_match = await query_library_service.find_similar_query(
                    db, question, min_usage_count=2, min_success_rate=0.85
                )
                if lib_match and lib_match.get("sql_template"):
                    clean_sql = SQLValidator.clean(lib_match["sql_template"])
                    cache_hit = True
                    model_used = "query_library"

                    # Calculate confidence for library match
                    confidence = ConfidenceScorer.calculate_confidence(
                        question, clean_sql, lib_match, True, model_used, False
                    )

                    if SQLValidator.validate(clean_sql):
                        result = await self._execute_with_retry(db, clean_sql)
                        rows = result.fetchall()
                        columns = result.keys()
                        formatted_data = [dict(zip(columns, row)) for row in rows]
                        execution_time_ms = int((time.time() - start_time) * 1000)

                        # LOG SUCCESS
                        log_id = await QueryLoggingService.log_query_execution(
                            db=db,
                            user_question=question,
                            generated_sql=clean_sql,
                            execution_success=True,
                            result_count=len(formatted_data),
                            execution_time_ms=execution_time_ms,
                            error_message=None,
                            confidence_score=confidence,
                            model_used=model_used,
                            cache_hit=cache_hit,
                            context_data={
                                "source": "query_library",
                                "query_type": "lookup",
                                "query_name": lib_match.get('query_name', 'unknown')
                            },
                            user_id=user_id,
                            conversation_id=conversation_id
                        )

                        logger.info(f"Query library HIT: {lib_match.get('query_name', '?')} -> {len(formatted_data)} rows (confidence={confidence:.2f})")

                        return {
                            "results": formatted_data,
                            "sql": clean_sql,
                            "count": len(formatted_data),
                            "error": None,
                            "source": "query_library",
                            "confidence": confidence,
                            "model_used": model_used,
                            "log_id": str(log_id) if log_id else None
                        }
            except Exception as lib_err:
                logger.debug(f"Query library lookup skipped: {lib_err}")

            # 1. Generate SQL (with automatic complexity detection and fallback)
            try:
                is_complex = self._detect_complexity(question)
                pred = self.forward(question, page_context=page_context, use_fallback=is_complex)
                raw_sql = pred.sql_query

                if not raw_sql or not raw_sql.strip():
                    execution_time_ms = int((time.time() - start_time) * 1000)

                    # LOG GENERATION FAILURE
                    log_id = await QueryLoggingService.log_query_execution(
                        db=db,
                        user_question=question,
                        generated_sql=None,
                        execution_success=False,
                        result_count=0,
                        execution_time_ms=execution_time_ms,
                        error_message="Empty SQL generated",
                        confidence_score=0.0,
                        model_used=model_used,
                        cache_hit=False,
                        context_data={"error_type": "empty_sql"},
                        user_id=user_id,
                        conversation_id=conversation_id
                    )

                    return {
                        "error": "SQL-generering returnerte tom streng. Prøv å omformulere spørsmålet.",
                        "sql": None,
                        "results": [],
                        "confidence": 0.0,
                        "log_id": str(log_id) if log_id else None
                    }

                clean_sql = SQLValidator.clean(raw_sql)
                model_used = "gpt-4o" if is_complex else "gpt-4o-mini"

                # Calculate confidence for generated SQL
                confidence = ConfidenceScorer.calculate_confidence(
                    question, clean_sql, None, False, model_used, is_complex
                )

                logger.info(f"DSPy generated SQL (confidence={confidence:.2f}, model={model_used}): {clean_sql[:200]}...")

            except Exception as gen_error:
                logger.error(f"DSPy SQL generation failed: {gen_error}", exc_info=True)
                execution_time_ms = int((time.time() - start_time) * 1000)

                # LOG GENERATION ERROR
                log_id = await QueryLoggingService.log_query_execution(
                    db=db,
                    user_question=question,
                    generated_sql=None,
                    execution_success=False,
                    result_count=0,
                    execution_time_ms=execution_time_ms,
                    error_message=str(gen_error),
                    confidence_score=0.0,
                    model_used=model_used,
                    cache_hit=False,
                    context_data={"error_type": type(gen_error).__name__},
                    user_id=user_id,
                    conversation_id=conversation_id
                )

                return {
                    "error": f"Kunne ikke generere SQL fra spørsmålet. Feil: {str(gen_error)}",
                    "sql": None,
                    "results": [],
                    "confidence": 0.0,
                    "log_id": str(log_id) if log_id else None
                }

            # 2. Validate SQL safety
            if not SQLValidator.validate(clean_sql):
                logger.warning(f"SQL validation failed for: {clean_sql[:100]}...")
                execution_time_ms = int((time.time() - start_time) * 1000)

                # LOG VALIDATION FAILURE
                log_id = await QueryLoggingService.log_query_execution(
                    db=db,
                    user_question=question,
                    generated_sql=clean_sql,
                    execution_success=False,
                    result_count=0,
                    execution_time_ms=execution_time_ms,
                    error_message="SQL validation failed - not READ-ONLY or contains forbidden operations",
                    confidence_score=confidence,
                    model_used=model_used,
                    cache_hit=False,
                    context_data={"error_type": "validation_error"},
                    user_id=user_id,
                    conversation_id=conversation_id
                )

                return {
                    "error": "SQL validering feilet - spørringen er ikke READ-ONLY eller inneholder ugyldige operasjoner.",
                    "sql": clean_sql,
                    "results": [],
                    "confidence": confidence,
                    "log_id": str(log_id) if log_id else None
                }

            # 3. Execute SQL with retry logic (for serverless cold starts)
            try:
                logger.info(f"DSPy executing SQL: {clean_sql}")
                result = await self._execute_with_retry(db, clean_sql)
                rows = result.fetchall()

                # 4. Format Results
                columns = result.keys()
                formatted_data = [dict(zip(columns, row)) for row in rows]
                execution_time_ms = int((time.time() - start_time) * 1000)

                # LOG SUCCESS
                log_id = await QueryLoggingService.log_query_execution(
                    db=db,
                    user_question=question,
                    generated_sql=clean_sql,
                    execution_success=True,
                    result_count=len(formatted_data),
                    execution_time_ms=execution_time_ms,
                    error_message=None,
                    confidence_score=confidence,
                    model_used=model_used,
                    cache_hit=cache_hit,
                    context_data={
                        "source": "dspy",
                        "query_type": "lookup",
                        "is_complex": is_complex
                    },
                    user_id=user_id,
                    conversation_id=conversation_id
                )

                logger.info(f"DSPy query returned {len(formatted_data)} rows (confidence={confidence:.2f})")

                return {
                    "results": formatted_data,
                    "sql": clean_sql,
                    "count": len(formatted_data),
                    "error": None,
                    "confidence": confidence,
                    "model_used": model_used,
                    "log_id": str(log_id) if log_id else None
                }

            except Exception as db_error:
                # Database execution error - provide helpful error message
                error_msg = str(db_error)
                logger.error(f"SQL execution failed: {error_msg}\nSQL: {clean_sql}", exc_info=True)
                execution_time_ms = int((time.time() - start_time) * 1000)

                # LOG EXECUTION FAILURE
                log_id = await QueryLoggingService.log_query_execution(
                    db=db,
                    user_question=question,
                    generated_sql=clean_sql,
                    execution_success=False,
                    result_count=0,
                    execution_time_ms=execution_time_ms,
                    error_message=error_msg,
                    confidence_score=confidence,
                    model_used=model_used,
                    cache_hit=cache_hit,
                    context_data={"error_type": type(db_error).__name__},
                    user_id=user_id,
                    conversation_id=conversation_id
                )

                # PHASE 1: Auto-retry for low confidence failures
                if confidence < 0.70 and model_used != "gpt-4o":
                    logger.info(f"Low confidence failure ({confidence:.2f}), triggering auto-retry with gpt-4o")
                    return await self._retry_with_fallback(
                        db, question, page_context, log_id, start_time, user_id, conversation_id
                    )

                # Check for common errors and provide helpful hints
                if "syntax error" in error_msg.lower() or "invalid" in error_msg.lower():
                    hint = "SQL-syntaksfeil. Sjekk JSONB-syntaks (->> for tekst, -> for objekt) og type-casting (::numeric, ::date)."
                elif "does not exist" in error_msg.lower():
                    hint = "Kolonne eller tabell finnes ikke. Sjekk at du bruker riktige tabellnavn og kolonnenavn fra schema."
                elif "operator does not exist" in error_msg.lower():
                    hint = "Operatør-feil. Husk å caste JSONB-verdier (f.eks. ::numeric eller ::date) før sammenligning."
                else:
                    hint = "Database-feil. Sjekk SQL-syntaks og at alle JSONB-felt er riktig formatert."

                return {
                    "error": f"{hint} Detaljer: {error_msg}",
                    "sql": clean_sql,
                    "results": [],
                    "confidence": confidence,
                    "log_id": str(log_id) if log_id else None
                }

        except Exception as e:
            # Unexpected error
            logger.error(f"DSPy execution failed with unexpected error: {e}", exc_info=True)
            execution_time_ms = int((time.time() - start_time) * 1000)

            # LOG UNEXPECTED ERROR
            try:
                log_id = await QueryLoggingService.log_query_execution(
                    db=db,
                    user_question=question,
                    generated_sql=clean_sql,
                    execution_success=False,
                    result_count=0,
                    execution_time_ms=execution_time_ms,
                    error_message=str(e),
                    confidence_score=confidence,
                    model_used=model_used,
                    cache_hit=cache_hit,
                    context_data={"error_type": type(e).__name__},
                    user_id=user_id,
                    conversation_id=conversation_id
                )
            except:
                pass  # Don't fail if logging fails

            return {
                "error": f"Uventet feil under SQL-generering/kjøring: {str(e)}",
                "sql": clean_sql if clean_sql else "N/A",
                "results": [],
                "confidence": confidence,
                "log_id": str(log_id) if log_id else None
            }

    async def _retry_with_fallback(
        self,
        db: AsyncSession,
        question: str,
        page_context: str,
        parent_log_id: UUID,
        original_start_time: float,
        user_id: Optional[str],
        conversation_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Retry failed query with gpt-4o and enhanced prompt.

        This is the core of the self-learning loop's auto-improvement feature.
        When a low-confidence query fails, we automatically retry with:
        - More powerful model (gpt-4o instead of gpt-4o-mini)
        - Enhanced prompt with JSONB guidance
        - Linked to parent attempt via parent_log_id for tracking
        """
        logger.info(f"🔁 Auto-retry with gpt-4o for question: {question[:50]}...")

        # Enhanced prompt with specific JSONB guidance
        enhanced_question = f"""{question}

[System: Previous attempt failed. Extra guidance:
- Use NULLIF(column, 0) to prevent division by zero
- Cast JSONB fields correctly: (field->>'key')::numeric for numbers
- Double-check column names match SCHEMA.md exactly
- Use COALESCE for NULL safety in calculations]"""

        try:
            # Force gpt-4o for retry
            pred = self.forward(enhanced_question, page_context=page_context, use_fallback=True)
            clean_sql = SQLValidator.clean(pred.sql_query)

            # Validate
            if not SQLValidator.validate(clean_sql):
                raise ValueError("SQL validation failed on retry")

            # Execute
            result = await self._execute_with_retry(db, clean_sql)
            rows = result.fetchall()
            columns = result.keys()
            formatted_data = [dict(zip(columns, row)) for row in rows]
            execution_time_ms = int((time.time() - original_start_time) * 1000)

            # LOG RETRY SUCCESS
            retry_log_id = await QueryLoggingService.log_query_execution(
                db=db,
                user_question=question,
                generated_sql=clean_sql,
                execution_success=True,
                result_count=len(formatted_data),
                execution_time_ms=execution_time_ms,
                error_message=None,
                confidence_score=0.85,  # gpt-4o retry has good confidence
                model_used="gpt-4o",
                cache_hit=False,
                context_data={"retry_reason": "low_confidence_failure", "source": "dspy"},
                user_id=user_id,
                conversation_id=conversation_id,
                retry_count=1,
                parent_log_id=parent_log_id
            )

            # Cache the successful retry for future use
            cache_key = self._generate_cache_key(question)
            self._cache_sql(cache_key, clean_sql, "gpt-4o")

            logger.info(f"✅ Auto-retry SUCCESS! Generated working SQL with gpt-4o")

            return {
                "results": formatted_data,
                "sql": clean_sql,
                "count": len(formatted_data),
                "error": None,
                "confidence": 0.85,
                "model_used": "gpt-4o",
                "retried": True,
                "log_id": str(retry_log_id) if retry_log_id else None
            }

        except Exception as retry_error:
            execution_time_ms = int((time.time() - original_start_time) * 1000)
            error_msg = str(retry_error)

            # LOG RETRY FAILURE
            await QueryLoggingService.log_query_execution(
                db=db,
                user_question=question,
                generated_sql=clean_sql if 'clean_sql' in locals() else None,
                execution_success=False,
                result_count=0,
                execution_time_ms=execution_time_ms,
                error_message=error_msg,
                confidence_score=0.0,
                model_used="gpt-4o",
                cache_hit=False,
                context_data={"retry_reason": "low_confidence_failure", "error_type": type(retry_error).__name__},
                user_id=user_id,
                conversation_id=conversation_id,
                retry_count=1,
                parent_log_id=parent_log_id
            )

            logger.error(f"❌ Auto-retry also FAILED with gpt-4o: {error_msg}")

            # Return error from retry
            return {
                "error": f"Auto-retry med gpt-4o feilet også. Feil: {error_msg}",
                "sql": clean_sql if 'clean_sql' in locals() else None,
                "results": [],
                "confidence": 0.0,
                "retried": True,
                "log_id": str(parent_log_id) if parent_log_id else None
            }

# Singleton
dspy_generator = SQLGenerator()
