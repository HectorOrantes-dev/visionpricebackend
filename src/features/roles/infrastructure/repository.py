"""Adaptador SQLAlchemy del catálogo de roles."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.roles.domain.ports import Rol, RoleRepository
from src.shared.models import Rol as RolModel


class SqlAlchemyRoleRepository(RoleRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def listar(self) -> list[Rol]:
        result = await self._session.execute(
            select(RolModel).order_by(RolModel.id)
        )
        return [Rol(id=r.id, nombre=r.nombre) for r in result.scalars().all()]
