"""Composición de dependencias del webhook de pagos."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.features.pagos.application.actualizar_entitlement import (
    ActualizarEntitlement,
)
from src.features.pagos.infrastructure.repository import (
    SqlAlchemyEntitlementRepository,
)


def get_actualizar_entitlement(
    session: AsyncSession = Depends(get_session),
) -> ActualizarEntitlement:
    return ActualizarEntitlement(repo=SqlAlchemyEntitlementRepository(session))
