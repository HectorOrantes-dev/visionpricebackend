"""Adaptador SQLAlchemy del repositorio de cotizaciones.

Persiste sobre las tablas presupuestos + detalle_presupuesto del esquema.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.cotizaciones.domain.entities import (
    Cotizacion,
    CotizacionPdfItem,
    LineaCotizacion,
    InfoProyectoPdf,
)
from src.features.cotizaciones.domain.ports import CotizacionRepository
from src.shared.models import DetallePresupuesto, Presupuesto, Transcripcion, Proyecto, Usuario


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
                    proveedor_nombre=ln.proveedor_nombre,
                    proveedor_distancia=ln.proveedor_distancia,
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
                proveedor_nombre=d.proveedor_nombre,
                proveedor_distancia=float(d.proveedor_distancia) if d.proveedor_distancia else None,
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

    async def listar_cotizaciones_de_proyecto(
        self, proyecto_id: int, usuario_id: int
    ) -> list[Cotizacion]:
        """Lista TODAS las cotizaciones del proyecto (de cualquier miembro).

        La verificación de acceso (puede_acceder) se hace antes de llamar
        este método, en el caso de uso GenerarPdfProyecto.
        """
        result = await self._session.execute(
            select(Presupuesto).where(
                Presupuesto.proyecto_id == proyecto_id,
                Presupuesto.estado.in_(["borrador", "confirmado"]),
            ).order_by(Presupuesto.id)
        )
        presupuestos = result.scalars().all()
        if not presupuestos:
            return []
            
        cotizaciones = []
        for p in presupuestos:
            det = await self._session.execute(
                select(DetallePresupuesto)
                .where(DetallePresupuesto.presupuesto_id == p.id)
                .order_by(DetallePresupuesto.id)
            )
            lineas = [
                LineaCotizacion(
                    material_id=d.material_id,
                    proveedor_id=d.proveedor_id,
                    proveedor_nombre=d.proveedor_nombre,
                    proveedor_distancia=float(d.proveedor_distancia) if d.proveedor_distancia else None,
                    descripcion=d.descripcion_actividad,
                    cantidad=float(d.cantidad),
                    unidad=d.unidad_medida,
                    precio_unitario=float(d.precio_unitario or 0),
                    subtotal=float(d.subtotal or 0),
                )
                for d in det.scalars().all()
            ]
            cotizaciones.append(
                Cotizacion(
                    id=p.id,
                    proyecto_id=p.proyecto_id,
                    usuario_id=p.usuario_id,
                    estado=p.estado,
                    total=float(p.total_estimado or 0),
                    fecha=p.fecha_generacion,
                    lineas=lineas,
                )
            )
        return cotizaciones

    async def listar_pdfs_de_usuario(self, usuario_id: int) -> list[CotizacionPdfItem]:
        result = await self._session.execute(
            select(
                Presupuesto.id,
                Presupuesto.proyecto_id,
                Proyecto.nombre.label("proyecto_nombre"),
                Presupuesto.estado,
                Presupuesto.total_estimado,
                Presupuesto.fecha_generacion,
            )
            .join(Proyecto, Proyecto.id == Presupuesto.proyecto_id)
            .where(
                Presupuesto.usuario_id == usuario_id,
                Presupuesto.estado.in_(["borrador", "confirmado"]),
            )
            .order_by(Presupuesto.fecha_generacion.desc())
        )
        return [
            CotizacionPdfItem(
                id=row.id,
                proyecto_id=row.proyecto_id,
                proyecto_nombre=row.proyecto_nombre,
                estado=row.estado,
                total=float(row.total_estimado or 0),
                fecha=row.fecha_generacion,
            )
            for row in result.all()
        ]

    async def obtener_info_proyecto(
        self, proyecto_id: int, usuario_id: int
    ) -> InfoProyectoPdf | None:
        """Info del proyecto para el PDF. No filtra por dueño:
        el guard de acceso ya se verificó en el caso de uso.
        """
        result = await self._session.execute(
            select(Proyecto.nombre, Proyecto.direccion, Usuario.nombre.label("usuario_nombre"))
            .join(Usuario, Usuario.id == Proyecto.usuario_id)
            .where(Proyecto.id == proyecto_id)
        )
        row = result.first()
        if not row:
            return None
        return InfoProyectoPdf(
            proyecto_id=proyecto_id,
            nombre_proyecto=row.nombre,
            direccion=row.direccion,
            nombre_usuario=row.usuario_nombre,
        )
