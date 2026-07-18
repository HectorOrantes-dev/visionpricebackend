"""Adaptador SQLAlchemy del repositorio de invitaciones."""
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.proyectos.domain.entities import Invitacion
from src.features.proyectos.domain.ports import InvitacionRepository
from src.shared.models import ProyectoInvitacion


def _to_entity(m: ProyectoInvitacion) -> Invitacion:
    return Invitacion(
        id=m.id,
        proyecto_id=m.proyecto_id,
        codigo=m.codigo,
        rol_en_proyecto=m.rol_en_proyecto,
        estado=m.estado,
        usos=m.usos,
        invitado_por=m.invitado_por,
        fecha_creacion=m.fecha_creacion,
        fecha_expiracion=m.fecha_expiracion,
    )


class SqlAlchemyInvitacionRepository(InvitacionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def crear(self, inv: Invitacion) -> Invitacion:
        fila = ProyectoInvitacion(
            proyecto_id=inv.proyecto_id,
            codigo=inv.codigo,
            rol_en_proyecto=inv.rol_en_proyecto,
            estado=inv.estado,
            usos=inv.usos,
            invitado_por=inv.invitado_por,
            fecha_expiracion=inv.fecha_expiracion,
        )
        self._session.add(fila)
        await self._session.commit()
        await self._session.refresh(fila)
        return _to_entity(fila)

    async def obtener_por_codigo(self, codigo: str) -> Invitacion | None:
        result = await self._session.execute(
            select(ProyectoInvitacion).where(ProyectoInvitacion.codigo == codigo)
        )
        fila = result.scalar_one_or_none()
        return _to_entity(fila) if fila else None

    async def listar_activas_de_proyecto(
        self, proyecto_id: int
    ) -> list[Invitacion]:
        ahora = datetime.utcnow()
        result = await self._session.execute(
            select(ProyectoInvitacion)
            .where(
                ProyectoInvitacion.proyecto_id == proyecto_id,
                ProyectoInvitacion.estado == "activa",
                ProyectoInvitacion.fecha_expiracion > ahora,
            )
            .order_by(ProyectoInvitacion.fecha_creacion.desc())
        )
        return [_to_entity(f) for f in result.scalars().all()]

    async def incrementar_usos(self, invitacion_id: int) -> None:
        await self._session.execute(
            update(ProyectoInvitacion)
            .where(ProyectoInvitacion.id == invitacion_id)
            .values(usos=ProyectoInvitacion.usos + 1)
        )
        await self._session.commit()

    async def revocar(self, invitacion_id: int) -> bool:
        fila = await self._session.get(ProyectoInvitacion, invitacion_id)
        if fila is None:
            return False
        fila.estado = "revocada"
        await self._session.commit()
        return True

    async def codigo_existe(self, codigo: str) -> bool:
        result = await self._session.execute(
            select(ProyectoInvitacion.id).where(
                ProyectoInvitacion.codigo == codigo
            )
        )
        return result.scalar_one_or_none() is not None
