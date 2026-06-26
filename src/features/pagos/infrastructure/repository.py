"""Adaptador SQLAlchemy del entitlement."""
from datetime import datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.pagos.domain.ports import EntitlementRepository
from src.shared.models import Usuario


class SqlAlchemyEntitlementRepository(EntitlementRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def actualizar(
        self,
        usuario_id: int,
        plan_activo: str | None,
        vigencia_hasta: datetime | None,
    ) -> bool:
        result = await self._session.execute(
            update(Usuario)
            .where(Usuario.id == usuario_id)
            .values(plan_activo=plan_activo, vigencia_hasta=vigencia_hasta)
        )
        await self._session.commit()
        return result.rowcount > 0
