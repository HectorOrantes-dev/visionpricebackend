"""Composición de dependencias de la feature login."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_session
from src.features.login.application.authenticate_user import AuthenticateUser
from src.features.login.application.verify_two_factor import VerifyTwoFactor
from src.features.login.infrastructure.challenge_repository import (
    SqlAlchemyChallengeRepository,
)
from src.features.login.infrastructure.repository import SqlAlchemyLoginRepository
from src.features.two_factor.infrastructure.client import HttpTwoFactorClient


def get_authenticate_user(
    session: AsyncSession = Depends(get_session),
) -> AuthenticateUser:
    return AuthenticateUser(
        repo=SqlAlchemyLoginRepository(session),
        two_factor=HttpTwoFactorClient(),
        challenges=SqlAlchemyChallengeRepository(session),
    )


def get_verify_two_factor(
    session: AsyncSession = Depends(get_session),
) -> VerifyTwoFactor:
    return VerifyTwoFactor(
        repo=SqlAlchemyLoginRepository(session),
        two_factor=HttpTwoFactorClient(),
        challenges=SqlAlchemyChallengeRepository(session),
        max_intentos=settings.two_factor_max_intentos,
    )
