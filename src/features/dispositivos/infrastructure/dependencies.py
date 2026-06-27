"""Composición de dependencias de la feature dispositivos."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.features.dispositivos.application.gestionar_dispositivo import (
    EliminarDispositivo,
    RegistrarDispositivo,
)
from src.features.dispositivos.infrastructure.repository import (
    SqlAlchemyDispositivoRepository,
)


def get_registrar_dispositivo(
    session: AsyncSession = Depends(get_session),
) -> RegistrarDispositivo:
    return RegistrarDispositivo(repo=SqlAlchemyDispositivoRepository(session))


def get_eliminar_dispositivo(
    session: AsyncSession = Depends(get_session),
) -> EliminarDispositivo:
    return EliminarDispositivo(repo=SqlAlchemyDispositivoRepository(session))
