"""Adaptador SQLAlchemy de RecomendacionUsoRepository."""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.recomendaciones.domain.entities import RecomendacionKit
from src.features.recomendaciones.domain.ports import RecomendacionUsoRepository
from src.shared.models import RecomendacionUso
from src.shared.timeutils import utcnow


class SqlAlchemyRecomendacionUsoRepository(RecomendacionUsoRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def registrar_solicitud(
        self,
        *,
        usuario_id: int,
        proyecto_id: int | None,
        recomendacion: RecomendacionKit,
        categoria: str,
    ) -> int:
        fila = RecomendacionUso(
            usuario_id=usuario_id,
            proyecto_id=proyecto_id,
            categoria=categoria,
            tipo_kit_recomendado=recomendacion.tipo_kit,
            complementos_recomendados=recomendacion.complementos_recomendados,
            metodo_crucetas_recomendado=recomendacion.metodo_crucetas_recomendado,
        )
        self._session.add(fila)
        await self._session.commit()
        await self._session.refresh(fila)
        return fila.id

    async def marcar_usada(self, recomendacion_id: int, cotizacion_id: int) -> bool:
        fila = await self._session.get(RecomendacionUso, recomendacion_id)
        if fila is None:
            return False
        fila.cotizacion_id = cotizacion_id
        fila.fecha_uso = utcnow()
        await self._session.commit()
        return True

    async def contar_uso(self) -> tuple[int, int]:
        total = (
            await self._session.execute(select(func.count()).select_from(RecomendacionUso))
        ).scalar_one()
        usadas = (
            await self._session.execute(
                select(func.count()).select_from(RecomendacionUso).where(
                    RecomendacionUso.cotizacion_id.is_not(None)
                )
            )
        ).scalar_one()
        return total, usadas
