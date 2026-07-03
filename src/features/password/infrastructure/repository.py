"""Adaptador SQLAlchemy del repositorio de password reset."""
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.features.password.domain.ports import PasswordUserRepository
from src.shared.models import Usuario


class SqlAlchemyPasswordRepository(PasswordUserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def id_por_correo(self, correo: str) -> int | None:
        result = await self._session.execute(
            select(Usuario.id).where(Usuario.correo == correo)
        )
        return result.scalar_one_or_none()

    async def actualizar_password(
        self, usuario_id: int, contrasena_hash: str
    ) -> None:
        await self._session.execute(
            update(Usuario)
            .where(Usuario.id == usuario_id)
            .values(contrasena_hash=contrasena_hash)
        )
        await self._session.commit()

    async def datos_sesion(self, usuario_id: int) -> tuple[str, str] | None:
        result = await self._session.execute(
            select(Usuario)
            .options(joinedload(Usuario.rol))
            .where(Usuario.id == usuario_id)
        )
        u = result.scalar_one_or_none()
        if u is None:
            return None
        return u.correo, u.rol.nombre
