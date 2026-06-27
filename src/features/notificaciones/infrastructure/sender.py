"""Canal de envío.

`LogNotificationSender`: registra el envío (placeholder). NO persiste el correo.
Para envío real por email, reemplázalo por un adaptador al microservicio
correspondiente (o a Gmail), manteniendo el contacto solo en memoria.
"""
import logging

from src.features.notificaciones.domain.ports import NotificationSender

_log = logging.getLogger("notificaciones")


class LogNotificationSender(NotificationSender):
    async def send(self, *, correo: str, titulo: str, cuerpo: str) -> None:
        # No se loguea el correo completo (dato sensible): solo se confirma envío.
        _log.info("Notificación enviada (canal=email) titulo=%s", titulo)
