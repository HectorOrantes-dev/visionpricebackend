"""Adaptador SQLAlchemy del repositorio de cotizaciones.

Persiste sobre las tablas presupuestos + detalle_presupuesto del esquema.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.cotizaciones.domain.entities import Cotizacion, LineaCotizacion
from src.features.cotizaciones.domain.ports import CotizacionRepository
from src.shared.models import DetallePresupuesto, Presupuesto, Transcripcion


class SqlAlchemyCotizacionRepository(CotizacionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def texto_transcripcion(self, grabacion_id: int) -> str | None:
        result = await self._session.execute(
            select(Transcripcion.texto).where(
                Transcripcion.grabacion_id == grabacion_id
            )
        )
        return result.scalar_one_or_none()

    async def crear(
        self,
        *,
        proyecto_id: int,
        usuario_id: int,
        total: float,
        lineas: list[LineaCotizacion],
    ) -> Cotizacion:
        presupuesto = Presupuesto(
            proyecto_id=proyecto_id,
            usuario_id=usuario_id,
            total_estimado=total,
            estado="borrador",
        )
        self._session.add(presupuesto)
        await self._session.flush()

        for ln in lineas:
            self._session.add(
                DetallePresupuesto(
                    presupuesto_id=presupuesto.id,
                    material_id=ln.material_id,
                    proveedor_id=ln.proveedor_id,
                    descripcion_actividad=ln.descripcion,
                    cantidad=ln.cantidad,
                    unidad_medida=ln.unidad,
                    precio_unitario=ln.precio_unitario,
                    subtotal=ln.subtotal,
                )
            )
        await self._session.commit()
        await self._session.refresh(presupuesto)
        return Cotizacion(
            id=presupuesto.id,
            proyecto_id=presupuesto.proyecto_id,
            usuario_id=presupuesto.usuario_id,
            estado=presupuesto.estado,
            total=float(presupuesto.total_estimado or 0),
            fecha=presupuesto.fecha_generacion,
            lineas=lineas,
        )

    async def obtener(
        self, cotizacion_id: int, usuario_id: int
    ) -> Cotizacion | None:
        result = await self._session.execute(
            select(Presupuesto).where(
                Presupuesto.id == cotizacion_id,
                Presupuesto.usuario_id == usuario_id,
            )
        )
        presupuesto = result.scalar_one_or_none()
        if presupuesto is None:
            return None

        det = await self._session.execute(
            select(DetallePresupuesto)
            .where(DetallePresupuesto.presupuesto_id == cotizacion_id)
            .order_by(DetallePresupuesto.id)
        )
        lineas = [
            LineaCotizacion(
                material_id=d.material_id,
                proveedor_id=d.proveedor_id,
                descripcion=d.descripcion_actividad,
                cantidad=float(d.cantidad),
                unidad=d.unidad_medida,
                precio_unitario=float(d.precio_unitario or 0),
                subtotal=float(d.subtotal or 0),
            )
            for d in det.scalars().all()
        ]
        return Cotizacion(
            id=presupuesto.id,
            proyecto_id=presupuesto.proyecto_id,
            usuario_id=presupuesto.usuario_id,
            estado=presupuesto.estado,
            total=float(presupuesto.total_estimado or 0),
            fecha=presupuesto.fecha_generacion,
            lineas=lineas,
        )
