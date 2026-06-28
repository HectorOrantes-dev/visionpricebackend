"""Composición de dependencias de auditoría de precios."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_session
from src.features.auditoria_precios.application.auditar import (
    AuditarPresupuesto,
    AuditarZona,
)
from src.features.auditoria_precios.infrastructure.repository import (
    SqlAlchemyAuditoriaRepository,
)


def _params() -> dict:
    return {
        "precision": settings.auditoria_zona_precision,
        "margen": settings.auditoria_margen,
        "min_muestras": settings.auditoria_min_muestras,
    }


def get_auditar_presupuesto(
    session: AsyncSession = Depends(get_session),
) -> AuditarPresupuesto:
    return AuditarPresupuesto(
        SqlAlchemyAuditoriaRepository(session), **_params()
    )


def get_auditar_zona(
    session: AsyncSession = Depends(get_session),
) -> AuditarZona:
    return AuditarZona(SqlAlchemyAuditoriaRepository(session), **_params())
