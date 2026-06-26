"""Inyección de dependencias (composición) de la feature register."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.features.register.application.register_user import RegisterUser
from src.features.register.infrastructure.repository import (
    SqlAlchemyRegisterRepository,
)
from src.features.two_factor.infrastructure.client import HttpTwoFactorClient


def get_register_user(
    session: AsyncSession = Depends(get_session),
) -> RegisterUser:
    return RegisterUser(
        repo=SqlAlchemyRegisterRepository(session),
        two_factor=HttpTwoFactorClient(),
    )
