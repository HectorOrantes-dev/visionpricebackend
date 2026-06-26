"""Configuración central de la aplicación.

Lee variables de entorno (.env) con pydantic-settings. Se expone una única
instancia `settings` que el resto de la app importa.
"""
from functools import lru_cache
from urllib.parse import urlencode, urlsplit, urlunsplit

from pydantic_settings import BaseSettings, SettingsConfigDict

# Parámetros de query que pone Neon/Postgres pero que asyncpg NO entiende en la
# URL (los maneja por connect_args). Se quitan al normalizar.
_DROP_QUERY_KEYS = {"sslmode", "channel_binding"}


def _normalize_db_url(url: str) -> tuple[str, bool]:
    """Devuelve (url_para_sqlalchemy, requiere_ssl).

    - postgres:// y postgresql://  ->  postgresql+asyncpg://
    - quita sslmode/channel_binding de la query (asyncpg los rechaza)
    - detecta si hay que forzar SSL (Neon o sslmode=require)
    """
    if url.startswith("sqlite"):
        return url, False

    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://") :]

    parts = urlsplit(url)
    require_ssl = "neon.tech" in parts.hostname if parts.hostname else False

    kept: list[tuple[str, str]] = []
    for key, value in (
        kv.split("=", 1) if "=" in kv else (kv, "")
        for kv in parts.query.split("&")
        if kv
    ):
        if key in _DROP_QUERY_KEYS:
            if key == "sslmode" and value in ("require", "verify-full", "verify-ca"):
                require_ssl = True
            continue
        kept.append((key, value))

    normalized = urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(kept), parts.fragment)
    )
    return normalized, require_ssl


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- App ---
    app_name: str = "VisionPrice API"
    api_prefix: str = "/api/v1"
    environment: str = "local"
    allowed_origins: str = "*"

    # --- Base de datos ---
    database_url: str = "sqlite+aiosqlite:///./visionprice.db"

    # --- JWT (mismo secreto que el microservicio de Pagos) ---
    jwt_secret: str = "cambia-esto-por-un-secreto-largo-y-aleatorio"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 1440

    # --- Google OAuth (Sign-In) ---
    # Uno o varios client IDs (web, android, ios) separados por coma. El id_token
    # de Google debe tener alguno de estos en su claim `aud`.
    google_client_ids: str = ""

    # --- Microservicio 2FA ---
    two_factor_base_url: str = "https://visionprice-2fa-production.up.railway.app"
    two_factor_timeout: int = 20
    # Máximo de intentos de código por desafío (anti fuerza bruta).
    two_factor_max_intentos: int = 5

    # --- Microservicio de Extracciones ---
    extractions_base_url: str = ""
    extractions_api_key: str = ""

    # --- Microservicio de Pagos ---
    payments_base_url: str = ""

    # --- Webhooks/callbacks ENTRANTES (servicio -> esta API) ---
    # Los microservicios de ML y Pagos llaman de vuelta con este X-Api-Key.
    webhook_api_key: str = "cambia-esto-por-una-api-key-interna"

    @property
    def cors_origins(self) -> list[str]:
        if self.allowed_origins.strip() in ("", "*"):
            return ["*"]
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def google_audiences(self) -> list[str]:
        return [c.strip() for c in self.google_client_ids.split(",") if c.strip()]

    @property
    def sqlalchemy_url(self) -> str:
        """URL lista para SQLAlchemy async (driver y query normalizados)."""
        return _normalize_db_url(self.database_url)[0]

    @property
    def db_connect_args(self) -> dict:
        """connect_args para el engine (SSL para Neon/Postgres remoto)."""
        if _normalize_db_url(self.database_url)[1]:
            return {"ssl": True}
        return {}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
