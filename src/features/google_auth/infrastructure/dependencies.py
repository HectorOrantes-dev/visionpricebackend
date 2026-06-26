"""Composición de dependencias de la feature google_auth."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_session
from src.features.google_auth.application.google_login import GoogleLogin
from src.features.google_auth.application.google_register import GoogleRegister
from src.features.google_auth.infrastructure.repository import (
    SqlAlchemyGoogleRepository,
)
from src.features.google_auth.infrastructure.verifier import PyJwtGoogleVerifier


def get_google_login(
    session: AsyncSession = Depends(get_session),
) -> GoogleLogin:
    return GoogleLogin(
        verifier=PyJwtGoogleVerifier(settings.google_audiences),
        repo=SqlAlchemyGoogleRepository(session),
    )


def get_google_register(
    session: AsyncSession = Depends(get_session),
) -> GoogleRegister:
    return GoogleRegister(
        verifier=PyJwtGoogleVerifier(settings.google_audiences),
        repo=SqlAlchemyGoogleRepository(session),
    )
