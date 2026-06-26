"""Composición de dependencias de la feature roles."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.features.roles.application.listar_roles import ListarRoles
from src.features.roles.infrastructure.repository import SqlAlchemyRoleRepository


def get_listar_roles(
    session: AsyncSession = Depends(get_session),
) -> ListarRoles:
    return ListarRoles(repo=SqlAlchemyRoleRepository(session))
