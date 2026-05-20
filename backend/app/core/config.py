import os
from typing import List, Union, Optional, Any
from pydantic import AnyHttpUrl, field_validator, ValidationInfo, Field, AliasChoices, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "BEFS Backend"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    
    # CORS
    BACKEND_CORS_ORIGINS: Union[List[str], str] = []

    # JWT Auth (Shared Secret / Supabase)
    # Default to the same fallback as frontend client.ts for easy setup
    SECRET_KEY: Optional[str] = "befs-super-secret-key-12345"
    SUPABASE_JWT_SECRET: Optional[str] = None  # Set to Supabase JWT secret for token verification
    ADMIN_EMAILS: Union[List[str], str] = []
    # Delt hemmelighet i Authorization: Bearer … (kun for eldre/dev). None = auto: av når SUPABASE_JWT_SECRET er satt.
    ALLOW_SHARED_SECRET_BYPASS: Optional[bool] = None

    @model_validator(mode="after")
    def _default_shared_secret_bypass(self) -> "Settings":
        if self.ALLOW_SHARED_SECRET_BYPASS is None:
            # Med Supabase JWT skal ikke nettleseren kunne bruke statisk hemmelighet som styringsnøkkel
            object.__setattr__(
                self,
                "ALLOW_SHARED_SECRET_BYPASS",
                False if self.SUPABASE_JWT_SECRET else True,
            )
        return self

    @field_validator("ADMIN_EMAILS", mode="before")
    @classmethod
    def parse_admin_emails(cls, v: Any) -> List[str]:
        """Parse comma-separated admin emails from env var."""
        if isinstance(v, list):
            return v
        if not v or not isinstance(v, str):
            return []
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                v = v[1:-1]
        return [email.strip().strip('"').strip("'") for email in v.split(",") if email.strip()]

    # Database
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    DATABASE_URL: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """
        Normaliserer DATABASE_URL for asyncpg:
        - Fjerner psql '...' wrapper hvis limt inn fra utklippstavle
        - Fjerner sslmode/ssl query-parametere (asyncpg håndterer SSL via connect_args i session.py)
        - Konverterer postgres:// og postgresql:// til postgresql+asyncpg://
        - Advarer hvis URL peker til localhost (ikke produksjon).
        """
        if isinstance(v, str):
            v = v.strip()
            # Fjern omsluttende anførselstegn (f.eks. satt feil i Railway/Railway env vars)
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1].strip()
            # Fjern psql-kommando wrapper (psql '...' eller psql "...")
            if v.startswith("psql '") and v.endswith("'"):
                v = v[6:-1]
            elif v.startswith("psql \"") and v.endswith("\""):
                v = v[6:-1]

            # Fjern query-parametere (asyncpg støtter ikke sslmode/ssl i URL)
            # SSL konfigureres i stedet via connect_args={"ssl": True} i session.py
            if "?" in v:
                base_url = v.split("?")[0]
            else:
                base_url = v

            # Advarsel hvis localhost (produksjon bør bruke Cloud DB)
            if "localhost" in base_url or "127.0.0.1" in base_url:
                import warnings
                warnings.warn(
                    "DATABASE_URL peker til localhost. Sjekk at du bruker produksjons-URL i produksjon.",
                    UserWarning,
                )

            if base_url.startswith("postgresql://"):
                return base_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif base_url.startswith("postgres://"):
                return base_url.replace("postgres://", "postgresql+asyncpg://", 1)
            return base_url

        # Fallback: bygg URL fra individuelle POSTGRES_* variabler
        if info.data.get("POSTGRES_USER") and info.data.get("POSTGRES_PASSWORD") and info.data.get("POSTGRES_SERVER") and info.data.get("POSTGRES_DB"):
            return f"postgresql+asyncpg://{info.data['POSTGRES_USER']}:{info.data['POSTGRES_PASSWORD']}@{info.data['POSTGRES_SERVER']}/{info.data['POSTGRES_DB']}"

        return v

    # AI & Search

    # OpenAI Direct
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"  # 94% cheaper than gpt-4o ($0.15/$0.60 vs $2.50/$10.00 per 1M tokens)
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # AI Timeouts (in seconds)
    CHAT_TIMEOUT_SECONDS: float = 90.0
    SQL_GEN_TIMEOUT_SECONDS: float = 20.0
    
    # Vector Search (Postgres pgvector)
    ENABLE_VECTOR_SEARCH: bool = True

    # PDF Processing with Docling
    USE_DOCLING: bool = True  # Enable Docling for advanced PDF parsing
    DOCLING_FALLBACK_TO_PYPDF: bool = True  # Fallback to PyPDF if Docling fails
    DOCLING_EXTRACT_TABLES: bool = True  # Extract tables as structured data
    DOCLING_EXTRACT_IMAGES: bool = False  # Extract images (resource-intensive)
    DOCLING_OCR_ENABLED: bool = True  # OCR for scanned documents

    # External APIs
    BRONNOYSUND_API_KEY: Optional[str] = None

    # Mapbox (kart, geocoding, POI-søk)
    MAPBOX_ACCESS_TOKEN: Optional[str] = None

    # Kartverket / Geonorge (Open Data)
    NVE_API_KEY: Optional[str] = None
    FROST_CLIENT_ID: Optional[str] = None
    FROST_CLIENT_SECRET: Optional[str] = None
    KARTVERKET_API_KEY: Optional[str] = None # Optional for higher rates
    VARSOM_API_KEY: Optional[str] = None
    NGU_API_KEY: Optional[str] = None
    SSB_API_KEY: Optional[str] = None
    MILJODIR_API_KEY: Optional[str] = None
    LOVDATA_API_KEY: Optional[str] = None
    PLANSLURPEN_API_KEY: Optional[str] = None

    # BRREG Regnskapsregisteret Credentials
    BRREG_KR_USERNAME: str = os.getenv("BRREG_KR_USERNAME", "bufdir")
    BRREG_KR_PASSWORD: str = os.getenv("BRREG_KR_PASSWORD", "3vtDgDK7Ys")

    # Jira Integration
    JIRA_URL: Optional[str] = None  # e.g., "https://yourcompany.atlassian.net"
    JIRA_EMAIL: Optional[str] = None
    JIRA_API_TOKEN: Optional[str] = None
    JIRA_DEFAULT_PROJECT: Optional[str] = None  # e.g., "BEFS"

    @field_validator("JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_DEFAULT_PROJECT", mode="before")
    @classmethod
    def validate_jira_config(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Strip whitespace from Jira configuration values to prevent 401 errors."""
        if v and isinstance(v, str):
            return v.strip()
        return v

    # Email Service Configuration
    # Option 1: Resend (Recommended for production)
    RESEND_API_KEY: Optional[str] = None
    EMAIL_FROM: str = "noreply@befs.no"
    
    # Option 2: SMTP (Alternative)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    
    # Frontend URLs (for CORS)
    FRONTEND_URLS: Union[List[str], str] = ["http://localhost:3000", "https://knowme-frontend-amber.vercel.app"]

    @field_validator("FRONTEND_URLS", mode="before")
    @classmethod
    def parse_frontend_urls(cls, v: Any) -> List[str]:
        """Parse comma-separated frontend URLs from env var."""
        if isinstance(v, list):
            return v
        if not v or not isinstance(v, str):
            # Default fallbacks
            return ["http://localhost:3000", "https://knowme-frontend-amber.vercel.app"]
        return [url.strip() for url in v.split(",") if url.strip()]
    
    # Maskinporten (RRH)
    RRH_MASKINPORTEN_CLIENT_ID: Optional[str] = None
    RRH_MASKINPORTEN_KEY_PATH: Optional[str] = None # Path to private key file or raw key
    RRH_MASKINPORTEN_SCOPES: str = "brreg:reelle/offentlig"
    LOCAL_AI_STATION_URL: str = "http://localhost:8080" # Default for Docker Model Runner
    USE_LOCAL_AI: bool = False
    LOCAL_MODEL_NAME: str = "gemma2"
    
    DOCKER_MCP_GATEWAY_URL: str = "http://localhost:8080" # Default for local MCP hub
    # Remote MCP Servers (JSON string or Dict)
    # Example: '{"stripe": "https://mcp-stripe.example.com", "brave": "https://mcp-brave.example.com"}'
    MCP_SERVERS_CONFIG: str = "{}"

    @field_validator("POSTGRES_SERVER", "POSTGRES_USER", "POSTGRES_DB", mode="after")
    @classmethod
    def validate_database_config(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        # Relaxed validation: Allow None/Empty if configured via DATABASE_URL
        # The provided code snippet seems to be intended for Alembic's env.py,
        # where 'config' and 'settings' would be available in the global scope.
        # As this is config.py, we'll keep the original validation logic.
        return v
    
    @field_validator("OPENAI_API_KEY", mode="after")
    @classmethod
    def validate_openai_key(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        if v and len(v) < 10:
             raise ValueError("OPENAI_API_KEY seems too short to be valid.")
        return v

    @model_validator(mode="after")
    def validate_openai_or_local_ai(self) -> "Settings":
        if self.USE_LOCAL_AI:
            return self
        if self.OPENAI_API_KEY and len(self.OPENAI_API_KEY) < 10:
            raise ValueError("OPENAI_API_KEY seems too short to be valid.")
        return self

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> Union[List[str], str]:
        if isinstance(v, list):
            return v
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(f"Invalid CORS origins format: {v}")

    def get_cors_origins_list(self) -> List[str]:
        """Single source for CORS allowed origins (Fix 5 - CODE_REVIEW_30-01)."""
        origins: List[str] = []
        if self.BACKEND_CORS_ORIGINS:
            if isinstance(self.BACKEND_CORS_ORIGINS, list):
                origins.extend(self.BACKEND_CORS_ORIGINS)
            else:
                origins.extend([o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",")])
        if self.FRONTEND_URLS:
            origins.extend(self.FRONTEND_URLS)
        if not origins:
            origins = ["http://localhost:3000", "https://knowme-frontend-amber.vercel.app"]
        return list(dict.fromkeys(origins))

    model_config = SettingsConfigDict(
        case_sensitive=True,
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
    )

settings = Settings()
