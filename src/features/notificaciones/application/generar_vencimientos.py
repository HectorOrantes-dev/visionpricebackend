"""Job: generar notificaciones de suscripciones por vencer / vencidas.

Lo dispara un cron (endpoint protegido con X-Api-Key). Es idempotente: no
duplica avisos del mismo tipo para el mismo usuario dentro de una ventana.

Datos sensibles: al ENVIAR, el correo del destinatario se obtiene de forma
TRANSITORIA y se descarta; NUNCA se guarda en la notificación.
"""
from dataclasses import dataclass

from src.features.notificaciones.application import mensajes
from src.features.notificaciones.domain.entities import (
    NuevaNotificacion,
    TipoNotificacion,
)
from src.features.notificaciones.domain.ports import (
    NotificacionRepository,
    PushNotifier,
)

# Ventana de dedupe para "vencida" (no recordar a diario).
_DEDUPE_VENCIDA_DIAS = 30


@dataclass
class ResultadoJob:
    por_vencer: int
    vencidas: int


class GenerarNotificacionesVencimiento:
    def __init__(
        self,
        repo: NotificacionRepository,
        push: PushNotifier | None = None,
        dias_aviso: int = 7,
    ) -> None:
        self._repo = repo
        self._push = push
        self._dias_aviso = dias_aviso

    async def execute(self) -> ResultadoJob:
        por_vencer = 0
        for s in await self._repo.suscripciones_por_vencer(self._dias_aviso):
            if await self._repo.existe_reciente(
                s.usuario_id, TipoNotificacion.SUSCRIPCION_POR_VENCER, self._dias_aviso
            ):
                continue
            titulo, cuerpo = mensajes.vencimiento_por_vencer(
                s.plan_activo, s.vigencia_hasta
            )
            await self._crear_y_enviar(
                s.usuario_id, TipoNotificacion.SUSCRIPCION_POR_VENCER, titulo, cuerpo
            )
            por_vencer += 1

        vencidas = 0
        for s in await self._repo.suscripciones_vencidas():
            if await self._repo.existe_reciente(
                s.usuario_id, TipoNotificacion.SUSCRIPCION_VENCIDA, _DEDUPE_VENCIDA_DIAS
            ):
                continue
            titulo, cuerpo = mensajes.vencimiento_vencido(
                s.plan_activo, s.vigencia_hasta
            )
            await self._crear_y_enviar(
                s.usuario_id, TipoNotificacion.SUSCRIPCION_VENCIDA, titulo, cuerpo
            )
            vencidas += 1

        return ResultadoJob(por_vencer=por_vencer, vencidas=vencidas)

    async def _crear_y_enviar(
        self, usuario_id: int, tipo: str, titulo: str, cuerpo: str
    ) -> None:
        notif = await self._repo.crear(
            NuevaNotificacion(
                usuario_id=usuario_id,
                tipo=tipo,
                titulo=titulo,
                cuerpo=cuerpo,  # sin PII
                canal="push",
                referencia_tipo="suscripcion",
                referencia_id=usuario_id,
            )
        )

        if self._push is None:
            return

        # Los device tokens se resuelven al vuelo dentro del push notifier y
        # NO se persisten en la notificación (dato de dispositivo transitorio).
        enviados = await self._push.notificar(
            usuario_id, titulo, cuerpo, data={"tipo": tipo}
        )
        if enviados > 0:
            await self._repo.marcar_enviada(notif.id)
