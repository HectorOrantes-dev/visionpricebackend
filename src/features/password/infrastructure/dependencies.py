"""Composición de dependencias del restablecimiento de contraseña."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.features.password.application.restablecer import Restablecer
from src.features.password.application.solicitar_reset import SolicitarReset
from src.features.password.infrastructure.repository import (
    SqlAlchemyPasswordRepository,
)
from src.features.two_factor.infrastructure.client import HttpTwoFactorClient


def get_solicitar_reset(
    session: AsyncSession = Depends(get_session),
) -> SolicitarReset:
    return SolicitarReset(
        repo=SqlAlchemyPasswordRepository(session),
        two_factor=HttpTwoFactorClient(),
    )


def get_restablecer(
    session: AsyncSession = Depends(get_session),
) -> Restablecer:
    return Restablecer(
        repo=SqlAlchemyPasswordRepository(session),
        two_factor=HttpTwoFactorClient(),
    )
