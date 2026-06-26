"""VisionPrice — API principal (Módulo de Usuarios).

App factory: monta routers, CORS, manejadores de error y /health.
Arquitectura hexagonal: cada feature vive en src/features/<feature>/
con capas domain / application / infrastructure.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.features.account.infrastructure.router import router as account_router
from src.features.google_auth.infrastructure.router import router as google_router
from src.features.grabaciones.infrastructure.router import router as grabaciones_router
from src.features.login.infrastructure.router import router as login_router
from src.features.pagos.infrastructure.router import router as pagos_router
from src.features.register.infrastructure.router import router as register_router
from src.features.roles.infrastructure.router import router as roles_router
from src.shared.errors import register_error_handlers
from src.shared.schemas import HealthOut


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="API principal de VisionPrice (usuarios, auth 2FA, proyectos).",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)

    @app.get("/health", tags=["health"], response_model=HealthOut)
    async def health() -> HealthOut:
        return HealthOut(status="ok", environment=settings.environment)

    # Routers de features, todos bajo el prefijo /api/v1.
    app.include_router(register_router, prefix=settings.api_prefix)
    app.include_router(login_router, prefix=settings.api_prefix)
    app.include_router(google_router, prefix=settings.api_prefix)
    app.include_router(roles_router, prefix=settings.api_prefix)
    app.include_router(account_router, prefix=settings.api_prefix)
    app.include_router(grabaciones_router, prefix=settings.api_prefix)
    app.include_router(pagos_router, prefix=settings.api_prefix)

    return app


app = create_app()
