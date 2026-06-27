"""Composición de dependencias de la feature notificaciones."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_session
from src.features.dispositivos.infrastructure.repository import (
    SqlAlchemyDispositivoRepository,
)
from src.features.notificaciones.application.consultar import (
    ListarNotificaciones,
    MarcarLeida,
)
from src.features.notificaciones.application.emitir_evento import EmitirEvento
from src.features.notificaciones.application.generar_vencimientos import (
    GenerarNotificacionesVencimiento,
)
from src.features.notificaciones.domain.ports import PushNotifier
from src.features.notificaciones.infrastructure.fcm_push import (
    FcmPushNotifier,
    NullPushNotifier,
)
from src.features.notificaciones.infrastructure.repository import (
    SqlAlchemyNotificacionRepository,
)


def _build_push(session: AsyncSession) -> PushNotifier:
    """FCM si Firebase está configurado; si no, un push que no hace nada."""
    if settings.firebase_enabled:
        return FcmPushNotifier(SqlAlchemyDispositivoRepository(session))
    return NullPushNotifier()


def get_generar_vencimientos(
    session: AsyncSession = Depends(get_session),
) -> GenerarNotificacionesVencimiento:
    return GenerarNotificacionesVencimiento(
        repo=SqlAlchemyNotificacionRepository(session),
        push=_build_push(session),
        dias_aviso=settings.notificaciones_dias_aviso,
    )


def get_emitir_evento(
    session: AsyncSession = Depends(get_session),
) -> EmitirEvento:
    return EmitirEvento(
        repo=SqlAlchemyNotificacionRepository(session),
        push=_build_push(session),
    )


def get_listar_notificaciones(
    session: AsyncSession = Depends(get_session),
) -> ListarNotificaciones:
    return ListarNotificaciones(repo=SqlAlchemyNotificacionRepository(session))


def get_marcar_leida(
    session: AsyncSession = Depends(get_session),
) -> MarcarLeida:
    return MarcarLeida(repo=SqlAlchemyNotificacionRepository(session))
