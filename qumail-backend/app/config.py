from functools import lru_cache
from typing import Optional

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = ConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Allow extra fields to be ignored
    )
    
    app_name: str = Field(default="QuMail Backend", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    debug: bool = Field(default=False, alias="DEBUG")

    database_url: str = Field(
        default="mongodb+srv://user:password@cluster.mongodb.net/qumail?retryWrites=true&w=majority",
        alias="DATABASE_URL",
    )
    fallback_database_url: str = Field(
        default="mongodb://127.0.0.1:27017/qumail?directConnection=true",
        alias="FALLBACK_DATABASE_URL",
        description="Optional local MongoDB connection string used when the primary URL is unreachable",
    )
    mongo_tls_allow_invalid_certs: bool = Field(
        default=False,
        alias="MONGO_TLS_ALLOW_INVALID_CERTS",
        description="Allow invalid TLS certificates when connecting to MongoDB (development only)",
    )
    mongo_tls_ca_file: Optional[str] = Field(
        default=None,
        alias="MONGO_TLS_CA_FILE",
        description="Optional CA bundle for MongoDB TLS connections",
    )
    mongo_force_local: bool = Field(
        default=False,
        alias="MONGO_FORCE_LOCAL",
        description="Skip cloud MongoDB attempts and use fallback/local connection immediately",
    )
    mongo_embedded_enabled: bool = Field(
        default=True,
        alias="MONGO_EMBEDDED_ENABLED",
        description="Enable lightweight embedded MongoDB fallback when all connections fail",
    )
    mongo_embedded_db_name: str = Field(
        default="qumail_dev",
        alias="MONGO_EMBEDDED_DB_NAME",
        description="Database name to use for embedded MongoDB fallback",
    )
    mongo_min_pool_size: int = Field(default=1, alias="MONGO_MIN_POOL_SIZE")
    mongo_max_pool_size: int = Field(default=50, alias="MONGO_MAX_POOL_SIZE")
    mongo_connection_timeout_ms: int = Field(
        default=5000,
        alias="MONGO_CONNECTION_TIMEOUT_MS",
        description="Server selection timeout for MongoDB clients (milliseconds)",
    )

    secret_key: str = Field(alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    encryption_master_key: str = Field(alias="ENCRYPTION_MASTER_KEY", description="Base64 fernet key")

    google_client_id: str = Field(alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(alias="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(alias="GOOGLE_REDIRECT_URI")

    km1_base_url: str = Field(alias="KM1_BASE_URL")
    km2_base_url: str = Field(alias="KM2_BASE_URL")
    km1_client_cert_pfx: str = Field(alias="KM1_CLIENT_CERT_PFX")
    km2_client_cert_pfx: str = Field(alias="KM2_CLIENT_CERT_PFX")
    km1_client_key: str = Field(default="", alias="KM1_CLIENT_KEY")
    km2_client_key: str = Field(default="", alias="KM2_CLIENT_KEY")
    km_client_cert_password: str = Field(default="", alias="KM_CLIENT_CERT_PASSWORD")
    km1_ca_cert: str = Field(alias="KM1_CA_CERT")
    km2_ca_cert: str = Field(alias="KM2_CA_CERT")
    sender_sae_id: int = Field(alias="SENDER_SAE_ID")
    receiver_sae_id: int = Field(alias="RECEIVER_SAE_ID")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: str = Field(default="qumail-backend.log", alias="LOG_FILE")
    
    # CORS and security - include all deployment origins
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173,https://temp2mgm.netlify.app,https://qumail-nine.vercel.app,https://qumail-frontend.vercel.app,https://qumail-frontend.netlify.app", 
        alias="ALLOWED_ORIGINS"
    )
    cors_enabled: bool = Field(default=True, alias="CORS_ENABLED")
    
    # Rate limiting
    rate_limit_requests_per_minute: int = Field(default=60, alias="RATE_LIMIT_REQUESTS_PER_MINUTE")
    
    # Development settings
    reload_on_change: bool = Field(default=False, alias="RELOAD_ON_CHANGE")
    show_docs: bool = Field(default=True, alias="SHOW_DOCS")
    
    # Health and monitoring
    health_check_timeout: int = Field(default=10, alias="HEALTH_CHECK_TIMEOUT")
    km_connection_timeout: int = Field(default=5, alias="KM_CONNECTION_TIMEOUT")
    
    # Performance
    workers: int = Field(default=1, alias="WORKERS")
    max_connections: int = Field(default=100, alias="MAX_CONNECTIONS")
    keepalive_timeout: int = Field(default=5, alias="KEEPALIVE_TIMEOUT")

def get_settings() -> Settings:
    return Settings()  # type: ignore
