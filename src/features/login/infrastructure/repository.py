"""Adaptador SQLAlchemy del repositorio de login."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.features.login.domain.entities import AuthUser
from src.features.login.domain.ports import LoginUserRepository
from src.shared.models import Usuario


class SqlAlchemyLoginRepository(LoginUserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, correo: str) -> AuthUser | None:
        result = await self._session.execute(
            select(Usuario)
            .options(joinedload(Usuario.rol))
            .where(Usuario.correo == correo)
        )
        usuario = result.scalar_one_or_none()
        if usuario is None:
            return None
        return AuthUser(
            id=usuario.id,
            nombre=usuario.nombre,
            correo=usuario.correo,
            contrasena_hash=usuario.contrasena_hash,
            rol=usuario.rol.nombre,
            activo=usuario.activo,
        )
