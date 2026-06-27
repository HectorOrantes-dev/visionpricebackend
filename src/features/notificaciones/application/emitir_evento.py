"""Caso de uso: emitir una notificación por un evento de negocio.

Lo usan otras features o microservicios (ML, Pagos) para crear notificaciones
como grabacion_procesada, presupuesto_listo, bienvenida, etc. Si no se pasan
título/cuerpo, se usan los textos por defecto del catálogo.
"""
from dataclasses import dataclass

from src.features.notificaciones.application import mensajes
from src.features.notificaciones.domain.entities import (
    Notificacion,
    NuevaNotificacion,
    TipoNotificacion,
)
from src.features.notificaciones.domain.ports import (
    NotificacionRepository,
    PushNotifier,
)
from src.shared.errors import ValidationError


@dataclass
class EventoCommand:
    usuario_id: int
    tipo: str
    titulo: str | None = None
    cuerpo: str | None = None
    referencia_tipo: str | None = None
    referencia_id: int | None = None


class EmitirEvento:
    def __init__(
        self, repo: NotificacionRepository, push: PushNotifier | None = None
    ) -> None:
        self._repo = repo
        self._push = push

    async def execute(self, cmd: EventoCommand) -> Notificacion:
        if cmd.tipo not in TipoNotificacion.TODOS:
            raise ValidationError(f"Tipo de notificación inválido: {cmd.tipo!r}.")

        titulo, cuerpo = cmd.titulo, cmd.cuerpo
        if titulo is None or cuerpo is None:
            default = mensajes.DEFAULTS.get(cmd.tipo)
            if default is None:
                raise ValidationError(
                    f"El tipo {cmd.tipo!r} requiere titulo y cuerpo explícitos."
                )
            titulo = titulo or default[0]
            cuerpo = cuerpo or default[1]

        notif = await self._repo.crear(
            NuevaNotificacion(
                usuario_id=cmd.usuario_id,
                tipo=cmd.tipo,
                titulo=titulo,
                cuerpo=cuerpo,
                canal="push" if self._push is not None else "in_app",
                referencia_tipo=cmd.referencia_tipo,
                referencia_id=cmd.referencia_id,
            )
        )

        if self._push is not None:
            enviados = await self._push.notificar(
                cmd.usuario_id, titulo, cuerpo, data={"tipo": cmd.tipo}
            )
            if enviados > 0:
                await self._repo.marcar_enviada(notif.id)

        return notif
