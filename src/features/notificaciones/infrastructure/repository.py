"""Adaptador SQLAlchemy del repositorio de notificaciones."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.notificaciones.domain.entities import (
    Destinatario,
    Notificacion,
    NuevaNotificacion,
    SuscripcionUsuario,
)
from src.features.notificaciones.domain.ports import NotificacionRepository
from src.shared.models import Notificacion as NotifModel
from src.shared.models import Usuario


def _to_entity(m: NotifModel) -> Notificacion:
    return Notificacion(
        id=m.id,
        usuario_id=m.usuario_id,
        tipo=m.tipo,
        titulo=m.titulo,
        cuerpo=m.cuerpo,
        canal=m.canal,
        estado=m.estado,
        leida=m.leida,
        referencia_tipo=m.referencia_tipo,
        referencia_id=m.referencia_id,
        fecha_creacion=m.fecha_creacion,
        fecha_envio=m.fecha_envio,
    )


class SqlAlchemyNotificacionRepository(NotificacionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def crear(self, nueva: NuevaNotificacion) -> Notificacion:
        fila = NotifModel(
            usuario_id=nueva.usuario_id,
            tipo=nueva.tipo,
            titulo=nueva.titulo,
            cuerpo=nueva.cuerpo,
            canal=nueva.canal,
            referencia_tipo=nueva.referencia_tipo,
            referencia_id=nueva.referencia_id,
        )
        self._session.add(fila)
        await self._session.commit()
        await self._session.refresh(fila)
        return _to_entity(fila)

    async def existe_reciente(
        self, usuario_id: int, tipo: str, dentro_dias: int
    ) -> bool:
        desde = datetime.now(timezone.utc) - timedelta(days=dentro_dias)
        result = await self._session.execute(
            select(NotifModel.id).where(
                NotifModel.usuario_id == usuario_id,
                NotifModel.tipo == tipo,
                NotifModel.fecha_creacion >= desde,
            )
        )
        return result.first() is not None

    async def listar_por_usuario(
        self, usuario_id: int, solo_no_leidas: bool = False
    ) -> list[Notificacion]:
        stmt = select(NotifModel).where(NotifModel.usuario_id == usuario_id)
        if solo_no_leidas:
            stmt = stmt.where(NotifModel.leida.is_(False))
        stmt = stmt.order_by(NotifModel.id.desc())
        result = await self._session.execute(stmt)
        return [_to_entity(m) for m in result.scalars().all()]

    async def marcar_leida(self, notificacion_id: int, usuario_id: int) -> bool:
        result = await self._session.execute(
            update(NotifModel)
            .where(
                NotifModel.id == notificacion_id,
                NotifModel.usuario_id == usuario_id,
            )
            .values(leida=True)
        )
        await self._session.commit()
        return result.rowcount > 0

    async def marcar_enviada(self, notificacion_id: int) -> None:
        await self._session.execute(
            update(NotifModel)
            .where(NotifModel.id == notificacion_id)
            .values(estado="enviada", fecha_envio=datetime.now(timezone.utc))
        )
        await self._session.commit()

    async def suscripciones_por_vencer(
        self, dias: int
    ) -> list[SuscripcionUsuario]:
        ahora = datetime.now(timezone.utc)
        limite = ahora + timedelta(days=dias)
        result = await self._session.execute(
            select(Usuario.id, Usuario.plan_activo, Usuario.vigencia_hasta).where(
                Usuario.plan_activo.is_not(None),
                Usuario.vigencia_hasta.is_not(None),
                Usuario.vigencia_hasta >= ahora,
                Usuario.vigencia_hasta <= limite,
            )
        )
        return [
            SuscripcionUsuario(usuario_id=uid, plan_activo=plan, vigencia_hasta=vig)
            for uid, plan, vig in result.all()
        ]

    async def suscripciones_vencidas(self) -> list[SuscripcionUsuario]:
        ahora = datetime.now(timezone.utc)
        result = await self._session.execute(
            select(Usuario.id, Usuario.plan_activo, Usuario.vigencia_hasta).where(
                Usuario.plan_activo.is_not(None),
                Usuario.vigencia_hasta.is_not(None),
                Usuario.vigencia_hasta < ahora,
            )
        )
        return [
            SuscripcionUsuario(usuario_id=uid, plan_activo=plan, vigencia_hasta=vig)
            for uid, plan, vig in result.all()
        ]

    async def get_destinatario(self, usuario_id: int) -> Destinatario | None:
        result = await self._session.execute(
            select(Usuario.correo).where(Usuario.id == usuario_id)
        )
        correo = result.scalar_one_or_none()
        if correo is None:
            return None
        return Destinatario(usuario_id=usuario_id, correo=correo)
