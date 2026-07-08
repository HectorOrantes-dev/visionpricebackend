"""Adaptador SQLAlchemy del repositorio de auditoría de precios.

El historial sale de detalle_presupuesto (precio_unitario) uniendo con
presupuestos → proyectos para conocer la ubicación. La "zona" se resuelve por
una caja (bounding box) de la rejilla: ±medio paso de 10^-precision.
"""
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.auditoria_precios.domain.entities import LineaPrecio
from src.features.auditoria_precios.domain.ports import AuditoriaRepository
from src.shared.models import DetallePresupuesto, Presupuesto, Proyecto


def _delta(precision: int) -> float:
    return 0.5 * (10 ** -precision)


class SqlAlchemyAuditoriaRepository(AuditoriaRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def coords_de_presupuesto(
        self, presupuesto_id: int
    ) -> tuple[float | None, float | None] | None:
        result = await self._session.execute(
            select(Proyecto.latitud, Proyecto.longitud)
            .join(Presupuesto, Presupuesto.proyecto_id == Proyecto.id)
            .where(Presupuesto.id == presupuesto_id)
        )
        fila = result.first()
        if fila is None:
            return None
        lat, lng = fila
        return (
            float(lat) if lat is not None else None,
            float(lng) if lng is not None else None,
        )

    async def lineas_de_presupuesto(
        self, presupuesto_id: int
    ) -> list[LineaPrecio]:
        result = await self._session.execute(
            select(DetallePresupuesto).where(
                DetallePresupuesto.presupuesto_id == presupuesto_id
            )
        )
        return [_to_linea(d) for d in result.scalars().all()]

    async def historico_precios(
        self,
        material_id: str,
        *,
        lat: float | None,
        lng: float | None,
        precision: int,
        excluir_presupuesto: int | None = None,
    ) -> list[float]:
        stmt = (
            select(DetallePresupuesto.precio_unitario)
            .join(
                Presupuesto,
                Presupuesto.id == DetallePresupuesto.presupuesto_id,
            )
            .join(Proyecto, Proyecto.id == Presupuesto.proyecto_id)
            .where(
                DetallePresupuesto.material_id == material_id,
                DetallePresupuesto.precio_unitario.is_not(None),
            )
        )
        if lat is not None and lng is not None:
            d = _delta(precision)
            stmt = stmt.where(
                and_(
                    Proyecto.latitud.between(lat - d, lat + d),
                    Proyecto.longitud.between(lng - d, lng + d),
                )
            )
        if excluir_presupuesto is not None:
            stmt = stmt.where(
                DetallePresupuesto.presupuesto_id != excluir_presupuesto
            )
        result = await self._session.execute(stmt)
        return [float(p) for (p,) in result.all() if p is not None]

    async def lineas_en_zona(
        self, *, lat: float, lng: float, precision: int
    ) -> list[LineaPrecio]:
        d = _delta(precision)
        result = await self._session.execute(
            select(DetallePresupuesto)
            .join(
                Presupuesto,
                Presupuesto.id == DetallePresupuesto.presupuesto_id,
            )
            .join(Proyecto, Proyecto.id == Presupuesto.proyecto_id)
            .where(
                Proyecto.latitud.between(lat - d, lat + d),
                Proyecto.longitud.between(lng - d, lng + d),
                DetallePresupuesto.precio_unitario.is_not(None),
            )
        )
        return [_to_linea(d_) for d_ in result.scalars().all()]


def _to_linea(d: DetallePresupuesto) -> LineaPrecio:
    return LineaPrecio(
        detalle_id=d.id,
        presupuesto_id=d.presupuesto_id,
        material_id=d.material_id,
        descripcion=d.descripcion_actividad,
        precio_unitario=float(d.precio_unitario or 0),
    )
